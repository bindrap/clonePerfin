from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from datetime import datetime, timedelta, date
import sqlite3
import os
import json
import pytz
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Toronto timezone
TORONTO_TZ = pytz.timezone('America/Toronto')

def get_toronto_date():
    """Get current date in Toronto timezone"""
    return datetime.now(TORONTO_TZ).date()

@app.route('/favicon_io/<path:filename>')
def favicon_io(filename):
    return send_from_directory('favicon_io', filename)

@app.route('/img/<path:filename>')
def serve_images(filename):
    return send_from_directory('img', filename)

@app.template_filter('tojsonfilter')
def to_json_filter(value):
    def convert_row_to_dict(obj):
        if hasattr(obj, 'keys') and hasattr(obj, '__getitem__'):
            # This is a SQLite Row object
            return dict(obj)
        elif isinstance(obj, list):
            return [convert_row_to_dict(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj
    
    try:
        converted_value = convert_row_to_dict(value)
        return json.dumps(converted_value, default=str)
    except (TypeError, ValueError) as e:
        # Fallback: convert to string representation
        return json.dumps(str(value))

def get_db_connection():
    conn = sqlite3.connect('finance_tracker.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_budget_period():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = get_toronto_date()
    cursor.execute('''
        SELECT * FROM budget_periods 
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY start_date DESC LIMIT 1
    ''', (today, today))
    period = cursor.fetchone()
    
    if not period:
        start_date = today
        end_date = today + timedelta(days=13)
        cursor.execute('''
            INSERT INTO budget_periods (start_date, end_date, budget_amount, is_current)
            VALUES (?, ?, 500.00, 1)
        ''', (start_date, end_date))
        period_id = cursor.lastrowid
        conn.commit()
        cursor.execute('SELECT * FROM budget_periods WHERE id = ?', (period_id,))
        period = cursor.fetchone()
    
    conn.close()
    return period

@app.route('/')
def dashboard():
    conn = get_db_connection()
    budget_period = get_current_budget_period()
    
    today = get_toronto_date()
    end_date = budget_period['end_date']
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    days_left = (end_date - today).days + 1
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(price) as total_spent 
        FROM spending_log 
        WHERE date BETWEEN ? AND ?
    ''', (budget_period['start_date'], budget_period['end_date']))
    
    result = cursor.fetchone()
    total_spent = float(result['total_spent']) if result['total_spent'] else 0.0
    
    budget_amount = float(budget_period['budget_amount'])
    remaining_budget = budget_amount - total_spent
    daily_spend_limit = remaining_budget / max(days_left, 1)
    
    thirty_days_ago = today - timedelta(days=30)
    cursor.execute('''
        SELECT 
            SUM(gym) as gym_count,
            SUM(jiu_jitsu) as jiu_jitsu_count,
            SUM(skateboarding) as skateboarding_count,
            SUM(work) as work_count,
            SUM(coitus) as coitus_count,
            SUM(sauna) as sauna_count,
            SUM(supplements) as supplements_count,
            COUNT(*) as total_days
        FROM personal_log 
        WHERE date >= ?
    ''', (thirty_days_ago,))
    activity_stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT 
            SUM(gym) as total_gym,
            SUM(jiu_jitsu) as total_jiu_jitsu,
            SUM(skateboarding) as total_skateboarding,
            SUM(work) as total_work,
            SUM(coitus) as total_coitus,
            SUM(sauna) as total_sauna,
            SUM(supplements) as total_supplements,
            COUNT(*) as total_all_days
        FROM personal_log
    ''')
    all_time_stats = cursor.fetchone()
    
    total_days = all_time_stats['total_all_days'] if all_time_stats['total_all_days'] else 1
    activity_percentages = {
        'gym_percentage': round((all_time_stats['total_gym'] / total_days) * 100, 1) if all_time_stats['total_gym'] else 0,
        'jiu_jitsu_percentage': round((all_time_stats['total_jiu_jitsu'] / total_days) * 100, 1) if all_time_stats['total_jiu_jitsu'] else 0,
        'skateboarding_percentage': round((all_time_stats['total_skateboarding'] / total_days) * 100, 1) if all_time_stats['total_skateboarding'] else 0,
        'work_percentage': round((all_time_stats['total_work'] / total_days) * 100, 1) if all_time_stats['total_work'] else 0,
        'coitus_percentage': round((all_time_stats['total_coitus'] / total_days) * 100, 1) if all_time_stats['total_coitus'] else 0,
        'sauna_percentage': round((all_time_stats['total_sauna'] / total_days) * 100, 1) if all_time_stats['total_sauna'] else 0,
        'supplements_percentage': round((all_time_stats['total_supplements'] / total_days) * 100, 1) if all_time_stats['total_supplements'] else 0,
        'total_tracked_days': total_days
    }
    
    # Enhanced spending categorization
    cursor.execute('''
        SELECT 
            CASE 
                WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%tims%' THEN 'TIMS'
                WHEN LOWER(item) LIKE '%coffee%' AND LOWER(item) NOT LIKE '%tim%' THEN 'Coffee (Other)'
                WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' OR LOWER(item) LIKE '%petro%' THEN 'Gas'
                WHEN LOWER(item) LIKE '%dispo%' OR LOWER(item) LIKE '%cannabis%' THEN 'Dispo'
                WHEN LOWER(item) LIKE '%lcbo%' OR LOWER(item) LIKE '%alcohol%' OR LOWER(item) LIKE '%beer%' OR LOWER(item) LIKE '%wine%' THEN 'LCBO'
                WHEN LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%mcds%' THEN 'McDonalds'
                WHEN LOWER(item) LIKE '%domino%' THEN 'Dominos'
                WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%wendys%' OR LOWER(item) LIKE '%pizza%' OR LOWER(item) LIKE '%taco%' OR LOWER(item) LIKE '%burger%' OR LOWER(item) LIKE '%arbys%' OR LOWER(item) LIKE '%osmow%' OR LOWER(item) LIKE '%shawarma%' THEN 'Food'
                WHEN LOWER(item) LIKE '%gym%' OR LOWER(item) LIKE '%fit%' OR LOWER(item) LIKE '%workout%' THEN 'Fitness'
                WHEN LOWER(item) LIKE '%gift%' THEN 'Gifts'
                WHEN LOWER(item) LIKE '%wash%' OR LOWER(item) LIKE '%car%' THEN 'Car Care'
                ELSE 'Other'
            END as category,
            SUM(price) as total
        FROM spending_log 
        WHERE date >= ?
        GROUP BY category
        ORDER BY total DESC
    ''', (thirty_days_ago,))
    spending_by_category = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         budget_period=budget_period,
                         total_spent=total_spent,
                         remaining_budget=remaining_budget,
                         days_left=days_left,
                         daily_spend_limit=daily_spend_limit,
                         activity_stats=activity_stats,
                         activity_percentages=activity_percentages,
                         spending_by_category=spending_by_category,
                         today=today)

@app.route('/personal')
def personal():
    # Get date from query parameter or use today
    date_param = request.args.get('date')
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = get_toronto_date()
    else:
        selected_date = get_toronto_date()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM personal_log WHERE date = ?', (selected_date,))
    selected_data = cursor.fetchone()
    
    cursor.execute('''
        SELECT * FROM personal_log 
        ORDER BY date DESC 
        LIMIT 10
    ''')
    recent_entries = cursor.fetchall()
    
    conn.close()
    
    return render_template('personal.html', 
                         today_data=selected_data, 
                         recent_entries=recent_entries,
                         today=selected_date)

@app.route('/personal/save', methods=['POST'])
def save_personal():
    date_str = request.form.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    gym = 1 if request.form.get('gym') == 'on' else 0
    jiu_jitsu = 1 if request.form.get('jiu_jitsu') == 'on' else 0
    skateboarding = 1 if request.form.get('skateboarding') == 'on' else 0
    work = 1 if request.form.get('work') == 'on' else 0
    coitus = 1 if request.form.get('coitus') == 'on' else 0
    sauna = 1 if request.form.get('sauna') == 'on' else 0
    supplements = 1 if request.form.get('supplements') == 'on' else 0
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO personal_log 
        (date, gym, jiu_jitsu, skateboarding, work, coitus, sauna, supplements, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (date_obj, gym, jiu_jitsu, skateboarding, work, coitus, sauna, supplements, notes))
    
    conn.commit()
    conn.close()
    
    flash('Personal data saved successfully!', 'success')
    return redirect(url_for('personal', date=date_str))

@app.route('/spending')
def spending():
    toronto_today = get_toronto_date()
    budget_period = get_current_budget_period()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM spending_log 
        WHERE date = ? 
        ORDER BY created_at DESC
    ''', (toronto_today,))
    today_spending = cursor.fetchall()
    
    cursor.execute('''
        SELECT * FROM spending_log 
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC, created_at DESC
    ''', (budget_period['start_date'], budget_period['end_date']))
    period_spending = cursor.fetchall()
    
    cursor.execute('''
        SELECT SUM(price) as total 
        FROM spending_log 
        WHERE date = ?
    ''', (toronto_today,))
    today_total = cursor.fetchone()['total'] or 0
    
    cursor.execute('''
        SELECT SUM(price) as total 
        FROM spending_log 
        WHERE date BETWEEN ? AND ?
    ''', (budget_period['start_date'], budget_period['end_date']))
    period_total = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    return render_template('spending.html', 
                         budget_period=budget_period,
                         today_spending=today_spending,
                         period_spending=period_spending,
                         today_total=today_total,
                         period_total=period_total,
                         today=toronto_today)

@app.route('/spending/add', methods=['POST'])
def add_spending():
    date_str = request.form.get('date')
    item = request.form.get('item')
    price = float(request.form.get('price'))
    
    if not item or price <= 0:
        flash('Please provide valid item and price', 'error')
        return redirect(url_for('spending'))
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO spending_log (date, item, price)
        VALUES (?, ?, ?)
    ''', (date_obj, item, price))
    
    conn.commit()
    conn.close()
    
    flash(f'Added {item} for ${price:.2f}', 'success')
    return redirect(url_for('spending'))

