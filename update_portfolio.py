#!/usr/bin/env python3
"""
Daily Portfolio Update Script
============================
This script allows you to quickly update your ETF portfolio values.
You can run this manually or set it up as a cron job for daily updates.

Usage:
    python update_portfolio.py --nasdaq 21500.00 --btcc 2650.00 --zsp 23500.00
    python update_portfolio.py  (will prompt for values)
"""

import argparse
import requests
import json
import sys

def update_portfolio_values(nasdaq_value, btcc_value, zsp_value, host='localhost', port=5005):
    """Update portfolio values via API"""
    url = f"http://{host}:{port}/api/portfolio/update_daily"
    
    data = {
        'nasdaq_value': float(nasdaq_value),
        'btcc_value': float(btcc_value),
        'zsp_value': float(zsp_value)
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Portfolio updated successfully!")
            print(f"📅 Date: {result['date']}")
            print(f"💰 Total Portfolio Value: ${result['total_portfolio_value']:,.2f}")
            print(f"📈 Profit/Loss: ${result['profit_loss']:+,.2f} ({result['profit_loss_percentage']:+.2f}%)")
            print(f"📊 Change from Yesterday: ${result['difference_from_yesterday']:+,.2f}")
            return True
        else:
            error = response.json().get('error', 'Unknown error')
            print(f"❌ Error updating portfolio: {error}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to the app at http://{host}:{port}")
        print("Make sure the Flask app is running: python app.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def get_user_input():
    """Get ETF values from user input"""
    print("📊 Daily Portfolio Update")
    print("=" * 30)
    
    try:
        nasdaq = float(input("Enter NASDAQ/NAS current value ($): ").strip())
        btcc = float(input("Enter BTCC current value ($): ").strip())
        zsp = float(input("Enter ZSP current value ($): ").strip())
        
        total = nasdaq + btcc + zsp
        print(f"\n💰 Total Portfolio Value: ${total:,.2f}")
        
        confirm = input("Confirm update? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Update cancelled.")
            return None, None, None
            
        return nasdaq, btcc, zsp
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")
        return None, None, None
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled.")
        return None, None, None

def main():
    parser = argparse.ArgumentParser(description='Update daily portfolio values')
    parser.add_argument('--nasdaq', type=float, help='NASDAQ/NAS ETF current value')
    parser.add_argument('--btcc', type=float, help='BTCC ETF current value')
    parser.add_argument('--zsp', type=float, help='ZSP ETF current value')
    parser.add_argument('--host', default='localhost', help='Flask app host (default: localhost)')
    parser.add_argument('--port', type=int, default=5005, help='Flask app port (default: 5005)')
    
    args = parser.parse_args()
    
    # If values provided via command line
    if all([args.nasdaq, args.btcc, args.zsp]):
        nasdaq_value = args.nasdaq
        btcc_value = args.btcc
        zsp_value = args.zsp
    else:
        # Get values from user input
        nasdaq_value, btcc_value, zsp_value = get_user_input()
        if nasdaq_value is None:
            sys.exit(1)
    
    # Update portfolio
    success = update_portfolio_values(nasdaq_value, btcc_value, zsp_value, args.host, args.port)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()