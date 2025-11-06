import sqlite3
from datetime import datetime

conn = sqlite3.connect('finance_tracker.db')
cursor = conn.cursor()

# Check if year column exists
cursor.execute('PRAGMA table_info(condo_config)')
columns = [col[1] for col in cursor.fetchall()]

if 'year' not in columns:
    cursor.execute('ALTER TABLE condo_config ADD COLUMN year INTEGER')
    print("✅ Added 'year' column to condo_config")
else:
    print("⚠️  'year' column already exists")

# Get all records
cursor.execute('SELECT id, year FROM condo_config ORDER BY id')
records = cursor.fetchall()
print(f"Found {len(records)} config records")

# Keep only the most recent record for year 2025
if records:
    latest_id = records[-1][0]
    # Delete all but the latest
    cursor.execute('DELETE FROM condo_config WHERE id != ?', (latest_id,))
    deleted_count = cursor.rowcount
    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} old config records, keeping the latest (id={latest_id})")

    # Update the latest to year 2025
    cursor.execute('UPDATE condo_config SET year = 2025 WHERE id = ?', (latest_id,))
    print(f"✅ Set latest config (id={latest_id}) to year 2025")

# Drop existing index if it exists
try:
    cursor.execute('DROP INDEX IF EXISTS idx_condo_config_year')
    print("✅ Dropped old index")
except:
    pass

# Create a unique index on year to ensure only one config per year
try:
    cursor.execute('CREATE UNIQUE INDEX idx_condo_config_year ON condo_config(year)')
    print("✅ Created unique index on year")
except sqlite3.OperationalError as e:
    print(f"⚠️  Index issue: {e}")

conn.commit()
conn.close()
print("\n✅ Migration completed successfully!")
