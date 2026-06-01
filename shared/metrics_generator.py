import random
import datetime
import calendar

def generate_daily_metrics(date):
    """
    Generates realistic mock AWS resource metrics and costs for a given date.
    
    Args:
        date (datetime.date or str): The date to generate metrics for (e.g. datetime.date(2026, 6, 1) or "2026-06-01")
        
    Returns:
        dict: A structured dictionary containing daily usage and costs per service, rounded to 4 decimal places.
    """
    # Parse string date if provided
    if isinstance(date, str):
        try:
            date_obj = datetime.date.fromisoformat(date)
        except ValueError:
            # Fallback parsing for other common formats
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        date_obj = date

    # Set seed based on date to maintain consistency for deterministic testing if needed
    # However, keeping random.uniform(0.9, 1.1) dynamic. To make it reproducible but realistic:
    # We will use the date's ordinal number as a seed base, but still allow realistic noise
    random.seed(date_obj.toordinal())

    is_weekend = date_obj.weekday() >= 5  # 5 is Saturday, 6 is Sunday

    # Service calculations
    
    # 1. EC2: 3 t3.medium instances ($0.0464/hr) + weekday bursting
    ec2_base_hours = 3 * 24.0  # 72 hours base
    ec2_burst_hours = 0.0 if is_weekend else random.uniform(5.0, 15.0)
    ec2_total_hours = ec2_base_hours + ec2_burst_hours
    ec2_noise = random.uniform(0.9, 1.1)
    ec2_cost = round(ec2_total_hours * 0.0464 * ec2_noise, 4)
    
    # 2. S3: 50GB base storage growing slowly ($0.023/GB/month)
    # Slow growth: 0.15GB added per day since start of current year
    start_of_year = datetime.date(date_obj.year, 1, 1)
    days_elapsed = (date_obj - start_of_year).days
    s3_storage_gb = 50.0 + (days_elapsed * 0.15)
    s3_daily_rate = 0.023 / 30.0  # approximate daily rate
    s3_noise = random.uniform(0.9, 1.1)
    s3_cost = round(s3_storage_gb * s3_daily_rate * s3_noise, 4)

    # 3. Lambda: invocation counts with daytime peaks ($0.0000002/invocation)
    # Weekend traffic is significantly lower
    if is_weekend:
        lambda_invocations = int(random.uniform(150000, 350000))
    else:
        lambda_invocations = int(random.uniform(800000, 1500000))
    lambda_noise = random.uniform(0.9, 1.1)
    lambda_cost = round(lambda_invocations * 0.0000002 * lambda_noise, 4)

    # 4. RDS: 1 db.t3.micro instance ($0.017/hr), always on (24 hours)
    rds_hours = 24.0
    rds_noise = random.uniform(0.9, 1.1)
    rds_cost = round(rds_hours * 0.017 * rds_noise, 4)

    # 5. CloudFront: data transfer out ($0.0085/GB)
    if is_weekend:
        cloudfront_gb = random.uniform(80.0, 180.0)
    else:
        cloudfront_gb = random.uniform(300.0, 600.0)
    cloudfront_noise = random.uniform(0.9, 1.1)
    cloudfront_cost = round(cloudfront_gb * 0.0085 * cloudfront_noise, 4)

    # Compile service data
    services_data = {
        "EC2": {
            "usage": round(ec2_total_hours, 2),
            "usage_unit": "Hrs",
            "cost": ec2_cost
        },
        "S3": {
            "usage": round(s3_storage_gb, 2),
            "usage_unit": "GB",
            "cost": s3_cost
        },
        "Lambda": {
            "usage": lambda_invocations,
            "usage_unit": "Invocations",
            "cost": lambda_cost
        },
        "RDS": {
            "usage": rds_hours,
            "usage_unit": "Hrs",
            "cost": rds_cost
        },
        "CloudFront": {
            "usage": round(cloudfront_gb, 2),
            "usage_unit": "GB",
            "cost": cloudfront_cost
        }
    }

    # Sum total daily cost
    total_daily_cost = round(sum(service["cost"] for service in services_data.values()), 4)

    # Reset seed to random to avoid impacting other parts of execution
    random.seed(None)

    return {
        "date": date_obj.isoformat(),
        "services": services_data,
        "total_cost": total_daily_cost
    }

def generate_month_to_date(year, month):
    """
    Generates all daily metrics from the 1st of the specified month up to today 
    (if referencing the current month) or the end of the month (if in the past).
    
    Args:
        year (int): Year of the month to generate (e.g. 2026)
        month (int): Month number (1 to 12)
        
    Returns:
        list: A list of daily metric dictionaries.
    """
    today = datetime.date.today()
    requested_date = datetime.date(year, month, 1)

    # Determine end day
    if year > today.year or (year == today.year and month > today.month):
        # Future month: no metrics to generate
        return []
    elif year == today.year and month == today.month:
        # Current month: up to today
        last_day = today.day
    else:
        # Past month: full month range
        last_day = calendar.monthrange(year, month)[1]

    daily_metrics_list = []
    for day in range(1, last_day + 1):
        current_day = datetime.date(year, month, day)
        daily_metrics_list.append(generate_daily_metrics(current_day))
        
    return daily_metrics_list
