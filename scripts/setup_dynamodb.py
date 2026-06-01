import os
import boto3
from botocore.exceptions import ClientError

# Configuration
ENDPOINT_URL = "http://localhost:8000"
REGION_NAME = "us-east-1"

def get_dynamodb_resource():
    """Initializes and returns a boto3 DynamoDB resource."""
    endpoint = os.environ.get('DYNAMODB_ENDPOINT_URL', ENDPOINT_URL)
    if endpoint == 'live' or endpoint == 'AWS' or not endpoint:
        # Connect to live AWS DynamoDB
        return boto3.resource('dynamodb', region_name=REGION_NAME)
    return boto3.resource(
        'dynamodb',
        endpoint_url=endpoint,
        region_name=REGION_NAME,
        aws_access_key_id="mock_key_id",      # Dummy credentials for local DynamoDB
        aws_secret_access_key="mock_secret"
    )

def create_table(dynamodb, table_name, key_schema, attribute_definitions):
    """Helper function to create a DynamoDB table with local capacity configurations."""
    try:
        print(f"Attempting to create table '{table_name}'...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait until the table exists
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Success: Table '{table_name}' created successfully.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceInUseException':
            print(f"⚠️ Warning: Table '{table_name}' already exists.")
        else:
            print(f"❌ Error: Failed to create table '{table_name}'. Detail: {e}")

def main():
    print(f"Connecting to local DynamoDB instance at {ENDPOINT_URL}...")
    try:
        dynamodb = get_dynamodb_resource()
        
        # 1. CostMetrics table setup
        cost_metrics_key_schema = [
            {'AttributeName': 'service', 'KeyType': 'HASH'},  # Partition key
            {'AttributeName': 'date', 'KeyType': 'RANGE'}     # Sort key
        ]
        cost_metrics_attrs = [
            {'AttributeName': 'service', 'AttributeType': 'S'},
            {'AttributeName': 'date', 'AttributeType': 'S'}
        ]
        create_table(dynamodb, "CostMetrics", cost_metrics_key_schema, cost_metrics_attrs)

        # 2. AlertConfig table setup
        alert_config_key_schema = [
            {'AttributeName': 'config_id', 'KeyType': 'HASH'}  # Partition key
        ]
        alert_config_attrs = [
            {'AttributeName': 'config_id', 'AttributeType': 'S'}
        ]
        create_table(dynamodb, "AlertConfig", alert_config_key_schema, alert_config_attrs)

        print("\n🎉 DynamoDB local setup execution finished.")

    except Exception as e:
        print(f"❌ Critical Error: Could not connect to local DynamoDB. Is it running? Detail: {e}")

if __name__ == "__main__":
    main()
