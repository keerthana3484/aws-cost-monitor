import datetime
import os
import sys

# Setup package path imports to access shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from shared.metrics_generator import generate_daily_metrics, generate_month_to_date

def test_generate_daily_metrics_returns_all_services():
    """Test that the generator returns all 5 required AWS services for any given day."""
    test_date = datetime.date(2026, 6, 1)  # A Monday
    result = generate_daily_metrics(test_date)
    
    assert "date" in result
    assert "services" in result
    assert "total_cost" in result
    
    services = result["services"]
    required_services = ["EC2", "S3", "Lambda", "RDS", "CloudFront"]
    
    for service in required_services:
        assert service in services
        assert "usage" in services[service]
        assert "usage_unit" in services[service]
        assert "cost" in services[service]

def test_weekday_costs_are_greater_than_weekend_costs():
    """Test that weekday daily costs are greater than weekend daily costs due to traffic models."""
    weekday = datetime.date(2026, 6, 1)  # Monday
    weekend = datetime.date(2026, 6, 7)  # Sunday
    
    weekday_metrics = generate_daily_metrics(weekday)
    weekend_metrics = generate_daily_metrics(weekend)
    
    print(f"Weekday cost: ${weekday_metrics['total_cost']:.2f}")
    print(f"Weekend cost: ${weekend_metrics['total_cost']:.2f}")
    
    assert weekday_metrics["total_cost"] > weekend_metrics["total_cost"]

def test_no_negative_costs_or_usages():
    """Test that cost and usage values are non-negative across a 30-day window."""
    today = datetime.date.today()
    
    for i in range(30):
        target_date = today - datetime.timedelta(days=i)
        metrics = generate_daily_metrics(target_date)
        
        assert metrics["total_cost"] >= 0, f"Negative total cost detected on {target_date}"
        
        for service, data in metrics["services"].items():
            assert data["cost"] >= 0, f"Negative cost detected for {service} on {target_date}"
            assert data["usage"] >= 0, f"Negative usage detected for {service} on {target_date}"

def test_generate_month_to_date_length_matches_elapsed_days():
    """Test that generate_month_to_date yields the exact number of days elapsed up to today."""
    today = datetime.date.today()
    year = today.year
    month = today.month
    
    mtd_metrics = generate_month_to_date(year, month)
    
    # Expected length: current day of the month (e.g. June 1st = 1 item)
    expected_length = today.day
    
    assert len(mtd_metrics) == expected_length
    
    # Check chronological ordering and elements
    for idx, day_metric in enumerate(mtd_metrics):
        expected_date = datetime.date(year, month, idx + 1).isoformat()
        assert day_metric["date"] == expected_date
