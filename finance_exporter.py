#!/usr/bin/env python3
"""
Simple Yahoo Finance Prometheus Exporter using yfinance directly
"""

import time
import yfinance as yf
import schedule
from prometheus_client import start_http_server, Gauge
import logging
from datetime import datetime, timedelta
import pytz
import os

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

# Configuration from environment variables
SYMBOLS = os.getenv('SYMBOLS', 'AAPL,GOOGL,MSFT,TSLA,SPY,QQQ,NVDA,AMD,AMZN,META,WEX,F,GE,BAC,C,JPM').split(',')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '30'))
METRICS_PORT = int(os.getenv('METRICS_PORT', '8080'))

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
                
        logger.info("Metrics update complete")
    
    def run(self):
        """Run the exporter with smart scheduling"""
        logger.info("Starting Yahoo Finance Prometheus Exporter (Direct yfinance)")
        logger.info(f"Monitoring symbols: {', '.join(SYMBOLS)}")
        logger.info("Smart scheduler: Updates only during market hours, sleeps when closed")
        
        # Start Prometheus HTTP server
        start_http_server(METRICS_PORT)
        logger.info(f"Prometheus metrics server started on :{METRICS_PORT}")
        logger.info(f"Metrics available at http://localhost:{METRICS_PORT}/metrics")
        
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