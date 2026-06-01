import os
import json
from shared_utils.helpers import get_dynamodb_client

# Initialize DynamoDB client
dynamodb = get_dynamodb_client()
table_name = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    """
    AWS Lambda Handler that retrieves cost metrics from DynamoDB
    and serves them to the React frontend dashboard via API Gateway.
    """
    # TODO: Query/Scan table for cost data
    # TODO: Return formatted JSON response with CORS headers
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key"
        },
        "body": json.dumps({
            "message": "Cost metrics retrieved successfully",
            "data": []
        })
    }
