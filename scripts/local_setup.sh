#!/bin/bash

# Exit on any failure
set -e

echo "============================================="
echo "⚙️  AWS Cost Monitor - Local Environment Setup"
echo "============================================="

# 1. Spin up DynamoDB Local via Docker-Compose
echo -e "\n🐳 1. Starting local DynamoDB container..."
docker-compose up -d

# 2. Wait for DynamoDB local port to accept connections
echo -e "\n⏳ 2. Waiting for DynamoDB local (port 8000) to spin up..."
for i in {1..30}; do
  if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ DynamoDB Local is ready and accepting requests."
    break
  fi
  echo "   [Waiting for DB engine... attempt $i/30]"
  sleep 1
done

# 3. Create tables
echo -e "\n🛠️  3. Creating local DynamoDB schemas..."
python scripts/setup_dynamodb.py

# 4. Seed Alert Configuration
echo -e "\n🌱 4. Seeding default configurations ('main')..."
python scripts/seed_config.py

# 5. Backfill 30 days of mock metrics
echo -e "\n📊 5. Backfilling 30-day historical metrics..."
python scripts/backfill_metrics.py

echo -e "\n============================================="
echo "🎉 Local environment is fully primed and ready!"
echo "Run 'bash scripts/run_local.sh' to start the SAM local API."
echo "============================================="
