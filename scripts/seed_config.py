import os
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration
ENDPOINT_URL = "http://localhost:8000"
REGION_NAME = "us-east-1"
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_CONFIG', 'AlertConfig')

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
        aws_access_key_id="mock_key_id",
        aws_secret_access_key="mock_secret"
    )

def main():
    print(f"Connecting to local DynamoDB instance at {ENDPOINT_URL} to seed configuration...")
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(TABLE_NAME)
        
        # Default seeding item
        default_config = {
            'config_id': 'main',
            'monthly_threshold': Decimal('50.00'),
            'alert_email': 'test@example.com',
            'alerts_enabled': True
        }
        
        print(f"Attempting to seed default config item in '{TABLE_NAME}' table...")
        table.put_item(Item=default_config)
        print("✅ Success: Default alert configuration seeded successfully.")
        print(f"   Item: {default_config}")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Error: Table '{TABLE_NAME}' does not exist. Please run 'setup_dynamodb.py' first.")
        else:
            print(f"❌ Error: Seeding failed. Detail: {e}")
    except Exception as e:
        print(f"❌ Critical Error: Could not connect to local DynamoDB. Is it running? Detail: {e}")

if __name__ == "__main__":
    main()
