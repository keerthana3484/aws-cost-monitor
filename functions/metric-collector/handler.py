import os
import json
import datetime
import logging
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Setup path-resilient imports for local and AWS environment
try:
    # 1. Standard package import
    from shared.metrics_generator import generate_daily_metrics
except ImportError:
    try:
        # 2. Direct parent context import (for local tests)
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
        from shared.metrics_generator import generate_daily_metrics
    except ImportError:
        # 3. Layer import fallback (assuming metrics_generator is placed directly in standard PYTHONPATH)
        from metrics_generator import generate_daily_metrics

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'CostMetrics')
CW_NAMESPACE = "CostMonitor/Daily"

# Map of standard active resource counts per service
RESOURCE_COUNTS = {
    "EC2": 3,
    "S3": 1,
    "Lambda": 1,
    "RDS": 1,
    "CloudFront": 1
}

def get_dynamodb_table():
    """Initializes and returns the DynamoDB Table resource."""
    # Check if local endpoint is requested/present
    endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
    if endpoint_url:
        logger.info(f"Connecting to DynamoDB locally at {endpoint_url}")
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    else:
        dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(TABLE_NAME)

def get_cloudwatch_client():
    """Initializes and returns a CloudWatch client."""
    return boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    AWS Lambda Handler to generate today's resource metrics,
    write them to DynamoDB (CostMetrics), and publish to CloudWatch.
    """
    logger.info("Starting Daily Metric Collector execution.")
    
    today = datetime.date.today()
    logger.info(f"Target execution date: {today.isoformat()}")

    # 1. Generate metrics for today
    try:
        daily_data = generate_daily_metrics(today)
        logger.info(f"Generated mock cost metrics successfully: Total Cost = ${daily_data['total_cost']}")
    except Exception as e:
        logger.error(f"Failed to generate cost metrics: {e}")
        return {
            "statusCode": 500,
            "error": f"Metrics generation failed: {e}"
        }

    table = get_dynamodb_table()
    cw_client = get_cloudwatch_client()
    
    processed_services = []
    skipped_services = []
    
    # 2. Iterate and process each service
    for service_name, data in daily_data['services'].items():
        cost = data['cost']
        usage = data['usage']
        unit = data['usage_unit']
        count = RESOURCE_COUNTS.get(service_name, 1)

        # 3. Write service metrics to DynamoDB (using conditional write)
        # Condition: do not overwrite existing records for same date + service
        item = {
            'service': service_name,
            'date': today.isoformat(),
            'estimated_cost': Decimal(str(cost)),
            'usage_value': Decimal(str(usage)),
            'usage_unit': unit,
            'resource_count': Decimal(str(count))
        }

        try:
            logger.info(f"Writing metrics to DynamoDB for service {service_name}...")
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(service) AND attribute_not_exists(#d)',
                ExpressionAttributeNames={'#d': 'date'}
            )
            processed_services.append(service_name)
            logger.info(f"✅ Successfully wrote DynamoDB record for {service_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                skipped_services.append(service_name)
                logger.warning(f"⚠️ Service record for {service_name} on date {today.isoformat()} already exists. Write skipped.")
            else:
                logger.error(f"❌ DynamoDB error for service {service_name}: {e}")
                # Continue processing other services even if one fails
                continue

        # 4. Push custom metrics to CloudWatch
        try:
            logger.info(f"Publishing CloudWatch metrics for service {service_name}...")
            cw_client.put_metric_data(
                Namespace=CW_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': 'EstimatedCost',
                        'Dimensions': [{'Name': 'Service', 'Value': service_name}],
                        'Value': float(cost),
                        'Unit': 'None'
                    },
                    {
                        'MetricName': 'UsageValue',
                        'Dimensions': [{'Name': 'Service', 'Value': service_name}],
                        'Value': float(usage),
                        'Unit': 'None'
                    }
                ]
            )
            logger.info(f"✅ Published CloudWatch metrics for {service_name}")
        except Exception as e:
            logger.error(f"❌ CloudWatch publish error for service {service_name}: {e}")
            # Continue processing

    # 5. Return summary
    summary = {
        "status": "COMPLETED",
        "date": today.isoformat(),
        "total_cost": float(daily_data['total_cost']),
        "processed_services": processed_services,
        "skipped_services": skipped_services
    }
    
    logger.info(f"Metric Collector finished. Summary: {json.dumps(summary)}")
    return {
        "statusCode": 200,
        "body": summary
    }

# Local Test Block utilizing moto mocking
if __name__ == "__main__":
    # Setup standard console logging for local testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Configure mock environment variables
    os.environ['DYNAMODB_TABLE'] = 'CostMetrics'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'mock'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'mock'
    
    try:
        from moto import mock_dynamodb, mock_cloudwatch
        
        @mock_dynamodb
        @mock_cloudwatch
        def run_mock_test():
            print("--- Starting Local Moto Mock Test ---")
            
            # Setup Mock DynamoDB
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            print("Creating mock DynamoDB CostMetrics table...")
            table = dynamodb.create_table(
                TableName='CostMetrics',
                KeySchema=[
                    {'AttributeName': 'service', 'KeyType': 'HASH'},
                    {'AttributeName': 'date', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'service', 'AttributeType': 'S'},
                    {'AttributeName': 'date', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            # Wait for table
            table.meta.client.get_waiter('table_exists').wait(TableName='CostMetrics')
            print("Mock DynamoDB table created.")
            
            # 1. Run first simulation (successful write of all services)
            print("\n👉 Running first handler call (Expect all writes to succeed)...")
            res1 = lambda_handler({}, None)
            print(f"Response: {res1}\n")
            
            # Check database state
            print("Verifying DynamoDB item counts...")
            scan_res = table.scan()
            print(f"Total items in DB: {scan_res['Count']}")
            
            # 2. Run second simulation (expect all writes to be skipped due to Condition Check)
            print("\n👉 Running second handler call (Expect all writes to be skipped)...")
            res2 = lambda_handler({}, None)
            print(f"Response: {res2}\n")
            
            print("--- Local Moto Mock Test Completed Successfully ---")

        run_mock_test()
        
    except ImportError:
        print("\nℹ️ To run the local test suite without AWS credentials, please install the moto mocking library:")
        print("   pip install moto")
        print("\nNote: Fallback execution initiated (Requires active AWS environment or Local DynamoDB):")
        # Set database to connect locally if local DB is running
        os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:8000'
        try:
            lambda_handler({}, None)
        except Exception as e:
            print(f"Could not connect to active DB backend: {e}")
