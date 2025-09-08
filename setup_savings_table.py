#!/usr/bin/env python3
"""
Database Setup Script for Savings Functionality
===============================================
Creates the required tables for the savings feature
"""

import sqlite3
import os
from datetime import datetime

def setup_savings_tables():
    """Create savings-related tables in the database"""
    
    # Connect to the database
    db_path = 'finance_tracker.db'
    
    if not os.path.exists(db_path):
        print(f"Warning: Database file '{db_path}' not found. Creating new database...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Setting up savings tables...")
        
        # 1. Create savings_config table
        print("Creating savings_config table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS savings_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                savings_percentage REAL NOT NULL DEFAULT 40,
                investorline_percentage REAL NOT NULL DEFAULT 35,
                usd_percentage REAL NOT NULL DEFAULT 25,
                biweekly_income REAL NOT NULL DEFAULT 2000,
                pay_period_half INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Create savings_calculations table
        print("Creating savings_calculations table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS savings_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biweekly_income REAL NOT NULL,
                current_spending REAL NOT NULL,
                fixed_expenses REAL NOT NULL,
                total_expenses REAL NOT NULL,
                available_for_allocation REAL NOT NULL,
                savings_amount REAL NOT NULL,
                investorline_amount REAL NOT NULL,
                usd_amount REAL NOT NULL,
                pay_period_half INTEGER NOT NULL,
                period_start DATE,
                period_end DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. Create fixed_expenses table
        print("Creating fixed_expenses table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fixed_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_name TEXT NOT NULL,
                amount REAL NOT NULL,
                pay_period_half INTEGER NOT NULL,
                is_custom INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.1. Add is_custom column if it doesn't exist (for existing databases)
        print("Checking if is_custom column exists...")
        cursor.execute("PRAGMA table_info(fixed_expenses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_custom' not in columns:
            print("Adding is_custom column to fixed_expenses table...")
            cursor.execute('ALTER TABLE fixed_expenses ADD COLUMN is_custom INTEGER DEFAULT 1')
            print("is_custom column added successfully.")
        else:
            print("is_custom column already exists.")
        
        # 4. Create unique index for fixed_expenses
        print("Creating unique index for fixed_expenses...")
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_expense_period 
            ON fixed_expenses(expense_name, pay_period_half)
        ''')
        
        # 5. Insert default configuration
        print("Inserting default savings configuration...")
        cursor.execute('''
            INSERT OR IGNORE INTO savings_config 
            (savings_percentage, investorline_percentage, usd_percentage, biweekly_income, pay_period_half)
            VALUES (40, 35, 25, 2000, 1)
        ''')
        
        # 6. Insert default expenses if they don't exist
        print("Inserting default expenses...")
        
        default_expenses = [
            # 1st half expenses
            ('Fit4less', 14.50, 1, 0),
            ('Jiu Jitsu', 125.00, 1, 0),
            ('Phone Bill', 45.20, 1, 0),
            ('Car Insurance', 180.00, 1, 0),
            # 2nd half expenses
            ('Ravi Syal', 69.88, 2, 0),
            ('Condo Insurance', 37.74, 2, 0)
        ]
        
        for expense_name, amount, period_half, is_custom in default_expenses:
            cursor.execute('''
                INSERT OR IGNORE INTO fixed_expenses 
                (expense_name, amount, pay_period_half, is_custom, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (expense_name, amount, period_half, is_custom))
            
        # Special handling for Fit4less (appears in both periods)
        cursor.execute('''
            INSERT OR IGNORE INTO fixed_expenses 
            (expense_name, amount, pay_period_half, is_custom, created_at)
            VALUES ('Fit4less', 14.50, 2, 0, CURRENT_TIMESTAMP)
        ''')
        
        # 7. Verify tables were created
        print("\nVerifying table creation...")
        
        # Check savings_config
        cursor.execute("SELECT COUNT(*) FROM savings_config")
        config_count = cursor.fetchone()[0]
        print(f"  - savings_config: {config_count} record(s)")
        
        # Check savings_calculations
        cursor.execute("SELECT COUNT(*) FROM savings_calculations")
        calc_count = cursor.fetchone()[0]
        print(f"  - savings_calculations: {calc_count} record(s)")
        
        # Check fixed_expenses
        cursor.execute("SELECT COUNT(*) FROM fixed_expenses")
        expense_count = cursor.fetchone()[0]
        print(f"  - fixed_expenses: {expense_count} record(s)")
        
        # Show default expenses (now that we know is_custom column exists)
        try:
            cursor.execute('''
                SELECT expense_name, amount, pay_period_half, is_custom 
                FROM fixed_expenses 
                ORDER BY pay_period_half, expense_name
            ''')
            expenses = cursor.fetchall()
            if expenses:
                print(f"\nFixed expenses in database:")
                print(f"  1st Half:")
                for expense in expenses:
                    if expense[2] == 1:  # pay_period_half == 1
                        custom_type = "Custom" if expense[3] else "Default"
                        print(f"    - {expense[0]}: ${expense[1]:.2f} ({custom_type})")
                print(f"  2nd Half:")
                for expense in expenses:
                    if expense[2] == 2:  # pay_period_half == 2
                        custom_type = "Custom" if expense[3] else "Default"
                        print(f"    - {expense[0]}: ${expense[1]:.2f} ({custom_type})")
        except Exception as e:
            print(f"Note: Could not display expense details: {e}")
            
        # Show current configuration
        cursor.execute("SELECT * FROM savings_config ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        if config:
            print(f"\nDefault configuration:")
            print(f"  - Savings: {config[1]}%")
            print(f"  - Investorline: {config[2]}%")
            print(f"  - USD: {config[3]}%")
            print(f"  - Biweekly Income: ${config[4]}")
            print(f"  - Pay Period Half: {config[5]}")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ SUCCESS: All savings tables created successfully!")
        print(f"Database: {os.path.abspath(db_path)}")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to create tables: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()
    
    return True

def check_existing_tables():
    """Check which tables already exist"""
    
    db_path = 'finance_tracker.db'
    
    if not os.path.exists(db_path):
        print("Database file does not exist yet.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print("Existing tables in database:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} record(s)")
            
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        conn.close()

def main():
    print("SAVINGS DATABASE SETUP")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check existing tables first
    print("Checking existing database structure...")
    check_existing_tables()
    print()
    
    # Setup savings tables
    success = setup_savings_tables()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update your app.py with the new savings routes")
        print("2. Update your savings.html template")
        print("3. Restart your Flask app")
        print("4. Test the savings functionality")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")

if __name__ == '__main__':
    main()