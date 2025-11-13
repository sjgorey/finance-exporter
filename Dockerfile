FROM python:3.12-slim

WORKDIR /app

# Install required packages
RUN pip install --no-cache-dir prometheus_client yfinance schedule pytz

# Copy exporter script
COPY finance_exporter.py .

# Expose Prometheus metrics port
EXPOSE 8080

CMD ["python", "finance_exporter.py"]