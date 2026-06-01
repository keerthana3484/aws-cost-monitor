.PHONY: install test build deploy deploy-fast local seed destroy

# Variables
METRIC_COLLECTOR_DIR = functions/metric-collector
ALERT_CHECKER_DIR = functions/alert-checker
API_HANDLER_DIR = functions/api-handler

install:
	@echo "Installing root development dependencies..."
	pip install -r requirements.txt
	@echo "Installing Metric Collector function dependencies..."
	pip install -r $(METRIC_COLLECTOR_DIR)/requirements.txt -t $(METRIC_COLLECTOR_DIR)/
	@echo "Installing Alert Checker function dependencies..."
	pip install -r $(ALERT_CHECKER_DIR)/requirements.txt -t $(ALERT_CHECKER_DIR)/
	@echo "Installing API Handler function dependencies..."
	pip install -r $(API_HANDLER_DIR)/requirements.txt -t $(API_HANDLER_DIR)/
	@echo "Installing dashboard front-end dependencies..."
	cd dashboard && npm install
	@echo "✅ All dependencies installed successfully."

test:
	@echo "Running pytest suite..."
	pytest tests/

build:
	@echo "Building serverless application using AWS SAM..."
	sam build

deploy:
	@echo "Guided deployment to live AWS environment..."
	sam deploy --guided

deploy-fast:
	@echo "Fast deployment to live AWS environment (using previous configs)..."
	sam deploy

local:
	@echo "Bootstrapping local DynamoDB Local database & backfilling historical metrics..."
	bash scripts/local_setup.sh
	@echo "Starting local API Gateway execution..."
	bash scripts/run_local.sh

seed:
	@echo "Seeding default alarm config configurations against target DynamoDB..."
	@if [ -z "$$DYNAMODB_TABLE_CONFIG" ]; then \
		echo "⚠️ Warning: DYNAMODB_TABLE_CONFIG not specified, defaulting to 'AlertConfig'"; \
	fi
	python scripts/seed_config.py

destroy:
	@echo "Deleting AWS SAM deployment stack..."
	sam delete
