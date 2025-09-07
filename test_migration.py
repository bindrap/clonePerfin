#!/usr/bin/env python3
"""
Test script to verify migration results
"""

import sqlite3
import pandas as pd
from datetime import datetime

def test_migration_results():
    print("🔍 Testing Migration Results")
    print("=" * 50)
    
    conn = sqlite3.connect('finance_tracker.db')
    
    # 1. Overall counts
    print("\n📊 Overall Statistics:")
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM spending_log')
    total_spending = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM personal_log')
    total_personal = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM budget_periods')
    total_periods = cursor.fetchone()[0]
    
    print(f"   Spending records: {total_spending}")
    print(f"   Personal records: {total_personal}")
    print(f"   Budget periods: {total_periods}")
    
    # 2. Date range
    print("\n📅 Date Range:")
    cursor.execute('SELECT MIN(date), MAX(date) FROM spending_log')
    min_date, max_date = cursor.fetchone()
    print(f"   From: {min_date}")
    print(f"   To: {max_date}")
    
    # 3. Top spending categories/items
    print("\n💰 Top 10 Most Frequent Items:")
    cursor.execute('''
        SELECT item, COUNT(*) as frequency, SUM(price) as total_spent, AVG(price) as avg_price
        FROM spending_log 
        GROUP BY item 
        ORDER BY frequency DESC 
        LIMIT 10
    ''')
    
    for item, freq, total, avg in cursor.fetchall():
        print(f"   {item}: {freq} times, Total: ${total:.2f}, Avg: ${avg:.2f}")
    
    # 4. Monthly breakdown
    print("\n📈 Monthly Spending:")
    cursor.execute('''
        SELECT strftime('%Y-%m', date) as month, 
               COUNT(*) as transactions, 
               SUM(price) as total_spent
        FROM spending_log 
        GROUP BY strftime('%Y-%m', date) 
        ORDER BY month DESC
    ''')
    
    for month, transactions, total in cursor.fetchall():
        print(f"   {month}: {transactions} transactions, ${total:.2f}")
    
    # 5. Sample of detailed data
    print("\n📋 Sample Recent Transactions:")
    cursor.execute('''
        SELECT date, item, price 
        FROM spending_log 
        ORDER BY date DESC, id DESC 
        LIMIT 15
    ''')
    
    for date, item, price in cursor.fetchall():
        print(f"   {date}: {item} - ${price:.2f}")
    
    # 6. Check for any potential data issues
    print("\n⚠️  Data Quality Check:")
    cursor.execute('SELECT COUNT(*) FROM spending_log WHERE price <= 0')
    negative_prices = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM spending_log WHERE price > 1000')
    high_prices = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM spending_log WHERE item IS NULL OR item = ""')
    empty_items = cursor.fetchone()[0]
    
    print(f"   Negative/zero prices: {negative_prices}")
    print(f"   Very high prices (>$1000): {high_prices}")
    print(f"   Empty item names: {empty_items}")
    
    if high_prices > 0:
        print("\n   High-priced items:")
        cursor.execute('SELECT date, item, price FROM spending_log WHERE price > 1000 ORDER BY price DESC')
        for date, item, price in cursor.fetchall():
            print(f"     {date}: {item} - ${price:.2f}")
    
    # 7. Verify against original Excel (if you want to spot-check)
    print("\n📊 Spot Check - Nov 8-21 Period:")
    cursor.execute('''
        SELECT COUNT(*) as count, SUM(price) as total
        FROM spending_log 
        WHERE date BETWEEN '2024-11-08' AND '2024-11-21'
    ''')
    nov_count, nov_total = cursor.fetchone()
    print(f"   Nov 8-21: {nov_count} transactions, ${nov_total:.2f} total")
    
    conn.close()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_migration_results()