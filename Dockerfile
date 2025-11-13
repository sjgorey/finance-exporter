FROM python:3.12-slim

# Create non-root user
RUN groupadd -r exporter && useradd -r -g exporter exporter

WORKDIR /app

# Install required packages
RUN pip install --no-cache-dir prometheus_client yfinance schedule pytz

# Create cache directory for yfinance with proper permissions
RUN mkdir -p /app/.cache && chown -R exporter:exporter /app/.cache

# Copy exporter script and set ownership
COPY finance_exporter.py .
RUN chown -R exporter:exporter /app

# Switch to non-root user
USER exporter

# Set environment for cache location
ENV XDG_CACHE_HOME=/app/.cache

# Expose Prometheus metrics port
EXPOSE 8080

CMD ["python", "finance_exporter.py"]