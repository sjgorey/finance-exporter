# Finance Exporter

![Build Status](https://github.com/sjgorey/finance-exporter/actions/workflows/build-and-push.yml/badge.svg)

A Prometheus exporter that monitors stock prices and financial metrics from Yahoo Finance.

## Overview

This application exports financial metrics for various stocks to Prometheus, including:
- Current stock price
- Opening price, high, low
- Volume
- Market capitalization
- Daily change percentage

## Features

- Smart scheduling: Only updates during market hours (9:30 AM - 4:00 PM ET, weekdays)
- Automatic market hours detection with timezone handling
- Sleep mode when markets are closed
- Prometheus metrics export on configurable port (default: 8080)
- Configurable stock symbols via environment variables
- Configurable update interval

## Configuration

The application is configured using environment variables:

- **SYMBOLS**: Comma-separated list of stock symbols to monitor (default: "AAPL,GOOGL,MSFT,TSLA,SPY,QQQ,NVDA,AMD,AMZN,META,WEX,F,GE,BAC,C,JPM")
- **UPDATE_INTERVAL**: Update frequency in seconds (default: 30)
- **METRICS_PORT**: Port for Prometheus metrics (default: 8080)
- **TZ**: Timezone for market hours calculation

## Building and Pushing the Container Image

### Automated Builds (Recommended)

This repository includes GitHub Actions for automatic building and publishing:

- **Automatic builds** on every push to `main` branch
- **Multi-platform support** (AMD64 and ARM64)  
- **Automatic tagging** based on Git refs
- **Security attestation** for build provenance

See [GitHub Actions Setup](.github/ACTIONS.md) for configuration details.

### Manual Build (Development)

### Prerequisites

- Docker installed and running
- Access to push to the target registry (Docker Hub, etc.)
- Logged into Docker registry: `docker login`

### Build Commands

```bash
# Navigate to the finance-exporter directory
cd /home/sgorey/projects/finance-exporter

# Build the image with latest tag
docker build -t sjgorey/finance-exporter:latest .

# Build with a specific version tag
docker build -t sjgorey/finance-exporter:v1.0.0 .

# Build with multiple tags
docker build -t sjgorey/finance-exporter:latest -t sjgorey/finance-exporter:v1.0.0 .
```

### Push Commands

```bash
# Push the latest tag
docker push sjgorey/finance-exporter:latest

# Push a specific version
docker push sjgorey/finance-exporter:v1.0.0

# Push all tags for the image
docker push --all-tags sjgorey/finance-exporter
```

### Complete Build and Push Workflow

```bash
#!/bin/bash
# Complete build and push script

cd /home/sgorey/projects/finance-exporter

# Set version (update as needed)
VERSION="v1.0.0"

echo "Building finance-exporter image..."
docker build -t sjgorey/finance-exporter:latest -t sjgorey/finance-exporter:${VERSION} .

if [ $? -eq 0 ]; then
    echo "Build successful! Pushing to registry..."
    docker push sjgorey/finance-exporter:latest
    docker push sjgorey/finance-exporter:${VERSION}
    echo "Push complete!"
else
    echo "Build failed!"
    exit 1
fi
```

### Alternative: Using Docker Buildx (for multi-platform builds)

```bash
# Create a new builder instance (one-time setup)
docker buildx create --name finance-builder --use

# Build for multiple platforms and push
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t sjgorey/finance-exporter:latest \
    -t sjgorey/finance-exporter:v1.0.0 \
    --push .
```

## Local Testing

Before pushing, you can test the image locally:

```bash
# Run the container locally
docker run -p 8080:8080 --name finance-exporter-test sjgorey/finance-exporter:latest

# Test with custom symbols
docker run -p 8080:8080 \
    -e SYMBOLS="AAPL,GOOGL,MSFT" \
    -e UPDATE_INTERVAL=60 \
    --name finance-exporter-test \
    sjgorey/finance-exporter:latest

# Check metrics endpoint
curl http://localhost:8080/metrics

# Clean up
docker stop finance-exporter-test
docker rm finance-exporter-test
```

## Files

- `finance_exporter.py` - Main application code
- `Dockerfile` - Container build instructions

## Dependencies

The following Python packages are installed in the container:
- `prometheus_client` - Prometheus metrics export
- `yfinance` - Yahoo Finance data fetching
- `schedule` - Task scheduling
- `pytz` - Timezone handling

## Kubernetes Deployment

This application is designed to be deployed on Kubernetes. See the ArgoCD configuration in the `home-argocd-app-config` repository under `infrastructure/finance-exporter/` for deployment manifests.

## Metrics

The application exposes the following Prometheus metrics:

- `yahoo_finance_stock_price` - Current stock price
- `yahoo_finance_stock_volume` - Current stock volume  
- `yahoo_finance_market_cap` - Market capitalization
- `yahoo_finance_stock_open` - Opening price
- `yahoo_finance_stock_high` - Daily high
- `yahoo_finance_stock_low` - Daily low
- `yahoo_finance_change_percent` - Daily change percentage

All metrics include a `symbol` label with the stock ticker symbol.

## Development

To run locally for development:

```bash
# Install dependencies
pip install prometheus_client yfinance schedule pytz

# Run the application
python finance_exporter.py

# Access metrics
curl http://localhost:8080/metrics
```