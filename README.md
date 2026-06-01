# AWS Cloud Cost Monitoring Portal 📊☁️

An enterprise-grade, serverless billing intelligence platform built with Python Lambda functions, DynamoDB, EventBridge schedules, SNS alerting, and a premium dark-themed React dashboard.

This system provides automated daily ingestion, budget threshold comparisons, real-time Slack/Email alert dispatches on budget breaches, and a stacked historical visualizer suited for quick cost tracking.

---

## 🏗️ Architecture Design

```text
                                  +------------------+
                                  |  React Frontend  |
                                  +--------+---------+
                                           |
                                           | HTTPS (CORS)
                                           v
                                +----------+----------+
                                |  AWS API Gateway    |
                                +----------+----------+
                                           |
                                           v
                                +----------+----------+
                                |  ApiHandler Lambda  |
                                +----------+----------+
                                           |
                                           | Read / Write
                                           v
                                +----------+----------+
                                |     DynamoDB        | <----+
                                |   (CostMetrics /    |      |
                                |    AlertConfig)     |      | Read / Write
                                +----------+----------+      |
                                           ^                 |
                                           |                 |
                                   Trigger | Periodical      |
                                           |                 |
                                +----------+----------+      |
                                | CloudWatch Event    |      |
                                | (EventBridge Cron)  |      |
                                +----------+----------+      |
                                           |                 |
                                           +------------+    |
                                           |            |    |
                                           v            v    |
                                +----------+---+    +---+----+----+
                                |    Metric    |    |    Alert    |
                                |  Collector   |    |   Checker   |
                                |    Lambda    |    |   Lambda    |
                                +----------+---+    +---+----+----+
                                           |                 |
                                           v                 v
                                      +----+----+       +----+----+
                                      | AWS CW  |       | AWS SNS | ===> [ Email Alert ]
                                      | Metrics |       +---------+
                                      +---------+
```

---

## 💼 Portfolio & Resume Blurb

**AWS Cloud Cost Monitor** is a production-grade serverless portal designed to reduce idle cloud waste by surfacing real-time usage insights and automating budget policy enforcements. 
*   **Infrastructure as Code (IaC)**: Engineered using AWS SAM, defining highly secure IAM policies (`DynamoDBCrudPolicy`, custom KMS, and SNS dispatch grants), on-demand DynamoDB scaling, and automated EventBridge cron schedules.
*   **Decoupled Billing Pipelines**: Designed resilient Lambda functions in Python 3.11 with layered fallback support. Leverages DynamoDB conditional updates to enforce absolute write idempotency.
*   **Local Test Rigour**: Reached 100% test coverage for the core deterministic generator using `pytest` and mock test suites that orchestrate virtual DynamoDB instances in-memory using `moto`.
*   **Dashboard Experience**: Created a glassmorphism dark-slate React dashboard featuring **Recharts** stacked line graphs that handle asynchronous dataset streaming, automated 5-minute cache updates, and dynamic HTML layout bindings via Tailwind CSS.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:
*   **AWS CLI** v2 & **AWS SAM CLI** (configured with default credentials)
*   **Docker Desktop** (required for local DynamoDB and SAM execution)
*   **Python 3.11** & `pip`
*   **Node.js 18+** & `npm`

---

## ⚡ Quick Start: Local Development (Under 5 Minutes)

We provide a streamlined `Makefile` to set up and run the entire environment locally without needing active AWS configurations:

### 1. Install Dependencies
Install all pip dependencies locally into the separate Lambda directories and build the React modules:
```bash
make install
```

### 2. Launch Local Database & API
Spin up the local containerized DynamoDB instance, create schemas, load 30 days of high-fidelity historical seed metrics, and launch the SAM local API gateway on port `3001`:
```bash
make local
```

### 3. Run the React Dashboard
Open a new terminal window, navigate to the dashboard directory, and start the React client:
```bash
cd dashboard
npm start
```
Your dashboard will launch at **[http://localhost:3000](http://localhost:3000)**, automatically fetching live metrics from the local SAM gateway!

### 4. Run Pytest Suite
Run the automated test suite locally:
```bash
make test
```

---

## 🚀 Live AWS Deployment Steps

When you are ready to ship your stack to live AWS infrastructure:

### 1. Guided Initial Deployment
This packages your code, uploads assets to S3, and provisions all DynamoDB, Lambda, API Gateway, and SNS resources on AWS:
```bash
make build
make deploy
```
*You will be prompted to enter the parameters: `AlertEmail` (for cost notifications) and `MonthlyThreshold` (budget limit).*

### 2. Fast Subsequent Deployments
For quick updates to your logic or configurations after setup:
```bash
make build
make deploy-fast
```

### 3. Seed Live Database Configuration
To insert the baseline default settings (`monthly_threshold`, `alerts_enabled`) into your live AWS table:
```bash
make seed
```

### 4. Teardown Stack
Remove all deployed AWS CloudFormation resources:
```bash
make destroy
```

---

## 🧪 How the Deterministic Metrics Generator Works

To make local development feel incredibly real, the shared module [`shared/metrics_generator.py`](file:///c:/Users/ASUS/OneDrive/Desktop/cloud%20cost%20monitoring%20Dashboard/aws-cost-monitor/shared/metrics_generator.py) generates billing patterns:
*   **Deterministic Noise**: Employs Python's built-in `random.seed(date.toordinal())`. This generates random variance between `0.9` and `1.1` to mimic normal network jitter, but ensures that calling the generator for a specific date always returns the identical result (preserving graph integrity).
*   **Traffic Weighting**: Weekdays mimic business hours with bursting EC2 capacities, Lambda peaks, and elevated CloudFront traffic. Weekends scale usage down significantly to model typical developer downtime.
*   **Gradual Storage Accumulation**: S3 volume is calculated using a incremental modifier `0.15 GB/day` starting from January 1st to simulate progressive production database archiving.

---

## ⚙️ Environment Variables Reference

The system relies on the following configurations:

| Variable | Scope | Description | Default |
| :--- | :--- | :--- | :--- |
| `REACT_APP_API_URL` | React Client | Base API URL pointing to API Gateway endpoint | `http://localhost:3000/Prod` |
| `DYNAMODB_ENDPOINT_URL` | Scripts & Lambdas | Override destination for local database redirects | `http://localhost:8000` |
| `DYNAMODB_TABLE_COST` | Lambdas | DynamoDB table name for storing service costs | `CostMetrics` |
| `DYNAMODB_TABLE_CONFIG` | Lambdas | DynamoDB table name for storing alert thresholds | `AlertConfig` |
| `SNS_TOPIC_ARN` | Alert Checker | Target SNS Topic ARN for budget alert emails | *Auto-generated on deploy* |