@app.route('/spending/delete/<int:entry_id>', methods=['POST'])
def delete_spending(entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM spending_log WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
    
    flash('Spending entry deleted', 'success')
    return redirect(url_for('spending'))

# NEW ROUTES FOR ANALYTICS
@app.route('/analytics')
def analytics():
    """Advanced analytics page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get spending by time periods
    today = get_toronto_date()
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    # Weekly spending
    cursor.execute('''
        SELECT SUM(price) as total FROM spending_log 
        WHERE date >= ?
    ''', (seven_days_ago,))
    weekly_total = cursor.fetchone()['total'] or 0
    
    # Monthly spending
    cursor.execute('''
        SELECT SUM(price) as total FROM spending_log 
        WHERE date >= ?
    ''', (thirty_days_ago,))
    monthly_total = cursor.fetchone()['total'] or 0
    
    # Quarterly spending
    cursor.execute('''
        SELECT SUM(price) as total FROM spending_log 
        WHERE date >= ?
    ''', (ninety_days_ago,))
    quarterly_total = cursor.fetchone()['total'] or 0
    
    # Enhanced detailed spending by category using CTE for better categorization
    cursor.execute('''
        WITH categorized AS (
            SELECT 
                item,
                CASE 
                    WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%tims%' THEN 'TIMS'
                    WHEN LOWER(item) LIKE '%coffee%' AND LOWER(item) NOT LIKE '%tim%' THEN 'Coffee (Other)'
                    WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' OR LOWER(item) LIKE '%petro%' THEN 'Gas'
                    WHEN LOWER(item) LIKE '%dispo%' OR LOWER(item) LIKE '%cannabis%' THEN 'Dispo'
                    WHEN LOWER(item) LIKE '%lcbo%' OR LOWER(item) LIKE '%alcohol%' OR LOWER(item) LIKE '%beer%' OR LOWER(item) LIKE '%wine%' THEN 'LCBO'
                    WHEN LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%mcds%' THEN 'McDonalds'
                    WHEN LOWER(item) LIKE '%domino%' THEN 'Dominos'
                    WHEN LOWER(item) LIKE '%wendys%' THEN 'Wendys'
                    WHEN LOWER(item) LIKE '%osmow%' OR LOWER(item) LIKE '%shawarma%' THEN 'Osmows/Shawarma'
                    WHEN LOWER(item) LIKE '%arbys%' THEN 'Arbys'
                    WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%pizza%' OR LOWER(item) LIKE '%taco%' OR LOWER(item) LIKE '%burger%' THEN 'Food (Other)'
                    WHEN LOWER(item) LIKE '%gym%' OR LOWER(item) LIKE '%fit%' OR LOWER(item) LIKE '%workout%' THEN 'Fitness'
                    WHEN LOWER(item) LIKE '%gift%' THEN 'Gifts'
                    WHEN LOWER(item) LIKE '%wash%' OR LOWER(item) LIKE '%car%' THEN 'Car Care'
                    ELSE 'Other'
                END as category,
                price
            FROM spending_log 
            WHERE date >= ?
        )
        SELECT category, SUM(price) as total, COUNT(*) as count
        FROM categorized
        GROUP BY category
        ORDER BY total DESC
    ''', (thirty_days_ago.strftime('%Y-%m-%d'),))
    detailed_categories = cursor.fetchall()
    
    # Top spending items from spending_log
    cursor.execute('''
        SELECT item as item_name, SUM(price) as total, COUNT(*) as frequency
        FROM spending_log 
        WHERE date >= ?
        GROUP BY item
        ORDER BY total DESC
        LIMIT 10
    ''', (thirty_days_ago,))
    top_items = cursor.fetchall()
    
    # Spending trends by week
    cursor.execute('''
        SELECT 
            strftime('%Y-%W', date) as week,
            SUM(price) as total
        FROM spending_log 
        WHERE date >= ?
        GROUP BY strftime('%Y-%W', date)
        ORDER BY week
    ''', (ninety_days_ago,))
    weekly_trends = cursor.fetchall()
    
    conn.close()
    
    return render_template('analytics.html',
                         weekly_total=weekly_total,
                         monthly_total=monthly_total,
                         quarterly_total=quarterly_total,
                         detailed_categories=detailed_categories,
                         top_items=top_items,
                         weekly_trends=weekly_trends)

# NEW ROUTES FOR PORTFOLIO
@app.route('/portfolio')
def portfolio():
    """Portfolio tracking page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get latest portfolio data from portfolio_log
    cursor.execute('''
        SELECT 
            date,
            total_portfolio_value as total_market_value,
            nasdaq_value,
            btcc_value,
            zsp_value,
            difference
        FROM portfolio_log 
        ORDER BY date DESC 
        LIMIT 1
    ''')
    latest_data = cursor.fetchone()
    
    # Calculate total invested from ETF holdings
    cursor.execute('''
        SELECT SUM(purchase_value) as total_invested FROM etf_holdings
    ''')
    invested_result = cursor.fetchone()
    total_invested = float(invested_result['total_invested']) if invested_result['total_invested'] else 0
    
    # Create snapshot object with calculated values
    latest_snapshot = None
    if latest_data and latest_data['total_market_value']:
        current_value = float(latest_data['total_market_value'])
        profit_loss = current_value - total_invested
        profit_loss_percentage = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        latest_snapshot = {
            'date': latest_data['date'],
            'total_market_value': current_value,
            'total_invested': total_invested,
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'nasdaq_value': latest_data['nasdaq_value'],
            'btcc_value': latest_data['btcc_value'],
            'zsp_value': latest_data['zsp_value']
        }
    
    # Get recent portfolio updates from portfolio_log
    cursor.execute('''
        SELECT 
            date,
            total_portfolio_value,
            nasdaq_value,
            btcc_value,
            zsp_value,
            difference,
            'update' as entry_type
        FROM portfolio_log 
        WHERE total_portfolio_value > 0
        ORDER BY date DESC 
        LIMIT 10
    ''')
    recent_entries = cursor.fetchall()
    
    # Calculate portfolio summary from ETF holdings
    cursor.execute('''
        SELECT 
            SUM(purchase_value) as total_invested,
            COUNT(*) as etf_count
        FROM etf_holdings
    ''')
    portfolio_summary = cursor.fetchone()
    
    # Get portfolio performance over time from portfolio_log
    cursor.execute('''
        SELECT 
            date, 
            total_portfolio_value as total_market_value,
            CASE 
                WHEN total_portfolio_value > 0 THEN 
                    ((total_portfolio_value - ?) / ? * 100)
                ELSE 0 
            END as profit_loss_percentage
        FROM portfolio_log 
        WHERE total_portfolio_value > 0
        ORDER BY date DESC 
        LIMIT 30
    ''', (total_invested, total_invested if total_invested > 0 else 1))
    performance_history = cursor.fetchall()
    
    conn.close()
    
    return render_template('portfolio.html',
                         latest_snapshot=latest_snapshot,
                         recent_entries=recent_entries,
                         portfolio_summary=portfolio_summary,
                         performance_history=performance_history)

@app.route('/portfolio/update', methods=['POST'])
def update_portfolio():
    """Update current portfolio market value"""
    nasdaq_value = float(request.form.get('nasdaq_value', 0))
    btcc_value = float(request.form.get('btcc_value', 0))
    zsp_value = float(request.form.get('zsp_value', 0))
    
    # Calculate total portfolio value
    current_value = nasdaq_value + btcc_value + zsp_value
    
    if current_value <= 0:
        flash('Please provide valid ETF values', 'error')
        return redirect(url_for('portfolio'))
    
    today = get_toronto_date()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total invested amount from ETF holdings
    cursor.execute('SELECT SUM(purchase_value) as total_invested FROM etf_holdings')
    result = cursor.fetchone()
    total_invested = float(result['total_invested']) if result['total_invested'] else 0
    
    # Calculate difference from previous day
    cursor.execute('''
        SELECT total_portfolio_value FROM portfolio_log 
        WHERE total_portfolio_value > 0 
        ORDER BY date DESC LIMIT 1
    ''')
    prev_result = cursor.fetchone()
    prev_value = float(prev_result['total_portfolio_value']) if prev_result else current_value
    difference = current_value - prev_value
    
    # Insert or update today's portfolio log
    cursor.execute('''
        INSERT OR REPLACE INTO portfolio_log 
        (date, total_portfolio_value, nasdaq_value, btcc_value, zsp_value, trade_cash, difference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (today, current_value, nasdaq_value, btcc_value, zsp_value, 0, difference))
    
    conn.commit()
    conn.close()
    
    profit_loss = current_value - total_invested
    flash(f'Portfolio updated: ${current_value:.2f} (P/L: ${profit_loss:.2f})', 'success')
    return redirect(url_for('portfolio'))

@app.route('/portfolio/update_etf', methods=['POST'])
def update_etf_holdings():
    """Update ETF purchase values"""
    nas_value = float(request.form.get('nas_value', 0))
    btcc_value = float(request.form.get('btcc_value', 0))
    zsp_value = float(request.form.get('zsp_value', 0))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing holdings and insert new ones
    cursor.execute('DELETE FROM etf_holdings')
    
    if nas_value > 0:
        cursor.execute('INSERT INTO etf_holdings (etf_symbol, purchase_value) VALUES (?, ?)', ('NAS', nas_value))
    if btcc_value > 0:
        cursor.execute('INSERT INTO etf_holdings (etf_symbol, purchase_value) VALUES (?, ?)', ('BTCC', btcc_value))
    if zsp_value > 0:
        cursor.execute('INSERT INTO etf_holdings (etf_symbol, purchase_value) VALUES (?, ?)', ('ZSP', zsp_value))
    
    conn.commit()
    conn.close()
    
    flash('ETF holdings updated successfully!', 'success')
    return redirect(url_for('portfolio'))

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data - FIXED to show actual last 30 days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = get_toronto_date()
    thirty_days_ago = today - timedelta(days=29)
    
    # Daily spending over last 30 days
    cursor.execute('''
        SELECT date, SUM(price) as total
        FROM spending_log 
        WHERE date >= ? AND date <= ?
        GROUP BY date
        ORDER BY date
    ''', (thirty_days_ago, today))
    daily_spending = [dict(row) for row in cursor.fetchall()]
    
    # Fill in missing days with 0 spending
    complete_spending = []
    current_date = thirty_days_ago
    spending_dict = {row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], date) else str(row['date']): row['total'] for row in daily_spending}
    
    while current_date <= today:
        date_str = current_date.strftime('%Y-%m-%d')
        complete_spending.append({
            'date': date_str,
            'total': spending_dict.get(date_str, 0)
        })
        current_date += timedelta(days=1)
    
    # Activity frequency over last 30 days
    cursor.execute('''
        SELECT date, gym, jiu_jitsu, skateboarding, work, coitus, sauna, supplements
        FROM personal_log 
        WHERE date >= ? AND date <= ?
        ORDER BY date
    ''', (thirty_days_ago, today))
    activities = cursor.fetchall()
    
    # Convert date objects to strings
    daily_activities = []
    for row in activities:
        activity_dict = dict(row)
        activity_dict['date'] = activity_dict['date'].strftime('%Y-%m-%d') if activity_dict['date'] else ''
        daily_activities.append(activity_dict)
    
    conn.close()
    
    return jsonify({
        'daily_spending': complete_spending,
        'daily_activities': daily_activities
    })

@app.route('/api/analytics/detailed')
def api_detailed_analytics():
    """API endpoint for detailed analytics charts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced category spending over time using CTE for better categorization
    cursor.execute('''
        WITH categorized AS (
            SELECT 
                item,
                CASE 
                    WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%tims%' THEN 'TIMS'
                    WHEN LOWER(item) LIKE '%coffee%' AND LOWER(item) NOT LIKE '%tim%' THEN 'Coffee (Other)'
                    WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' OR LOWER(item) LIKE '%petro%' THEN 'Gas'
                    WHEN LOWER(item) LIKE '%dispo%' OR LOWER(item) LIKE '%cannabis%' THEN 'Dispo'
                    WHEN LOWER(item) LIKE '%lcbo%' OR LOWER(item) LIKE '%alcohol%' OR LOWER(item) LIKE '%beer%' OR LOWER(item) LIKE '%wine%' THEN 'LCBO'
                    WHEN LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%mcds%' THEN 'McDonalds'
                    WHEN LOWER(item) LIKE '%domino%' THEN 'Dominos'
                    WHEN LOWER(item) LIKE '%wendys%' THEN 'Wendys'
                    WHEN LOWER(item) LIKE '%osmow%' OR LOWER(item) LIKE '%shawarma%' THEN 'Osmows'
                    WHEN LOWER(item) LIKE '%arbys%' THEN 'Arbys'
                    WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%pizza%' OR LOWER(item) LIKE '%taco%' OR LOWER(item) LIKE '%burger%' THEN 'Food (Other)'
                    WHEN LOWER(item) LIKE '%gym%' OR LOWER(item) LIKE '%fit%' OR LOWER(item) LIKE '%workout%' THEN 'Fitness'
                    WHEN LOWER(item) LIKE '%gift%' THEN 'Gifts'
                    WHEN LOWER(item) LIKE '%wash%' OR LOWER(item) LIKE '%car%' THEN 'Car Care'
                    ELSE 'Other'
                END as category,
                strftime('%Y-%m', date) as month,
                price
            FROM spending_log 
            WHERE date >= date('now', '-6 months')
        )
        SELECT category, month, SUM(price) as total
        FROM categorized
        GROUP BY category, month
        ORDER BY month, category
    ''')
    category_trends = [dict(row) for row in cursor.fetchall()]
    
    # Overall daily average calculation - total spent divided by total days tracked
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT date) as total_days,
            SUM(price) as total_spent,
            ROUND(SUM(price) * 1.0 / COUNT(DISTINCT date), 2) as overall_daily_avg
        FROM spending_log
    ''')
    overall_stats = cursor.fetchone()
    
    # Also get daily averages for the last few months for trend visualization
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month,
            COUNT(DISTINCT date) as days_in_month,
            SUM(price) as monthly_total,
            ROUND(SUM(price) * 1.0 / COUNT(DISTINCT date), 2) as avg_daily_for_month
        FROM spending_log
        WHERE date >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    ''')
    monthly_daily_averages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'category_trends': category_trends,
        'monthly_daily_averages': monthly_daily_averages,
        'overall_stats': dict(overall_stats)
    })

@app.route('/api/analytics/activities')
def api_activity_analytics():
    """API endpoint for detailed activity analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Overall activity statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_days,
            SUM(gym) as gym_days,
            SUM(jiu_jitsu) as jj_days,
            SUM(skateboarding) as skate_days,
            SUM(work) as work_days,
            SUM(sauna) as sauna_days,
            SUM(supplements) as supp_days,
            SUM(coitus) as coitus_days
        FROM personal_log
    ''')
    stats = cursor.fetchone()
    
    # Calculate percentages
    total_days = stats['total_days'] if stats['total_days'] > 0 else 1
    activity_stats = {
        'total_days': stats['total_days'],
        'gym_days': stats['gym_days'],
        'jj_days': stats['jj_days'],
        'skate_days': stats['skate_days'],
        'work_days': stats['work_days'],
        'sauna_days': stats['sauna_days'],
        'supp_days': stats['supp_days'],
        'coitus_days': stats['coitus_days'],
        'gym_percentage': (stats['gym_days'] / total_days) * 100,
        'jj_percentage': (stats['jj_days'] / total_days) * 100,
        'work_percentage': (stats['work_days'] / total_days) * 100,
    }
    
    # Weekly activity patterns (last 12 weeks)
    cursor.execute('''
        SELECT 
            strftime('%Y-%W', date) as week,
            SUM(gym) as gym,
            SUM(jiu_jitsu) as jiu_jitsu,
            SUM(work) as work,
            SUM(skateboarding) as skateboarding
        FROM personal_log 
        WHERE date >= date('now', '-12 weeks')
        GROUP BY strftime('%Y-%W', date)
        ORDER BY week DESC
        LIMIT 12
    ''')
    weekly_patterns = [dict(row) for row in cursor.fetchall()]
    
    # Calculate current streaks
    cursor.execute('''
        SELECT date, gym, jiu_jitsu, work
        FROM personal_log 
        ORDER BY date DESC 
        LIMIT 30
    ''')
    recent_data = cursor.fetchall()
    
    # Calculate streaks
    gym_streak = 0
    jj_streak = 0
    work_streak = 0
    
    for day in recent_data:
        if day['gym']:
            gym_streak += 1
        else:
            break
    
    for day in recent_data:
        if day['jiu_jitsu']:
            jj_streak += 1
        else:
            break
            
    for day in recent_data:
        if day['work']:
            work_streak += 1
        else:
            break
    
    streaks = {
        'gym_current': gym_streak,
        'jj_current': jj_streak,
        'work_current': work_streak
    }
    
    # Generate insights
    insights = []
    if activity_stats['gym_percentage'] > 50:
        insights.append(f"You hit the gym {activity_stats['gym_percentage']:.0f}% of days - great consistency!")
    if activity_stats['jj_percentage'] > 40:
        insights.append(f"Strong jiu jitsu practice at {activity_stats['jj_percentage']:.0f}% of days")
    if gym_streak > 3:
        insights.append(f"You're on a {gym_streak}-day gym streak! 💪")
    if jj_streak > 2:
        insights.append(f"Current jiu jitsu streak: {jj_streak} days 🥋")
    if activity_stats['work_percentage'] > 60:
        insights.append(f"High work consistency at {activity_stats['work_percentage']:.0f}% of tracked days")
    
    if not insights:
        insights.append("Keep building those healthy habits!")
    
    conn.close()
    
    return jsonify({
        'activity_stats': activity_stats,
        'weekly_patterns': weekly_patterns,
        'streaks': streaks,
        'insights': insights
    })

