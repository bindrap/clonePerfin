import sqlite3
from datetime import datetime

conn = sqlite3.connect('finance_tracker.db')
cursor = conn.cursor()

# Check if effective_date column exists
cursor.execute('PRAGMA table_info(condo_config)')
columns = [col[1] for col in cursor.fetchall()]

if 'effective_date' not in columns:
    cursor.execute('ALTER TABLE condo_config ADD COLUMN effective_date DATE')
    print("✅ Added 'effective_date' column to condo_config")
else:
    print("⚠️  'effective_date' column already exists")

# Set effective_date for existing records (start of their year)
cursor.execute('SELECT id, year FROM condo_config WHERE effective_date IS NULL')
records = cursor.fetchall()

for record in records:
    config_id = record[0]
    year = record[1]
    # Set to January 1st of that year
    effective_date = f'{year}-01-01'
    cursor.execute('UPDATE condo_config SET effective_date = ? WHERE id = ?', (effective_date, config_id))
    print(f"✅ Set effective_date to {effective_date} for config id={config_id}")

# Drop the old unique index on year only
try:
    cursor.execute('DROP INDEX IF EXISTS idx_condo_config_year')
    print("✅ Dropped old unique index on year")
except:
    pass

# Create new unique index on year + effective_date combination
try:
    cursor.execute('CREATE UNIQUE INDEX idx_condo_config_year_date ON condo_config(year, effective_date)')
    print("✅ Created unique index on (year, effective_date)")
except sqlite3.OperationalError as e:
    if 'already exists' in str(e):
        print("⚠️  Index already exists")
    else:
        print(f"⚠️  Index creation issue: {e}")

conn.commit()
conn.close()
print("\n✅ Migration completed successfully!")
print("You can now have multiple lease terms per year with different effective dates.")
