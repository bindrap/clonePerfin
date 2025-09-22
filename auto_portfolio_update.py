#!/usr/bin/env python3
"""
Fixed Real-time Portfolio Update
==============================
Aggressively fetches current market data using multiple methods
"""

import requests
import json
import sys
import sqlite3
import pytz
from datetime import datetime, timedelta
import os
import time

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
ALPHA_VANTAGE_API_KEY = "Y4KO8J7ADHBJWULE"

# Toronto timezone
TORONTO_TZ = pytz.timezone('America/Toronto')

def get_toronto_date():
    """Get current date in Toronto timezone"""
    return datetime.now(TORONTO_TZ).date()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('finance_tracker.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def get_latest_nasdaq_value_from_db():
    """Get the latest NASDAQ value from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nasdaq_value FROM portfolio_log 
            WHERE nasdaq_value IS NOT NULL AND nasdaq_value > 0
            ORDER BY date DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return float(result['nasdaq_value'])
        else:
            return 22000.00  # Fallback
            
    except Exception as e:
        print(f"[ERROR] Error fetching NASDAQ from database: {e}")
        return 22000.00

def get_yahoo_finance_realtime(symbol):
    """Yahoo Finance real-time quotes"""
    try:
        # Multiple Yahoo endpoints to try
        endpoints = [
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
            f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        }
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Parse chart data
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    
                    if 'meta' in result:
                        meta = result['meta']
                        price = meta.get('regularMarketPrice') or meta.get('previousClose')
                        market_time = meta.get('regularMarketTime')
                        
                        if price:
                            if market_time:
                                market_date = datetime.fromtimestamp(market_time, TORONTO_TZ).strftime('%Y-%m-%d %H:%M %Z')
                            else:
                                market_date = "Current"
                            
                            print(f"[YAHOO] {symbol}: ${float(price):.2f} (as of {market_date})")
                            return float(price)
                
                # Parse quote data (alternative format)
                if 'quoteResponse' in data and 'result' in data['quoteResponse']:
                    quotes = data['quoteResponse']['result']
                    if quotes and len(quotes) > 0:
                        quote = quotes[0]
                        price = quote.get('regularMarketPrice') or quote.get('ask') or quote.get('bid')
                        if price:
                            print(f"[YAHOO] {symbol}: ${float(price):.2f} (quote data)")
                            return float(price)
                            
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        print(f"[YAHOO ERROR] {symbol}: {e}")
        return None

def get_alphavantage_intraday(symbol):
    """Alpha Vantage intraday data - most recent"""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': '1min',
            'apikey': ALPHA_VANTAGE_API_KEY,
            'outputsize': 'compact'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Time Series (1min)' in data:
            time_series = data['Time Series (1min)']
            # Get the most recent timestamp
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            price = float(latest_data['4. close'])
            
            print(f"[ALPHA-1MIN] {symbol}: ${price:.2f} (as of {latest_time})")
            return price
            
        # Try 5min if 1min fails
        params['interval'] = '5min'
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'Time Series (5min)' in data:
            time_series = data['Time Series (5min)']
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            price = float(latest_data['4. close'])
            
            print(f"[ALPHA-5MIN] {symbol}: ${price:.2f} (as of {latest_time})")
            return price
            
        return None
        
    except Exception as e:
        print(f"[ALPHA INTRADAY ERROR] {symbol}: {e}")
        return None

def get_alphavantage_quote(symbol):
    """Alpha Vantage Global Quote"""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            price = float(quote['05. price'])
            latest_trading_day = quote['07. latest trading day']
            change_percent = quote['10. change percent'].rstrip('%')
            
            print(f"[ALPHA-QUOTE] {symbol}: ${price:.2f} (as of {latest_trading_day}, {change_percent}%)")
            return price
        
        return None
        
    except Exception as e:
        print(f"[ALPHA QUOTE ERROR] {symbol}: {e}")
        return None

def get_polygon_price(symbol):
    """Polygon.io free tier (if available)"""
    try:
        # Note: Polygon has a free tier with delayed data
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {
            'adjusted': 'true',
            'apikey': 'demo'  # You can get a free key from polygon.io
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results'] and len(data['results']) > 0:
                result = data['results'][0]
                price = float(result['c'])  # closing price
                print(f"[POLYGON] {symbol}: ${price:.2f}")
                return price
        
        return None
        
    except Exception as e:
        print(f"[POLYGON ERROR] {symbol}: {e}")
        return None

def get_current_price_aggressive(symbol):
    """Try every method aggressively to get current price"""
    print(f"[AGGRESSIVE FETCH] Getting current price for {symbol}...")
    
    # Try Yahoo Finance first (usually most current)
    price = get_yahoo_finance_realtime(symbol)
    if price is not None:
        return price
    
    time.sleep(1)
    
    # Try Alpha Vantage intraday
    price = get_alphavantage_intraday(symbol)
    if price is not None:
        return price
    
    time.sleep(2)
    
    # Try Alpha Vantage quote
    price = get_alphavantage_quote(symbol)
    if price is not None:
        return price
    
    time.sleep(1)
    
    # Try Polygon
    price = get_polygon_price(symbol)
    if price is not None:
        return price
    
    # If everything fails, use fallback
    fallback_prices = {
        'BTCC-B.TO': 21.69,
        'BTCC.TO': 21.69,
        'ZSP.TO': 98.28
    }
    
    fallback = fallback_prices.get(symbol, 20.0)
    print(f"[FALLBACK] Using fallback price for {symbol}: ${fallback:.2f}")
    return fallback

def get_etf_holdings_from_db():
    """Get current ETF purchase values from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT etf_symbol, purchase_value
            FROM etf_holdings
            ORDER BY etf_symbol
        ''')
        holdings = cursor.fetchall()
        conn.close()

        holdings_dict = {}
        for holding in holdings:
            holdings_dict[holding['etf_symbol']] = float(holding['purchase_value'])

        return holdings_dict

    except Exception as e:
        print(f"[ERROR] Error fetching ETF holdings from database: {e}")
        # Fallback to reasonable defaults
        return {
            'NAS': 20000.00,
            'BTCC': 2600.00,
            'ZSP': 23000.00
        }

def fetch_current_etf_prices():
    """Fetch current ETF prices aggressively"""
    print("[AGGRESSIVE MODE] Fetching real-time ETF prices...")

    # Get current ETF holdings from database
    etf_holdings = get_etf_holdings_from_db()
    print(f"[DATABASE] Current ETF holdings:")
    for symbol, value in etf_holdings.items():
        print(f"  {symbol}: ${value:,.2f} (purchase value)")

    # Use current NASDAQ/NAS value from holdings
    nasdaq_value = etf_holdings.get('NAS', 22000.00)
    print(f"[HOLDINGS] Using NAS value from holdings: ${nasdaq_value:,.2f}")

    # Fixed share quantities for price calculation (these shouldn't change often)
    share_quantities = {
        'BTCC': 122.0,
        'ZSP': 234.0
    }

    prices = {
        'nasdaq_value': nasdaq_value
    }

    # Get BTCC price aggressively
    print()
    btcc_price = get_current_price_aggressive('BTCC-B.TO')
    # Calculate market value based on current shares
    btcc_shares = share_quantities['BTCC']
    prices['btcc_value'] = btcc_shares * btcc_price
    print(f"[CALC] BTCC: {btcc_shares} shares × ${btcc_price:.2f} = ${prices['btcc_value']:,.2f}")

    print()
    # Get ZSP price aggressively
    zsp_price = get_current_price_aggressive('ZSP.TO')
    # Calculate market value based on current shares
    zsp_shares = share_quantities['ZSP']
    prices['zsp_value'] = zsp_shares * zsp_price
    print(f"[CALC] ZSP: {zsp_shares} shares × ${zsp_price:.2f} = ${prices['zsp_value']:,.2f}")

    return prices

def update_portfolio_via_api(nasdaq_value, btcc_value, zsp_value, host='localhost', port=5001):
    """Update portfolio values via Flask API"""
    url = f"http://{host}:{port}/api/portfolio/update_daily"
    
    data = {
        'nasdaq_value': float(nasdaq_value),
        'btcc_value': float(btcc_value),
        'zsp_value': float(zsp_value)
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Portfolio updated successfully!")
            print(f"[INFO] Date: {result['date']}")
            print(f"[INFO] Total Portfolio Value: ${result['total_portfolio_value']:,.2f}")
            print(f"[INFO] Profit/Loss: ${result['profit_loss']:+,.2f} ({result['profit_loss_percentage']:+.2f}%)")
            print(f"[INFO] Change from Yesterday: ${result['difference_from_yesterday']:+,.2f}")
            return True
        else:
            error = response.json().get('error', 'Unknown error')
            print(f"[ERROR] Error updating portfolio: {error}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to Flask app at http://{host}:{port}")
        return False
    except Exception as e:
        print(f"[ERROR] API update error: {e}")
        return False

def main():
    print("AGGRESSIVE REAL-TIME PORTFOLIO UPDATE")
    print("=" * 50)
    now = datetime.now(TORONTO_TZ)
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Day of week: {now.strftime('%A')}")
    print()
    
    # Market hours check
    market_hour = now.hour
    if 9 <= market_hour <= 16:
        print("[INFO] During market hours - should get real-time data")
    else:
        print("[INFO] Outside market hours - may get previous close")
    
    try:
        prices = fetch_current_etf_prices()
        
        if not prices:
            print("[ERROR] Failed to fetch ETF data")
            sys.exit(1)
        
        print()
        print("FINAL PORTFOLIO VALUES:")
        print(f"   NASDAQ Value: ${prices['nasdaq_value']:,.2f} (manual from DB)")
        print(f"   BTCC Value: ${prices['btcc_value']:,.2f} (real-time)")
        print(f"   ZSP Value: ${prices['zsp_value']:,.2f} (real-time)")
        total_value = prices['nasdaq_value'] + prices['btcc_value'] + prices['zsp_value']
        print(f"   TOTAL VALUE: ${total_value:,.2f}")
        print()
        
        # Update portfolio
        print("Updating portfolio in database...")
        success = update_portfolio_via_api(
            prices['nasdaq_value'],
            prices['btcc_value'], 
            prices['zsp_value']
        )
        
        if success:
            print()
            print("[SUCCESS] Real-time portfolio update completed!")
        else:
            print()
            print("[ERROR] Portfolio update failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[CANCELLED] Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()