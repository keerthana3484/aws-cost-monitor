import os
import boto3
from botocore.exceptions import ClientError

def get_dynamodb_client():
    """Returns a boto3 DynamoDB resource client."""
    return boto3.resource('dynamodb')

def get_sns_client():
    """Returns a boto3 SNS client."""
    return boto3.client('sns')

def format_currency(amount: float) -> str:
    """Formats a float as USD currency."""
    return f"${amount:,.2f}"
