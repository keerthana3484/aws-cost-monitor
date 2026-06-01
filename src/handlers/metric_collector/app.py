import os
import datetime
import boto3
from shared_utils.helpers import get_dynamodb_client

# Initialize clients
dynamodb = get_dynamodb_client()
ce_client = boto3.client('ce')
table_name = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    """
    AWS Lambda Handler to collect cost metrics from Cost Explorer API
    and save them to DynamoDB.
    """
    # TODO: Implement Cost Explorer ce_client.get_cost_and_usage logic
    # TODO: Write response to DynamoDB table
    
    return {
        "statusCode": 200,
        "body": "Metrics collected successfully"
    }
