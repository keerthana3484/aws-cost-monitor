#!/bin/bash

echo "============================================="
echo "⚡ Starting AWS SAM Local Environment API"
echo "============================================="

# 1. Export Mock/Local configuration parameters
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=mock_local_key
export AWS_SECRET_ACCESS_KEY=mock_local_secret

# Local DynamoDB targets
export DYNAMODB_ENDPOINT=http://localhost:8000
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export DYNAMODB_TABLE_COST=CostMetrics
export DYNAMODB_TABLE_CONFIG=AlertConfig

# Target SNS Alert Topic mock
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:aws-cost-alerts-topic

echo "🚀 Launching SAM local start-api on port 3001..."
sam local start-api --port 3001
