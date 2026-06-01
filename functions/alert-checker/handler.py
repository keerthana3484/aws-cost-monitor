import os
import json
import datetime
import logging
import calendar
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
COST_TABLE = os.environ.get('DYNAMODB_TABLE_COST', 'CostMetrics')
CONFIG_TABLE = os.environ.get('DYNAMODB_TABLE_CONFIG', 'AlertConfig')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:aws-cost-alerts-topic')

def get_dynamodb_resource():
    """Initializes and returns the DynamoDB resource."""
    endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
    if endpoint_url:
        return boto3.resource('dynamodb', endpoint_url=endpoint_url)
    return boto3.resource('dynamodb')

def get_sns_client():
    """Initializes and returns the SNS client."""
    return boto3.client('sns')

def lambda_handler(event, context):
    """
    AWS Lambda Handler that evaluates Month-to-Date costs from CostMetrics 
    against thresholds stored in AlertConfig, triggering alerts via SNS on breach.
    """
    logger.info("Starting budget Alert Checker execution.")
    
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    month_prefix = f"{current_year}-{current_month:02d}"

    dynamodb = get_dynamodb_resource()
    sns_client = get_sns_client()

    # 1. Read AlertConfig from DynamoDB (config_id = "main")
    config_table = dynamodb.Table(CONFIG_TABLE)
    try:
        logger.info(f"Retrieving configuration from {CONFIG_TABLE}...")
        config_res = config_table.get_item(Key={'config_id': 'main'})
        if 'Item' not in config_res:
            logger.error("No default alert configuration 'main' found in AlertConfig table.")
            return {
                "alerted": False,
                "error": "Configuration item 'main' not found"
            }
        config = config_res['Item']
    except Exception as e:
        logger.error(f"Failed to read AlertConfig table: {e}")
        return {"alerted": False, "error": f"Failed to read config: {e}"}

    threshold = float(config.get('monthly_threshold', 50.00))
    alert_email = config.get('alert_email', 'test@example.com')
    alerts_enabled = config.get('alerts_enabled', True)
    last_alert_sent = config.get('last_alert_sent', '')

    logger.info(f"Alert configuration loaded: Threshold=${threshold}, Enabled={alerts_enabled}, LastAlert='{last_alert_sent}'")

    if not alerts_enabled:
        logger.info("Alerts are disabled in the configuration. Skipping evaluation.")
        return {
            "alerted": False,
            "mtd_cost": 0.0,
            "projected_cost": 0.0,
            "threshold": threshold,
            "message": "Alerts disabled"
        }

    # 2. Query CostMetrics for all records this month
    cost_table = dynamodb.Table(COST_TABLE)
    mtd_cost = 0.0
    service_breakdown = {}

    try:
        logger.info(f"Scanning CostMetrics table for month prefix: {month_prefix}")
        # Note: Scanning is safe for small metrics tables, but we filter by month prefix
        scan_kwargs = {
            'FilterExpression': 'begins_with(#d, :month_prefix)',
            'ExpressionAttributeNames': {'#d': 'date'},
            'ExpressionAttributeValues': {':month_prefix': month_prefix}
        }
        
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = cost_table.scan(**scan_kwargs)
            
            for item in response.get('Items', []):
                cost = float(item.get('estimated_cost', 0.0))
                service = item.get('service', 'Unknown')
                
                mtd_cost += cost
                service_breakdown[service] = service_breakdown.get(service, 0.0) + cost
                
            start_key = response.get('LastEvaluatedKey')
            done = start_key is None

        logger.info(f"Month-to-Date total cost calculated: ${mtd_cost:.2f}")
    except Exception as e:
        logger.error(f"Failed to fetch cost metrics: {e}")
        return {"alerted": False, "error": f"Failed to fetch cost metrics: {e}"}

    # 3. Calculate projected month-end cost
    days_elapsed = today.day
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    
    # Safe guard division by zero
    if days_elapsed <= 0:
        days_elapsed = 1
        
    projected_cost = (mtd_cost / days_elapsed) * days_in_month
    logger.info(f"Projected month-end cost: ${projected_cost:.2f} (days elapsed: {days_elapsed}/{days_in_month})")

    # Log current status regardless of alert
    logger.info(
        f"STATUS REPORT: MTD Cost = ${mtd_cost:.2f}, Projected Cost = ${projected_cost:.2f}, Threshold = ${threshold:.2f}"
    )

    # 4. Evaluate alert triggers
    # Trigger 1: MTD cost exceeds threshold
    # Trigger 2: Projected cost exceeds threshold by 20% (threshold * 1.2)
    trigger_mtd = mtd_cost > threshold
    trigger_projected = projected_cost > (threshold * 1.2)
    alert_triggered = trigger_mtd or trigger_projected

    alert_sent = False
    
    if alert_triggered:
        logger.info(f"Alert condition met! Trigger MTD: {trigger_mtd}, Trigger Projected: {trigger_projected}")
        
        # Guard against double alerting today
        today_str = today.isoformat()
        if last_alert_sent == today_str:
            logger.info("An alert has already been dispatched today. Suppressing redundant notification.")
        else:
            # Construct breakdown message string
            breakdown_str = "\n".join([f"- {svc}: ${val:.2f}" for svc, val in service_breakdown.items()])
            
            email_body = (
                f"🚨 AWS Cloud Cost Alert Triggered! 🚨\n\n"
                f"Your AWS cost monitoring system has detected a budget threshold breach.\n\n"
                f"--- Spend Overview ---\n"
                f"• Current MTD Cost: ${mtd_cost:.2f}\n"
                f"• Projected Month-End Cost: ${projected_cost:.2f}\n"
                f"• Monthly Budget Limit: ${threshold:.2f}\n\n"
                f"--- Service Breakdown ---\n"
                f"{breakdown_str}\n\n"
                f"Please review your AWS Console resources to manage unexpected billing items.\n"
            )

            # Publish alert to SNS
            try:
                logger.info(f"Publishing alert message to SNS topic: {SNS_TOPIC_ARN}")
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f"AWS Cost Alert - Spend Breach Detected (${mtd_cost:.2f})",
                    Message=email_body
                )
                alert_sent = True
                logger.info("✅ SNS cost alert published successfully.")

                # Update the AlertConfig table setting last_alert_sent
                logger.info("Updating last_alert_sent timestamp in DynamoDB...")
                config_table.update_item(
                    Key={'config_id': 'main'},
                    UpdateExpression='SET last_alert_sent = :today',
                    ExpressionAttributeValues={':today': today_str}
                )
                logger.info("✅ DynamoDB configuration timestamp updated.")
            except Exception as e:
                logger.error(f"❌ Failed to dispatch alert or update config state: {e}")
    else:
        logger.info("Cost levels are within acceptable thresholds. No action required.")

    return {
        "alerted": alert_sent,
        "mtd_cost": round(mtd_cost, 2),
        "projected_cost": round(projected_cost, 2),
        "threshold": round(threshold, 2)
    }

