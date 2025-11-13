#!/usr/bin/env python3
"""
Simple Yahoo Finance Prometheus Exporter using yfinance directly
"""

import time
import yfinance as yf
import schedule
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
from datetime import datetime, timedelta
import pytz
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Set cache location for yfinance to avoid permission issues
if 'XDG_CACHE_HOME' in os.environ:
    yf.set_tz_cache_location(os.environ['XDG_CACHE_HOME'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
stock_price = Gauge('yahoo_finance_stock_price', 'Current stock price', ['symbol'])
stock_volume = Gauge('yahoo_finance_stock_volume', 'Current stock volume', ['symbol'])
stock_market_cap = Gauge('yahoo_finance_market_cap', 'Market capitalization', ['symbol'])
stock_open = Gauge('yahoo_finance_stock_open', 'Opening price', ['symbol'])
stock_high = Gauge('yahoo_finance_stock_high', 'Daily high', ['symbol'])
stock_low = Gauge('yahoo_finance_stock_low', 'Daily low', ['symbol'])
stock_change_percent = Gauge('yahoo_finance_change_percent', 'Daily change percentage', ['symbol'])
last_updated = Gauge('yahoo_finance_last_updated', 'Unix timestamp of last successful update')

# Configuration from environment variables
SYMBOLS = os.getenv('SYMBOLS', 'AAPL,GOOGL,MSFT,TSLA,SPY,QQQ,NVDA,AMD,AMZN,META,WEX,F,GE,BAC,C,JPM').split(',')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '30'))
METRICS_PORT = int(os.getenv('METRICS_PORT', '8080'))

class MetricsHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler that only serves metrics during market hours"""
    
    def __init__(self, exporter, *args, **kwargs):
        self.exporter = exporter
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/metrics':
            if self.exporter.is_market_open():
                # Market is open - serve current metrics
                try:
                    output = generate_latest()
                    self.send_response(200)
                    self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                    self.end_headers()
                    self.wfile.write(output)
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error generating metrics: {e}'.encode())
            else:
                # Market is closed - return 503 Service Unavailable
                message = "Market closed - metrics not available until next market open\n"
                next_open_seconds = self.exporter.get_seconds_until_market_open()
                next_open_hours = next_open_seconds // 3600
                next_open_mins = (next_open_seconds % 3600) // 60
                message += f"Market opens in: {next_open_hours}h {next_open_mins}m\n"
                
                self.send_response(503)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(message.encode())
        elif parsed_path.path == '/healthz':
            # Health check endpoint - always available
            try:
                # Simple health check - verify we can connect and app is running
                status = {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "market_open": self.exporter.is_market_open()
                }
                
                if self.exporter.is_market_open():
                    status["next_market_close"] = self.exporter.get_seconds_until_market_close()
                else:
                    status["next_market_open"] = self.exporter.get_seconds_until_market_open()
                
                response = "OK\n"
                response += f"Status: {status['status']}\n"
                response += f"Market Open: {status['market_open']}\n"
                
                if "next_market_close" in status:
                    close_hours = status["next_market_close"] // 3600
                    close_mins = (status["next_market_close"] % 3600) // 60
                    response += f"Market closes in: {close_hours}h {close_mins}m\n"
                elif "next_market_open" in status:
                    open_hours = status["next_market_open"] // 3600
                    open_mins = (status["next_market_open"] % 3600) // 60
                    response += f"Market opens in: {open_hours}h {open_mins}m\n"
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(response.encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Health check failed: {e}'.encode())
        else:
            # Not /metrics or /healthz endpoint
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found - try /metrics or /healthz')
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

class FinanceExporter:
    def __init__(self):
        # Set up timezone for market hours
        self.et_tz = pytz.timezone('US/Eastern')
        
    def is_market_open(self):
        """Check if the stock market is currently open"""
        now_et = datetime.now(self.et_tz)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now_et.weekday() >= 5:  # Saturday or Sunday
            return False
            
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_et <= market_close
        
    def get_seconds_until_market_open(self):
        """Get seconds until next market open"""
        now_et = datetime.now(self.et_tz)
        
        # If market is open now, return 0
        if self.is_market_open():
            return 0
            
        # Find next market open
        next_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # If we're past market close today or it's weekend, move to next business day
        if now_et.hour >= 16 or now_et.weekday() >= 5:
            next_open += timedelta(days=1)
            
        # Skip weekends
        while next_open.weekday() >= 5:
            next_open += timedelta(days=1)
            
        return int((next_open - now_et).total_seconds())
        
    def get_seconds_until_market_close(self):
        """Get seconds until market close today"""
        now_et = datetime.now(self.et_tz)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if now_et >= market_close:
            return 0
            
        return int((market_close - now_et).total_seconds())
        
    def get_quote(self, symbol):
        """Get stock quote directly from Yahoo Finance using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
                
            latest = hist.iloc[-1]
            
            return {
                'symbol': symbol,
                'currentPrice': info.get('currentPrice', latest['Close']),
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'volume': latest['Volume'],
                'marketCap': info.get('marketCap'),
                'previousClose': info.get('previousClose', latest['Close']),
            }
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def update_metrics(self):
        """Update Prometheus metrics for all symbols"""            
        logger.info("Updating metrics...")
        
        for symbol in SYMBOLS:
            try:
                quote = self.get_quote(symbol)
                
                if quote:
                    # Update price metrics
                    price = quote.get('currentPrice')
                    if price:
                        stock_price.labels(symbol=symbol).set(float(price))
                        
                    # Update OHLV metrics
                    if quote.get('open'):
                        stock_open.labels(symbol=symbol).set(float(quote['open']))
                    if quote.get('high'):
                        stock_high.labels(symbol=symbol).set(float(quote['high']))
                    if quote.get('low'):
                        stock_low.labels(symbol=symbol).set(float(quote['low']))
                        
                    # Update volume metric
                    volume = quote.get('volume')
                    if volume:
                        stock_volume.labels(symbol=symbol).set(float(volume))
                        
                    # Update market cap
                    market_cap = quote.get('marketCap')
                    if market_cap:
                        stock_market_cap.labels(symbol=symbol).set(float(market_cap))
                        
                    # Calculate change percentage
                    prev_close = quote.get('previousClose')
                    if price and prev_close:
                        change_pct = ((float(price) - float(prev_close)) / float(prev_close)) * 100
                        stock_change_percent.labels(symbol=symbol).set(change_pct)
                        
                    logger.info(f"Updated {symbol}: ${price}")
                    
                else:
                    logger.warning(f"No data received for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        # Update the last_updated timestamp
        last_updated.set(time.time())
        logger.info("Metrics update complete")
    
    def run(self):
        """Run the exporter with smart scheduling"""
        logger.info("Starting Yahoo Finance Prometheus Exporter (Direct yfinance)")
        logger.info(f"Monitoring symbols: {', '.join(SYMBOLS)}")
        logger.info("Smart scheduler: Updates only during market hours, sleeps when closed")
        
        # Start custom HTTP server that respects market hours
        def handler_factory(*args, **kwargs):
            return MetricsHandler(self, *args, **kwargs)
        
        server = HTTPServer(('', METRICS_PORT), handler_factory)
        
        # Start server in a separate thread to avoid blocking
        import threading
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        logger.info(f"Market-aware metrics server started on :{METRICS_PORT}")
        logger.info(f"Metrics available at http://localhost:{METRICS_PORT}/metrics (during market hours only)")
        
        while True:
            if self.is_market_open():
                logger.info("Market is open - starting active monitoring")
                
                # Clear any existing schedules
                schedule.clear()
                
                # Schedule updates based on configured interval during market hours
                schedule.every(UPDATE_INTERVAL).seconds.do(self.update_metrics)
                
                # Run initial update
                self.update_metrics()
                
                # Keep updating until market closes
                while self.is_market_open():
                    schedule.run_pending()
                    time.sleep(1)
                    
                logger.info("Market closed - stopping active monitoring")
                schedule.clear()
                
            else:
                # Market is closed - sleep until next open
                sleep_seconds = self.get_seconds_until_market_open()
                sleep_minutes = sleep_seconds // 60
                sleep_hours = sleep_minutes // 60
                
                logger.info(f"Market closed - sleeping for {sleep_hours}h {sleep_minutes % 60}m until next open")
                
                # Sleep in chunks to allow for graceful shutdown
                while sleep_seconds > 0 and not self.is_market_open():
                    chunk = min(300, sleep_seconds)  # Sleep max 5 minutes at a time
                    time.sleep(chunk)
                    sleep_seconds -= chunk

if __name__ == "__main__":
    exporter = FinanceExporter()
    exporter.run()