@app.route('/api/portfolio')
def api_portfolio():
    """API endpoint for portfolio performance data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total invested from ETF holdings
    cursor.execute('SELECT SUM(purchase_value) as total_invested FROM etf_holdings')
    invested_result = cursor.fetchone()
    total_invested = float(invested_result['total_invested']) if invested_result['total_invested'] else 0
    
    # Portfolio value over time from portfolio_log
    cursor.execute('''
        SELECT 
            date, 
            total_portfolio_value as total_market_value,
            ? as total_invested,
            CASE 
                WHEN total_portfolio_value > 0 THEN 
                    ((total_portfolio_value - ?) / ? * 100)
                ELSE 0 
            END as profit_loss_percentage
        FROM portfolio_log 
        WHERE date >= date('now', '-6 months') AND total_portfolio_value > 0
        ORDER BY date
    ''', (total_invested, total_invested, total_invested if total_invested > 0 else 1))
    portfolio_performance = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'portfolio_performance': portfolio_performance
    })

@app.route('/api/portfolio/update_daily', methods=['POST'])
def update_portfolio_daily():
    """API endpoint for daily portfolio updates - can be called by external scripts"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    nasdaq_value = data.get('nasdaq_value', 0)
    btcc_value = data.get('btcc_value', 0)
    zsp_value = data.get('zsp_value', 0)
    
    if not all([nasdaq_value, btcc_value, zsp_value]):
        return jsonify({'error': 'Missing ETF values'}), 400
    
    current_value = float(nasdaq_value) + float(btcc_value) + float(zsp_value)
    today = get_toronto_date()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total invested amount from ETF holdings
    cursor.execute('SELECT SUM(purchase_value) as total_invested FROM etf_holdings')
    result = cursor.fetchone()
    total_invested = float(result['total_invested']) if result['total_invested'] else 0
    
    # Calculate difference from previous day
    cursor.execute('''
        SELECT total_portfolio_value FROM portfolio_log 
        WHERE total_portfolio_value > 0 
        ORDER BY date DESC LIMIT 1
    ''')
    prev_result = cursor.fetchone()
    prev_value = float(prev_result['total_portfolio_value']) if prev_result else current_value
    difference = current_value - prev_value
    
    # Insert or update today's portfolio log
    cursor.execute('''
        INSERT OR REPLACE INTO portfolio_log 
        (date, total_portfolio_value, nasdaq_value, btcc_value, zsp_value, trade_cash, difference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (today, current_value, nasdaq_value, btcc_value, zsp_value, 0, difference))
    
    conn.commit()
    conn.close()
    
    profit_loss = current_value - total_invested
    profit_loss_percentage = (profit_loss / total_invested * 100) if total_invested > 0 else 0
    
    return jsonify({
        'success': True,
        'date': today.strftime('%Y-%m-%d'),
        'total_portfolio_value': current_value,
        'profit_loss': profit_loss,
        'profit_loss_percentage': profit_loss_percentage,
        'difference_from_yesterday': difference
    })

# Auto-fetch ETF prices endpoint (for future automation)
@app.route('/api/portfolio/auto_update', methods=['POST'])
def auto_update_portfolio():
    """Auto-update portfolio with fetched ETF prices (placeholder for future API integration)"""
    # This is where you would integrate with a financial API like Yahoo Finance, Alpha Vantage, etc.
    # For now, this returns an error indicating manual update is required
    
    return jsonify({
        'error': 'Auto-update not yet implemented',
        'message': 'Please update portfolio values manually for now',
        'suggestion': 'Future versions will integrate with financial APIs for automatic updates'
    }), 501

if __name__ == '__main__':
    # Add pytz to requirements
    app.run(debug=True, host='0.0.0.0', port=5001)