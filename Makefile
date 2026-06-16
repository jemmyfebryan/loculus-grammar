.PHONY: help install dev start stop restart logs clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PIP) install -r requirements.txt

dev: ## Run the development server
	$(UVICORN) main:app --reload --host 0.0.0.0 --port 9006

start: ## Start the service with PM2
	pm2 start ecosystem.config.js

stop: ## Stop the service with PM2
	pm2 stop grammar-check

restart: ## Restart the service with PM2
	pm2 restart grammar-check

logs: ## View logs with PM2
	pm2 logs grammar-check

status: ## Check PM2 status
	pm2 status

clean: ## Stop and remove PM2 process
	pm2 delete grammar-check

save: ## Save PM2 process list
	pm2 save

reload: ## Reload PM2 (zero-downtime reload)
	pm2 reload grammar-check
