import os
import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Set absolute path imports for shared modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from shared.metrics_generator import generate_daily_metrics

# Configure mock/local AWS credentials & endpoint
ENDPOINT_URL = "http://localhost:8000"
REGION_NAME = "us-east-1"
TABLE_NAME = "CostMetrics"

# Local environment credentials (safety guard)
os.environ['AWS_DEFAULT_REGION'] = REGION_NAME
os.environ['AWS_ACCESS_KEY_ID'] = 'mock_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'mock_secret'

# Resource count mapping per service
RESOURCE_COUNTS = {
    "EC2": 3,
    "S3": 1,
    "Lambda": 1,
    "RDS": 1,
    "CloudFront": 1
}

def backfill():
    print(f"Connecting to local DynamoDB instance at {ENDPOINT_URL} for historical backfill...")
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL, region_name=REGION_NAME)
        table = dynamodb.Table(TABLE_NAME)
        
        # Test table exists
        table.load()
    except ClientError as e:
        print(f"❌ Error: Table '{TABLE_NAME}' not found. Please run 'setup_dynamodb.py' first.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical Error: Could not reach DynamoDB local: {e}")
        sys.exit(1)

    today = datetime.date.today()
    print("\n👉 Backfilling historical cost metrics for the last 30 days...")
    
    # Range of 30 days: from (today - 29 days) up to (today)
    for i in range(29, -1, -1):
        target_date = today - datetime.timedelta(days=i)
        date_str = target_date.isoformat()
        
        # Call metric collector library
        daily_data = generate_daily_metrics(target_date)
        total_cost = daily_data['total_cost']
        
        print(f"   Writing metrics for {date_str} (Total MTD baseline: ${total_cost:.2f})...")
        
        for service_name, data in daily_data['services'].items():
            cost = data['cost']
            usage = data['usage']
            unit = data['usage_unit']
            count = RESOURCE_COUNTS.get(service_name, 1)
            
            item = {
                'service': service_name,
                'date': date_str,
                'estimated_cost': Decimal(str(cost)),
                'usage_value': Decimal(str(usage)),
                'usage_unit': unit,
                'resource_count': Decimal(str(count))
            }
            
            try:
                table.put_item(Item=item)
            except Exception as e:
                print(f"      ❌ Failed to write record for {service_name} on {date_str}: {e}")
                
    print("\n🎉 Success: 30 days of cost metrics loaded into local DynamoDB.")

if __name__ == "__main__":
    backfill()
