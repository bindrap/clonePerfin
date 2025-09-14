#!/usr/bin/env python3

import sqlite3
import sys
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('finance_tracker.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def determine_pay_period_type(start_date, end_date):
    """
    Determine if a budget period is first or second half based on the logic:
    - If most days in budget period fall after the 15th → second period (2)
    - If most days fall before 15th → first period (1)
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    total_days = (end_date - start_date).days + 1
    days_after_15th = 0
    current = start_date

    while current <= end_date:
        if current.day > 15:
            days_after_15th += 1
        current += timedelta(days=1)

    return 2 if days_after_15th > (total_days / 2) else 1

def run_migration():
    """Run the database migration for the upgrades"""
    print("Starting database migration for upgrades...")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if pay_period_type column already exists
        cursor.execute("PRAGMA table_info(budget_periods)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'pay_period_type' not in columns:
            print("Adding pay_period_type column to budget_periods table...")
            cursor.execute('''
                ALTER TABLE budget_periods
                ADD COLUMN pay_period_type INTEGER DEFAULT 1
            ''')

            # Update existing budget periods with calculated pay period types
            print("Updating existing budget periods with pay period types...")
            cursor.execute('SELECT id, start_date, end_date FROM budget_periods')
            periods = cursor.fetchall()

            for period in periods:
                pay_period_type = determine_pay_period_type(period['start_date'], period['end_date'])
                cursor.execute('''
                    UPDATE budget_periods
                    SET pay_period_type = ?
                    WHERE id = ?
                ''', (pay_period_type, period['id']))
                print(f"Updated period {period['id']}: {period['start_date']} to {period['end_date']} → Type {pay_period_type}")

        else:
            print("pay_period_type column already exists, skipping...")

        # Check if previous_period_spending column exists in savings_calculations
        cursor.execute("PRAGMA table_info(savings_calculations)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'previous_period_spending' not in columns:
            print("Adding previous_period_spending column to savings_calculations table...")
            cursor.execute('''
                ALTER TABLE savings_calculations
                ADD COLUMN previous_period_spending REAL DEFAULT 0
            ''')
        else:
            print("previous_period_spending column already exists, skipping...")

        conn.commit()
        print("Migration completed successfully!")

        # Show updated budget periods
        print("\nCurrent budget periods:")
        cursor.execute('''
            SELECT id, start_date, end_date, pay_period_type, budget_amount
            FROM budget_periods
            ORDER BY start_date DESC
            LIMIT 5
        ''')
        periods = cursor.fetchall()

        for period in periods:
            period_type_text = "1st half" if period['pay_period_type'] == 1 else "2nd half"
            print(f"  ID {period['id']}: {period['start_date']} to {period['end_date']} - {period_type_text} (${period['budget_amount']})")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)