# Local Test Block utilizing moto mocking
if __name__ == "__main__":
    # Setup standard console logging for local testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Configure mock environment variables
    os.environ['DYNAMODB_TABLE_COST'] = 'CostMetrics'
    os.environ['DYNAMODB_TABLE_CONFIG'] = 'AlertConfig'
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:aws-cost-alerts-topic'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'mock'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'mock'

    try:
        from moto import mock_dynamodb, mock_sns
        
        @mock_dynamodb
        @mock_sns
        def run_mock_test():
            print("--- Starting Local Moto Mock Test for Alert Checker ---")
            
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            sns_client = boto3.client('sns', region_name='us-east-1')
            
            # 1. Create mock SNS Topic
            sns_res = sns_client.create_topic(Name="aws-cost-alerts-topic")
            sns_topic_arn = sns_res['TopicArn']
            os.environ['SNS_TOPIC_ARN'] = sns_topic_arn
            print(f"Mock SNS Topic created: {sns_topic_arn}")
            
            # 2. Create mock tables
            print("Creating mock DynamoDB CostMetrics & AlertConfig tables...")
            
            cost_table = dynamodb.create_table(
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
            cost_table.meta.client.get_waiter('table_exists').wait(TableName='CostMetrics')

            config_table = dynamodb.create_table(
                TableName='AlertConfig',
                KeySchema=[{'AttributeName': 'config_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'config_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            config_table.meta.client.get_waiter('table_exists').wait(TableName='AlertConfig')
            print("Mock tables created successfully.")

            # 3. Seed AlertConfig
            print("Seeding AlertConfig table with $100 limit...")
            config_table.put_item(Item={
                'config_id': 'main',
                'monthly_threshold': Decimal('100.00'),
                'alert_email': 'alert@example.com',
                'alerts_enabled': True,
                'last_alert_sent': ''
            })

            # 4. Seed CostMetrics (under threshold)
            today_str = datetime.date.today().isoformat()
            print("Seeding normal metrics under budget threshold...")
            cost_table.put_item(Item={
                'service': 'EC2',
                'date': today_str,
                'estimated_cost': Decimal('15.50'),
                'usage_value': Decimal('100.0'),
                'usage_unit': 'Hrs'
            })
            cost_table.put_item(Item={
                'service': 'S3',
                'date': today_str,
                'estimated_cost': Decimal('5.20'),
                'usage_value': Decimal('50.0'),
                'usage_unit': 'GB'
            })

            # Run check 1: should not trigger alert (total cost 20.70, threshold 100)
            print("\n👉 Running check 1 (Expect NO alert)...")
            res1 = lambda_handler({}, None)
            print(f"Response: {res1}")
            
            # 5. Seed extremely high cost to trigger alert
            print("\nSeeding high metric to trigger alert...")
            cost_table.put_item(Item={
                'service': 'Lambda',
                'date': today_str,
                'estimated_cost': Decimal('120.00'),
                'usage_value': Decimal('5000000.0'),
                'usage_unit': 'Invocations'
            })

            # Run check 2: should trigger alert and record timestamp
            print("\n👉 Running check 2 (Expect Alert Sent)...")
            res2 = lambda_handler({}, None)
            print(f"Response: {res2}")
            
            # Check AlertConfig state
            updated_config = config_table.get_item(Key={'config_id': 'main'})['Item']
            print(f"Updated configuration state: {updated_config}")

            # Run check 3: should suppress alert because alert was already sent today
            print("\n👉 Running check 3 (Expect Alert Suppressed)...")
            res3 = lambda_handler({}, None)
            print(f"Response: {res3}")

            print("\n--- Local Moto Mock Test for Alert Checker Completed Successfully ---")

        run_mock_test()
        
    except ImportError:
        print("\nℹ️ To run the local test suite without AWS credentials, please install the moto mocking library:")
        print("   pip install moto")
