#!/usr/bin/env python3
"""
Script to create and populate condo tables with data.
This script recreates the condo_config and condo_monthly_tracking tables
and populates them with the specified data.
"""

import sqlite3
from datetime import datetime

def setup_condo_tables(db_path='finance_tracker.db'):
    """Create and populate condo tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create condo_config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS condo_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mortgage DECIMAL(10,2) NOT NULL DEFAULT 1375.99,
                condo_fee DECIMAL(10,2) NOT NULL DEFAULT 427.35,
                property_tax DECIMAL(10,2) NOT NULL DEFAULT 406.00,
                rent_amount DECIMAL(10,2) NOT NULL DEFAULT 2000.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create condo_monthly_tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS condo_monthly_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                tenant_paid DECIMAL(10,2) DEFAULT 0,
                tenant_paid_date DATE,
                enwin_bill DECIMAL(10,2) DEFAULT 0,
                enbridge_bill DECIMAL(10,2) DEFAULT 0,
                who_paid_utilities TEXT DEFAULT 'Me',
                utilities_paid BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
            )
        ''')
        
        # Create property_tax_schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS property_tax_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                installment_number INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE NOT NULL,
                paid BOOLEAN DEFAULT 0,
                paid_date DATE,
                was_late BOOLEAN DEFAULT 0,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, installment_number)
            )
        ''')
        
        # Insert default condo configuration
        cursor.execute('''
            INSERT OR IGNORE INTO condo_config (mortgage, condo_fee, property_tax, rent_amount)
            VALUES (1375.99, 427.35, 406.00, 2000.00)
        ''')
        
        # Monthly tracking data based on your requirements
        monthly_data = [
            # (year, month, tenant_paid, enwin_bill, enbridge_bill, who_paid_utilities, utilities_paid)
            (2024, 12, 0, 45.75, 61.08, 'Me', 1),
            (2025, 1, 0, 39.01, 35.73, 'Me', 1),
            (2025, 2, 0, 31.16, 32.81, 'Me', 1),
            (2025, 3, 2000, 53.04, 31.54, 'Tenant', 1),
            (2025, 4, 2000, 44.57, 35.07, 'Tenant', 1),
            (2025, 5, 2000, 70.34, 28.01, 'Tenant', 1),
            (2025, 6, 2000, 109.91, 32.68, '', 0),
            (2025, 7, 2000, 143.73, 31.24, '', 0),
            (2025, 8, 2000, 0, 0, '', 0),
            (2025, 9, 2000, 0, 0, '', 0),
            (2025, 10, 2000, 0, 0, '', 0),
            (2025, 11, 2000, 0, 0, '', 0),
            (2025, 12, 2000, 0, 0, '', 0),
            (2026, 1, 2000, 0, 0, '', 0),
            (2026, 2, 2000, 0, 0, '', 0),
        ]
        
        # Insert monthly tracking data
        for year, month, tenant_paid, enwin, enbridge, who_paid, utilities_paid in monthly_data:
            cursor.execute('''
                INSERT OR REPLACE INTO condo_monthly_tracking 
                (year, month, tenant_paid, enwin_bill, enbridge_bill, who_paid_utilities, utilities_paid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (year, month, tenant_paid, enwin, enbridge, who_paid, utilities_paid))
        
        # Property tax schedule data based on your requirements
        property_tax_data = [
            # (year, installment_number, amount, due_date, paid, paid_date, was_late)
            (2025, 1, 409.53, '2025-02-19', 1, '2025-02-19', 0),
            (2025, 2, 412.09, '2025-03-19', 1, '2025-03-20', 1),  # was late
            (2025, 3, 407.00, '2025-04-16', 1, '2025-04-16', 0),
            (2025, 4, 407.15, '2025-07-16', 1, '2025-07-16', 0),
            (2025, 5, 406.00, '2025-09-17', 0, None, 0),  # not paid yet
            (2025, 6, 406.00, '2025-11-19', 0, None, 0),  # not paid yet
        ]
        
        # Insert property tax data
        for year, installment, amount, due_date, paid, paid_date, was_late in property_tax_data:
            cursor.execute('''
                INSERT OR REPLACE INTO property_tax_schedule 
                (year, installment_number, amount, due_date, paid, paid_date, was_late)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (year, installment, amount, due_date, paid, paid_date, was_late))
        
        conn.commit()
        
        # Verify data was inserted
        cursor.execute('SELECT COUNT(*) FROM condo_config')
        config_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM condo_monthly_tracking')
        tracking_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM property_tax_schedule')
        tax_count = cursor.fetchone()[0]
        
        print(f"✓ Condo tables created successfully!")
        print(f"✓ Configuration records: {config_count}")
        print(f"✓ Monthly tracking records: {tracking_count}")
        print(f"✓ Property tax schedule records: {tax_count}")
        
        # Show current configuration
        cursor.execute('SELECT * FROM condo_config ORDER BY id DESC LIMIT 1')
        config = cursor.fetchone()
        print(f"\nCurrent Configuration:")
        print(f"Mortgage: ${config[1]}")
        print(f"Condo Fee: ${config[2]}")
        print(f"Property Tax: ${config[3]}")
        print(f"Rent Amount: ${config[4]}")
        
        total_expenses = config[1] + config[2] + config[3]
        revenue = config[4] - total_expenses
        yearly_revenue = revenue * 12
        
        print(f"Total Expenses: ${total_expenses}")
        print(f"Monthly Revenue: ${revenue}")
        print(f"Yearly Revenue: ${yearly_revenue}")
        
    except Exception as e:
        print(f"Error setting up condo tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    setup_condo_tables()
