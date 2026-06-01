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

# In-memory mock configurations for standard fallback mode
MOCK_CONFIG = {
    'monthly_threshold': 50.00,
    'alerts_enabled': True
}

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to automatically serialize DynamoDB Decimal values to floats/ints."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_dynamodb_resource():
    """Initializes and returns the DynamoDB resource."""
    endpoint_url = os.environ.get('DYNAMODB_ENDPOINT_URL')
    if endpoint_url:
        return boto3.resource('dynamodb', endpoint_url=endpoint_url)
    return boto3.resource('dynamodb')

def make_response(status_code, body):
    """Constructs a JSON response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,PUT,OPTIONS"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def generate_mock_daily_metrics(date_obj):
    """Generates deterministic mock cost data for local fallback when DynamoDB is down."""
    import random
    random.seed(date_obj.toordinal())
    is_weekend = date_obj.weekday() >= 5
    
    ec2_cost = round((72.0 + (0.0 if is_weekend else random.uniform(5.0, 15.0))) * 0.0464 * random.uniform(0.9, 1.1), 4)
    
    start_of_year = datetime.date(date_obj.year, 1, 1)
    days_elapsed = (date_obj - start_of_year).days
    s3_cost = round((50.0 + (days_elapsed * 0.15)) * (0.023 / 30.0) * random.uniform(0.9, 1.1), 4)
    
    lambda_invocations = int(random.uniform(150000, 350000) if is_weekend else random.uniform(800000, 1500000))
    lambda_cost = round(lambda_invocations * 0.0000002 * random.uniform(0.9, 1.1), 4)
    
    rds_cost = round(24.0 * 0.017 * random.uniform(0.9, 1.1), 4)
    
    cloudfront_gb = random.uniform(80.0, 180.0) if is_weekend else random.uniform(300.0, 600.0)
    cloudfront_cost = round(cloudfront_gb * 0.0085 * random.uniform(0.9, 1.1), 4)
    
    # reset seed
    random.seed(None)
    
    return {
        "EC2": ec2_cost,
        "S3": s3_cost,
        "Lambda": lambda_cost,
        "RDS": rds_cost,
        "CloudFront": cloudfront_cost
    }

def lambda_handler(event, context):
    """
    AWS Lambda Handler that acts as a router for multiple API Gateway proxy requests.
    Supports:
      - GET /metrics?days=30
      - GET /summary
      - PUT /config
    """
    http_method = event.get('httpMethod', '').upper()
    if http_method == 'OPTIONS':
        return make_response(200, {"message": "CORS preflight OK"})

    path = event.get('path', '')
    resource = event.get('resource', '')
    
    logger.info(f"API Request received: Method={http_method}, Path={path}, Resource={resource}")

    try:
        dynamodb = get_dynamodb_resource()
        
        if (path == '/metrics' or resource == '/metrics') and http_method == 'GET':
            return handle_get_metrics(event, dynamodb)
            
        elif (path == '/summary' or resource == '/summary') and http_method == 'GET':
            return handle_get_summary(event, dynamodb)
            
        elif (path == '/config' or resource == '/config') and http_method == 'PUT':
            return handle_put_config(event, dynamodb)
            
        else:
            logger.warning(f"Unsupported route requested: Path={path}, Method={http_method}")
            return make_response(404, {"error": f"Unsupported route: {http_method} {path}"})
            
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        return make_response(500, {"error": "Internal Server Error", "details": str(e)})

def handle_get_metrics(event, dynamodb):
    """Fetches daily costs for the last N days across all services, falling back to mock data if DB is down."""
    query_params = event.get('queryStringParameters') or {}
    try:
        days = int(query_params.get('days', 30))
    except ValueError:
        return make_response(400, {"error": "Invalid query parameter 'days'. Must be an integer."})

    logger.info(f"Retrieving metrics for the last {days} days.")
    
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days - 1)
    
    try:
        cost_table = dynamodb.Table(COST_TABLE)
        cost_table.load()  # test if db/table is reachable
        
        scan_kwargs = {
            'FilterExpression': '#d BETWEEN :start_date AND :end_date',
            'ExpressionAttributeNames': {'#d': 'date'},
            'ExpressionAttributeValues': {
                ':start_date': start_date.isoformat(),
                ':end_date': today.isoformat()
            }
        }
        
        items = []
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = cost_table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey')
            done = start_key is None

        unique_services = sorted(list(set(item.get('service') for item in items if item.get('service'))))
        
        date_list = []
        curr = start_date
        while curr <= today:
            date_list.append(curr.isoformat())
            curr += datetime.timedelta(days=1)

        cost_map = {svc: {dt: 0.0 for dt in date_list} for svc in unique_services}
        
        for item in items:
            svc = item.get('service')
            dt = item.get('date')
            cost = float(item.get('estimated_cost', 0.0))
            
            if svc in cost_map and dt in cost_map[svc]:
                cost_map[svc][dt] = round(cost, 4)

        services_streams = {}
        for svc in unique_services:
            services_streams[svc] = [cost_map[svc][dt] for dt in date_list]

        return make_response(200, {
            "dates": date_list,
            "services": services_streams
        })

    except Exception as e:
        logger.warning(f"DynamoDB Local is unreachable or unseeded ({e}). Falling back to self-contained mock metrics.")
        
        date_list = []
        curr = start_date
        while curr <= today:
            date_list.append(curr.isoformat())
            curr += datetime.timedelta(days=1)
            
        services = ["EC2", "S3", "Lambda", "RDS", "CloudFront"]
        services_streams = {svc: [] for svc in services}
        
        curr = start_date
        while curr <= today:
            daily = generate_mock_daily_metrics(curr)
            for svc in services:
                services_streams[svc].append(daily[svc])
            curr += datetime.timedelta(days=1)
            
        return make_response(200, {
            "dates": date_list,
            "services": services_streams,
            "mocked_mode": True
        })

def handle_get_summary(event, dynamodb):
    """Fetches MTD totals and projections, falling back to mock data if DB is down."""
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    month_prefix = f"{current_year}-{current_month:02d}"

    try:
        cost_table = dynamodb.Table(COST_TABLE)
        config_table = dynamodb.Table(CONFIG_TABLE)
        cost_table.load()
        config_table.load()

        threshold = 50.00
        try:
            config_res = config_table.get_item(Key={'config_id': 'main'})
            if 'Item' in config_res:
                threshold = float(config_res['Item'].get('monthly_threshold', 50.00))
        except Exception as e:
            logger.warning(f"Could not read config from DB: {e}. Using default.")

        mtd_total = 0.0
        service_totals = {}
        
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
                svc = item.get('service', 'Unknown')
                
                mtd_total += cost
                service_totals[svc] = service_totals.get(svc, 0.0) + cost
                
            start_key = response.get('LastEvaluatedKey')
            done = start_key is None

        days_elapsed = today.day
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        
        if days_elapsed <= 0:
            days_elapsed = 1
            
        projected_month_end = (mtd_total / days_elapsed) * days_in_month
        percent_used = (mtd_total / threshold * 100) if threshold > 0 else 0.0

        top_service = "None"
        top_cost = 0.0
        for svc, cost in service_totals.items():
            if cost > top_cost:
                top_cost = cost
                top_service = svc

        rounded_service_totals = {svc: round(val, 2) for svc, val in service_totals.items()}

        return make_response(200, {
            "mtd_total": round(mtd_total, 2),
            "projected_month_end": round(projected_month_end, 2),
            "threshold": round(threshold, 2),
            "percent_used": round(percent_used, 2),
            "top_service": top_service,
            "service_totals": rounded_service_totals
        })

    except Exception as e:
        logger.warning(f"DynamoDB Local is unreachable or unseeded ({e}). Falling back to self-contained mock summary.")
        
        service_totals = {"EC2": 0.0, "S3": 0.0, "Lambda": 0.0, "RDS": 0.0, "CloudFront": 0.0}
        mtd_total = 0.0
        
        for day in range(1, today.day + 1):
            date_obj = datetime.date(current_year, current_month, day)
            daily = generate_mock_daily_metrics(date_obj)
            for svc, cost in daily.items():
                service_totals[svc] += cost
                mtd_total += cost
                
        days_elapsed = today.day
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        
        projected_month_end = (mtd_total / days_elapsed) * days_in_month
        
        threshold = MOCK_CONFIG.get('monthly_threshold', 50.00)
        percent_used = (mtd_total / threshold * 100) if threshold > 0 else 0.0
        
        top_service = "None"
        top_cost = 0.0
        for svc, cost in service_totals.items():
            if cost > top_cost:
                top_cost = cost
                top_service = svc
                
        rounded_service_totals = {svc: round(val, 2) for svc, val in service_totals.items()}
        
        return make_response(200, {
            "mtd_total": round(mtd_total, 2),
            "projected_month_end": round(projected_month_end, 2),
            "threshold": round(threshold, 2),
            "percent_used": round(percent_used, 2),
            "top_service": top_service,
            "service_totals": rounded_service_totals,
            "mocked_mode": True
        })

def handle_put_config(event, dynamodb):
    """Updates config in database, or falls back to updating local in-memory config dictionary."""
    body_str = event.get('body', '')
    if not body_str:
        return make_response(400, {"error": "Missing request body."})

    try:
        body = json.loads(body_str)
    except Exception as e:
        return make_response(400, {"error": f"Malformed JSON request body: {e}"})

    if 'monthly_threshold' not in body or 'alerts_enabled' not in body:
        return make_response(400, {"error": "Request body must contain 'monthly_threshold' and 'alerts_enabled'."})

    threshold = body['monthly_threshold']
    enabled = body['alerts_enabled']

    if not isinstance(threshold, (int, float)) or threshold < 0:
        return make_response(400, {"error": "'monthly_threshold' must be a non-negative number."})

    if not isinstance(enabled, bool):
        return make_response(400, {"error": "'alerts_enabled' must be a boolean."})

    try:
        config_table = dynamodb.Table(CONFIG_TABLE)
        config_table.load()
        
        logger.info(f"Updating AlertConfig parameters in DynamoDB: Threshold={threshold}, Enabled={enabled}")
        
        config_table.update_item(
            Key={'config_id': 'main'},
            UpdateExpression='SET monthly_threshold = :t, alerts_enabled = :e',
            ExpressionAttributeValues={
                ':t': Decimal(str(threshold)),
                ':e': enabled
            }
        )
        
        return make_response(200, {
            "message": "Alert configurations updated successfully.",
            "updated_config": {
                "monthly_threshold": threshold,
                "alerts_enabled": enabled
            }
        })
        
    except Exception as e:
        logger.warning(f"DynamoDB is unreachable ({e}). Updating self-contained in-memory config configuration.")
        
        MOCK_CONFIG['monthly_threshold'] = float(threshold)
        MOCK_CONFIG['alerts_enabled'] = bool(enabled)
        
        return make_response(200, {
            "message": "Alert configurations updated successfully (In-Memory Fallback).",
            "updated_config": {
                "monthly_threshold": threshold,
                "alerts_enabled": enabled
            },
            "mocked_mode": True
        })
