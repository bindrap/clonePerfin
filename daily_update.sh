#!/bin/bash

# Daily Portfolio Update Script
# =============================
# This script can be added to your crontab for daily automation.
# 
# To set up daily updates at 6 PM:
# crontab -e
# Add: 0 18 * * * /path/to/personalWebApp/daily_update.sh
#
# Or run manually whenever you want to update your portfolio.

# Change to script directory
cd "$(dirname "$0")"

# Check if the Flask app is running
if ! curl -s http://localhost:5005 > /dev/null; then
    echo "❌ Flask app is not running. Please start it first with: python app.py"
    exit 1
fi

echo "📊 Daily Portfolio Update - $(date)"
echo "=================================="

# You can either:
# 1. Set fixed values here (uncomment and modify):
# NASDAQ_VALUE=21500.00
# BTCC_VALUE=2650.00
# ZSP_VALUE=23500.00

# 2. Or use the interactive Python script:
python3 update_portfolio.py

# 3. Or call with command line args:
# python3 update_portfolio.py --nasdaq 21500.00 --btcc 2650.00 --zsp 23500.00

echo "Portfolio update completed at $(date)"