from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from datetime import datetime, timedelta, date
import sqlite3
import os
import json
import pytz
from functools import wraps
import subprocess
import threading

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
    # Don't count the end day as that is the day the user gets paid
    days_left = (end_date - today).days
    
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
    
    # Get current budget info
    budget_period = get_current_budget_period()
    
    conn.close()
    
    return jsonify({
        'daily_spending': complete_spending,
        'daily_activities': daily_activities,
        'current_budget': {
            'amount': float(budget_period['budget_amount']),
            'start_date': budget_period['start_date'],
            'end_date': budget_period['end_date']
        }
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
    
    # Weekly activity patterns - now including coitus and supplements
    today = get_toronto_date()
    twelve_weeks_ago = today - timedelta(weeks=12)
    
    cursor.execute('''
        SELECT 
            date,
            gym,
            jiu_jitsu,
            work,
            skateboarding,
            coitus,
            supplements
        FROM personal_log 
        WHERE date >= ?
        ORDER BY date
    ''', (twelve_weeks_ago,))
    
    daily_results = cursor.fetchall()
    
    # Group by week manually to ensure proper data structure
    weekly_data = {}
    
    for row in daily_results:
        row_date = row['date']
        if isinstance(row_date, str):
            row_date = datetime.strptime(row_date, '%Y-%m-%d').date()
        
        # Calculate week number (ISO week)
        year, week_num, _ = row_date.isocalendar()
        week_key = f"{year}-W{week_num:02d}"
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {
                'week_key': week_key,
                'week_num': week_num,
                'year': year,
                'gym': 0,
                'jiu_jitsu': 0,
                'work': 0,
                'skateboarding': 0,
                'coitus': 0,
                'supplements': 0,
                'start_date': row_date
            }
        
        # Sum up activities for the week
        weekly_data[week_key]['gym'] += row['gym'] or 0
        weekly_data[week_key]['jiu_jitsu'] += row['jiu_jitsu'] or 0
        weekly_data[week_key]['work'] += row['work'] or 0
        weekly_data[week_key]['skateboarding'] += row['skateboarding'] or 0
        weekly_data[week_key]['coitus'] += row['coitus'] or 0
        weekly_data[week_key]['supplements'] += row['supplements'] or 0
    
    # Convert to list and sort by date
    weekly_patterns = list(weekly_data.values())
    weekly_patterns.sort(key=lambda x: x['start_date'])
    
    # Format for chart display and limit to last 12 weeks
    weekly_patterns = weekly_patterns[-12:]
    
    # Create readable week labels
    formatted_patterns = []
    for week_data in weekly_patterns:
        # Create a more readable week label
        start_date = week_data['start_date']
        month_name = start_date.strftime('%b')
        week_label = f"W{week_data['week_num']} ({month_name})"
        
        formatted_patterns.append({
            'week': week_label,
            'gym': week_data['gym'],
            'jiu_jitsu': week_data['jiu_jitsu'],
            'work': week_data['work'],
            'skateboarding': week_data['skateboarding'],
            'coitus': week_data['coitus'],
            'supplements': week_data['supplements']
        })
    
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
        insights.append(f"You're on a {gym_streak}-day gym streak!")
    if jj_streak > 2:
        insights.append(f"Current jiu jitsu streak: {jj_streak} days")
    if activity_stats['work_percentage'] > 60:
        insights.append(f"High work consistency at {activity_stats['work_percentage']:.0f}% of tracked days")
    
    if not insights:
        insights.append("Keep building those healthy habits!")
    
    conn.close()
    
    return jsonify({
        'activity_stats': activity_stats,
        'weekly_patterns': formatted_patterns,
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

# Add these new routes to your app.py file

@app.route('/budget/update', methods=['POST'])
def update_budget():
    """Update budget amount for current budget period"""
    new_budget = request.form.get('budget_amount')
    
    try:
        new_budget_float = float(new_budget)
        if new_budget_float <= 0:
            flash('Budget amount must be greater than 0', 'error')
            return redirect(url_for('dashboard'))
    except (TypeError, ValueError):
        flash('Please provide a valid budget amount', 'error')
        return redirect(url_for('dashboard'))
    
    # Get current budget period
    budget_period = get_current_budget_period()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update the current budget period
    cursor.execute('''
        UPDATE budget_periods 
        SET budget_amount = ?
        WHERE id = ?
    ''', (new_budget_float, budget_period['id']))
    
    conn.commit()
    conn.close()
    
    flash(f'Budget updated to ${new_budget_float:.2f} for current period', 'success')
    return redirect(url_for('dashboard'))

@app.route('/portfolio/auto_update_trigger', methods=['POST'])
def trigger_auto_update():
    """Trigger the auto portfolio update script"""
    try:
        # Path to your auto update script
        script_path = os.path.join(os.path.dirname(__file__), 'auto_portfolio_update.py')
        
        if not os.path.exists(script_path):
            return jsonify({
                'error': 'Auto update script not found',
                'message': 'Please ensure auto_portfolio_update.py is in the same directory as app.py'
            }), 404
        
        # Run the script in the background
        def run_update():
            try:
                result = subprocess.run([
                    'python3', script_path
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print("Portfolio auto-update completed successfully")
                    print(f"Output: {result.stdout}")
                else:
                    print(f"Portfolio auto-update failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("Portfolio auto-update timed out after 60 seconds")
            except Exception as e:
                print(f"Error running portfolio auto-update: {e}")
        
        # Start the update in a background thread
        update_thread = threading.Thread(target=run_update)
        update_thread.daemon = True
        update_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio auto-update started in background'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to trigger auto-update',
            'message': str(e)
        }), 500

@app.route('/portfolio/last_update_status')
def get_last_update_status():
    """Get the status of the last portfolio update"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the most recent portfolio entry
    cursor.execute('''
        SELECT date, total_portfolio_value, difference, 
               datetime(date || ' 23:59:59') as last_update
        FROM portfolio_log 
        ORDER BY date DESC 
        LIMIT 1
    ''')
    latest = cursor.fetchone()
    
    conn.close()
    
    if latest:
        return jsonify({
            'last_update_date': latest['date'],
            'last_portfolio_value': latest['total_portfolio_value'],
            'last_change': latest['difference'],
            'needs_update': latest['date'] != get_toronto_date().strftime('%Y-%m-%d')
        })
    else:
        return jsonify({
            'last_update_date': None,
            'needs_update': True
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

# Add these routes to your app.py file

@app.route('/savings/update_expense/<int:expense_id>', methods=['POST'])
def update_fixed_expense(expense_id):
    """Update an existing fixed expense"""
    try:
        new_amount = float(request.form.get('amount', 0))
        
        if new_amount <= 0:
            flash('Please enter a valid amount greater than 0', 'error')
            return redirect(url_for('savings'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get expense details
        cursor.execute('SELECT expense_name FROM fixed_expenses WHERE id = ?', (expense_id,))
        expense = cursor.fetchone()
        
        if not expense:
            flash('Expense not found', 'error')
            conn.close()
            return redirect(url_for('savings'))
        
        # Update expense
        cursor.execute('''
            UPDATE fixed_expenses 
            SET amount = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_amount, expense_id))
        
        conn.commit()
        conn.close()
        
        flash(f'Updated "{expense["expense_name"]}" to ${new_amount:.2f}', 'success')
        return redirect(url_for('savings'))
        
    except ValueError:
        flash('Please enter a valid numeric amount', 'error')
        return redirect(url_for('savings'))
    except Exception as e:
        flash(f'Error updating expense: {str(e)}', 'error')
        return redirect(url_for('savings'))

@app.route('/savings/delete_expense/<int:expense_id>', methods=['POST'])
def delete_fixed_expense(expense_id):
    """Delete a fixed expense"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get expense details before deleting
        cursor.execute('SELECT expense_name FROM fixed_expenses WHERE id = ?', (expense_id,))
        expense = cursor.fetchone()
        
        if not expense:
            flash('Expense not found', 'error')
            conn.close()
            return redirect(url_for('savings'))
        
        # Delete expense
        cursor.execute('DELETE FROM fixed_expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        
        flash(f'Deleted expense "{expense["expense_name"]}"', 'success')
        return redirect(url_for('savings'))
        
    except Exception as e:
        flash(f'Error deleting expense: {str(e)}', 'error')
        return redirect(url_for('savings'))

@app.route('/savings')
def savings():
    """Savings allocation page with expense management"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current savings configuration or create default
    cursor.execute('SELECT * FROM savings_config ORDER BY id DESC LIMIT 1')
    config = cursor.fetchone()
    
    if not config:
        # Create default configuration
        cursor.execute('''
            INSERT INTO savings_config 
            (savings_percentage, investorline_percentage, usd_percentage, 
             biweekly_income, pay_period_half, created_at)
            VALUES (40, 35, 25, 2000, 1, CURRENT_TIMESTAMP)
        ''')
        conn.commit()
        cursor.execute('SELECT * FROM savings_config ORDER BY id DESC LIMIT 1')
        config = cursor.fetchone()
    
    # Get CURRENT BUDGET PERIOD instead of calendar month halves
    budget_period = get_current_budget_period()
    
    # Use budget period dates
    period_start = budget_period['start_date']
    period_end = budget_period['end_date']
    
    # Convert string dates to date objects if needed
    if isinstance(period_start, str):
        period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
    if isinstance(period_end, str):
        period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
    
    today = get_toronto_date()
    
    # Determine which half we're in based on budget period progress
    total_days = (period_end - period_start).days + 1
    days_elapsed = (today - period_start).days + 1
    
    # If we're in the first half of the budget period, use half 1, otherwise half 2
    current_half = 1 if days_elapsed <= (total_days / 2) else 2
    
    # Get spending for CURRENT BUDGET PERIOD (not calendar month)
    cursor.execute('''
        SELECT SUM(price) as total_spent
        FROM spending_log 
        WHERE date >= ? AND date <= ?
    ''', (period_start, period_end))
    
    spending_result = cursor.fetchone()
    current_spending = float(spending_result['total_spent']) if spending_result['total_spent'] else 0.0
    
    # Get ALL expenses from database (both custom and default)
    cursor.execute('''
        SELECT * FROM fixed_expenses 
        ORDER BY pay_period_half, expense_name
    ''')
    all_expenses_raw = cursor.fetchall()
    
    # Organize expenses by pay period
    first_half_expenses = {}
    second_half_expenses = {}
    
    for expense in all_expenses_raw:
        # FIXED: Access sqlite3.Row columns directly, not with .get()
        try:
            is_custom_value = expense['is_custom']
        except (KeyError, IndexError):
            is_custom_value = 1  # Default to custom if column doesn't exist
            
        expense_dict = {
            'id': expense['id'],
            'name': expense['expense_name'],
            'amount': float(expense['amount']),
            'is_custom': bool(is_custom_value)
        }
        
        if expense['pay_period_half'] == 1:
            first_half_expenses[expense['expense_name']] = expense_dict
        else:
            second_half_expenses[expense['expense_name']] = expense_dict
    
    # Create default expenses if they don't exist in database
    default_expenses_1st = {
        'Fit4less': 14.50,
        'Jiu Jitsu': 125.00,
        'Phone Bill': 45.20,
        'Car Insurance': 180.00
    }
    
    default_expenses_2nd = {
        'Fit4less': 14.50,
        'Ravi Syal': 69.88,
        'Condo Insurance': 37.74
    }
    
    # Add missing default expenses to database
    for name, amount in default_expenses_1st.items():
        if name not in first_half_expenses:
            cursor.execute('''
                INSERT INTO fixed_expenses (expense_name, amount, pay_period_half, is_custom, created_at)
                VALUES (?, ?, 1, 0, CURRENT_TIMESTAMP)
            ''', (name, amount))
            first_half_expenses[name] = {
                'id': cursor.lastrowid,
                'name': name,
                'amount': amount,
                'is_custom': False
            }
    
    for name, amount in default_expenses_2nd.items():
        if name not in second_half_expenses:
            cursor.execute('''
                INSERT INTO fixed_expenses (expense_name, amount, pay_period_half, is_custom, created_at)
                VALUES (?, ?, 2, 0, CURRENT_TIMESTAMP)
            ''', (name, amount))
            second_half_expenses[name] = {
                'id': cursor.lastrowid,
                'name': name,
                'amount': amount,
                'is_custom': False
            }
    
    conn.commit()
    
    # Get current period expenses
    if current_half == 1:
        fixed_expenses = first_half_expenses
    else:
        fixed_expenses = second_half_expenses
    
    # Calculate total
    total_fixed_expenses = sum(exp['amount'] for exp in fixed_expenses.values())
    
    # Get recent savings calculations
    cursor.execute('''
        SELECT * FROM savings_calculations 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    recent_calculations = cursor.fetchall()
    
    conn.close()
    
    return render_template('savings.html',
                         config=config,
                         current_spending=current_spending,
                         fixed_expenses=fixed_expenses,
                         total_fixed_expenses=total_fixed_expenses,
                         current_half=current_half,
                         period_start=period_start,
                         period_end=period_end,
                         budget_period=budget_period,
                         recent_calculations=recent_calculations,
                         all_first_half=first_half_expenses,
                         all_second_half=second_half_expenses,
                         today=today)

# Also fix the add_fixed_expense route to include is_custom:
@app.route('/savings/add_expense', methods=['POST'])
def add_fixed_expense():
    """Add a new fixed expense"""
    try:
        expense_name = request.form.get('expense_name', '').strip()
        amount = float(request.form.get('amount', 0))
        pay_period_half = int(request.form.get('pay_period_half', 1))
        
        if not expense_name:
            flash('Please enter a valid expense name', 'error')
            return redirect(url_for('savings'))
        
        if amount <= 0:
            flash('Please enter a valid amount greater than 0', 'error')
            return redirect(url_for('savings'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if expense already exists for this period
        cursor.execute('''
            SELECT id FROM fixed_expenses 
            WHERE expense_name = ? AND pay_period_half = ?
        ''', (expense_name, pay_period_half))
        
        if cursor.fetchone():
            flash(f'Expense "{expense_name}" already exists for this pay period', 'error')
            conn.close()
            return redirect(url_for('savings'))
        
        # Add new expense (FIXED: Include is_custom column)
        cursor.execute('''
            INSERT INTO fixed_expenses (expense_name, amount, pay_period_half, is_custom, created_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (expense_name, amount, pay_period_half))
        
        conn.commit()
        conn.close()
        
        period_text = "1st half" if pay_period_half == 1 else "2nd half"
        flash(f'Added expense "{expense_name}" (${amount:.2f}) to {period_text}', 'success')
        return redirect(url_for('savings'))
        
    except ValueError:
        flash('Please enter valid numeric values', 'error')
        return redirect(url_for('savings'))
    except Exception as e:
        flash(f'Error adding expense: {str(e)}', 'error')
        return redirect(url_for('savings'))

@app.route('/savings/calculate', methods=['POST'])
def calculate_savings():
    """Calculate savings allocation based on income and expenses"""
    try:
        # Get form data
        biweekly_income = float(request.form.get('biweekly_income', 0))
        savings_percentage = float(request.form.get('savings_percentage', 40))
        investorline_percentage = float(request.form.get('investorline_percentage', 35))
        usd_percentage = float(request.form.get('usd_percentage', 25))
        pay_period_half = int(request.form.get('pay_period_half', 1))
        
        # Validate percentages add up to 100
        total_percentage = savings_percentage + investorline_percentage + usd_percentage
        if abs(total_percentage - 100) > 0.01:
            flash(f'Allocation percentages must add up to 100% (current: {total_percentage:.1f}%)', 'error')
            return redirect(url_for('savings'))
        
        if biweekly_income <= 0:
            flash('Please enter a valid biweekly income amount', 'error')
            return redirect(url_for('savings'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get CURRENT BUDGET PERIOD spending (not calendar month)
        budget_period = get_current_budget_period()
        period_start = budget_period['start_date']
        period_end = budget_period['end_date']
        
        # Convert string dates to date objects if needed
        if isinstance(period_start, str):
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
        if isinstance(period_end, str):
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        # Get actual spending from database for current budget period
        cursor.execute('''
            SELECT SUM(price) as total_spent
            FROM spending_log 
            WHERE date >= ? AND date <= ?
        ''', (period_start, period_end))
        
        spending_result = cursor.fetchone()
        current_spending = float(spending_result['total_spent']) if spending_result['total_spent'] else 0.0
        
        # Get fixed expenses from database for the selected period
        cursor.execute('''
            SELECT SUM(amount) as total_fixed
            FROM fixed_expenses 
            WHERE pay_period_half = ?
        ''', (pay_period_half,))
        
        fixed_result = cursor.fetchone()
        total_fixed_expenses = float(fixed_result['total_fixed']) if fixed_result['total_fixed'] else 0.0
        
        # Calculate totals - THIS IS THE KEY FIX
        total_expenses = current_spending + total_fixed_expenses  # TOTAL expenses, not just fixed
        available_for_allocation = biweekly_income - total_expenses
        
        if available_for_allocation <= 0:
            flash(f'Warning: Expenses (${total_expenses:.2f}) exceed income (${biweekly_income:.2f})', 'warning')
            available_for_allocation = 0
        
        # Calculate allocations
        savings_amount = available_for_allocation * (savings_percentage / 100)
        investorline_amount = available_for_allocation * (investorline_percentage / 100)
        usd_amount = available_for_allocation * (usd_percentage / 100)
        
        # Update savings configuration
        cursor.execute('''
            INSERT INTO savings_config 
            (savings_percentage, investorline_percentage, usd_percentage, 
             biweekly_income, pay_period_half, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (savings_percentage, investorline_percentage, usd_percentage, 
              biweekly_income, pay_period_half))
        
        # Save calculation results - FIXED: Save total_expenses instead of just fixed_expenses
        cursor.execute('''
            INSERT INTO savings_calculations 
            (biweekly_income, current_spending, fixed_expenses, total_expenses,
             available_for_allocation, savings_amount, investorline_amount, 
             usd_amount, pay_period_half, period_start, period_end, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (biweekly_income, current_spending, total_fixed_expenses, total_expenses,  # FIXED: total_expenses
              available_for_allocation, savings_amount, investorline_amount,
              usd_amount, pay_period_half, period_start, period_end))
        
        conn.commit()
        conn.close()
        
        flash('Savings allocation calculated successfully!', 'success')
        return redirect(url_for('savings'))
        
    except ValueError as e:
        flash('Please enter valid numeric values', 'error')
        return redirect(url_for('savings'))
    except Exception as e:
        flash(f'Error calculating savings: {str(e)}', 'error')
        return redirect(url_for('savings'))

# You'll also need to add this new route for updating default expenses:
@app.route('/savings/update_default_expense/<int:expense_id>', methods=['POST'])
def update_default_expense(expense_id):
    """Update a default expense (same as update_fixed_expense but for clarity)"""
    return update_fixed_expense(expense_id)

@app.route('/savings/update_config', methods=['POST'])
def update_savings_config():
    """Update savings configuration"""
    try:
        savings_percentage = float(request.form.get('savings_percentage', 40))
        investorline_percentage = float(request.form.get('investorline_percentage', 35))
        usd_percentage = float(request.form.get('usd_percentage', 25))
        biweekly_income = float(request.form.get('biweekly_income', 2000))
        
        # Validate percentages
        total_percentage = savings_percentage + investorline_percentage + usd_percentage
        if abs(total_percentage - 100) > 0.01:
            flash(f'Allocation percentages must add up to 100% (current: {total_percentage:.1f}%)', 'error')
            return redirect(url_for('savings'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO savings_config 
            (savings_percentage, investorline_percentage, usd_percentage, 
             biweekly_income, pay_period_half, created_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (savings_percentage, investorline_percentage, usd_percentage, biweekly_income))
        
        conn.commit()
        conn.close()
        
        flash('Savings configuration updated successfully!', 'success')
        return redirect(url_for('savings'))
        
    except ValueError:
        flash('Please enter valid numeric values', 'error')
        return redirect(url_for('savings'))
    except Exception as e:
        flash(f'Error updating configuration: {str(e)}', 'error')
        return redirect(url_for('savings'))

@app.route('/savings/clear_calculations', methods=['POST'])
def clear_savings_calculations():
    """Clear all savings calculations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete all calculations
        cursor.execute('DELETE FROM savings_calculations')
        conn.commit()
        conn.close()
        
        flash('All savings calculations cleared successfully!', 'success')
        return redirect(url_for('savings'))
        
    except Exception as e:
        flash(f'Error clearing calculations: {str(e)}', 'error')
        return redirect(url_for('savings'))

# CONDO MANAGEMENT ROUTES
@app.route('/condo')
def condo():
    """Condo property management page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current condo configuration
    cursor.execute('SELECT * FROM condo_config ORDER BY id DESC LIMIT 1')
    config = cursor.fetchone()
    
    if not config:
        # Create default configuration
        cursor.execute('''
            INSERT INTO condo_config (mortgage, condo_fee, property_tax, rent_amount)
            VALUES (1375.99, 427.35, 406.00, 2000.00)
        ''')
        conn.commit()
        cursor.execute('SELECT * FROM condo_config ORDER BY id DESC LIMIT 1')
        config = cursor.fetchone()
    
    # Calculate total expenses
    total_expenses = float(config['mortgage']) + float(config['condo_fee']) + float(config['property_tax'])
    revenue = float(config['rent_amount']) - total_expenses
    yearly_revenue = revenue * 12
    
    # Get monthly tracking data for current year
    current_year = get_toronto_date().year
    cursor.execute('''
        SELECT * FROM condo_monthly_tracking 
        WHERE year = ? 
        ORDER BY month
    ''', (current_year,))
    monthly_data = cursor.fetchall()
    
    # Get property tax schedule
    cursor.execute('''
        SELECT * FROM property_tax_schedule 
        WHERE year = ? 
        ORDER BY installment_number
    ''', (current_year,))
    property_tax_data = cursor.fetchall()
    
    # Calculate property tax totals
    cursor.execute('''
        SELECT 
            SUM(amount) as total_amount,
            COUNT(CASE WHEN paid = 1 THEN 1 END) as paid_count,
            COUNT(*) as total_count
        FROM property_tax_schedule 
        WHERE year = ?
    ''', (current_year,))
    tax_summary = cursor.fetchone()
    
    conn.close()
    
    return render_template('condo.html',
                         config=config,
                         total_expenses=total_expenses,
                         revenue=revenue,
                         yearly_revenue=yearly_revenue,
                         monthly_data=monthly_data,
                         property_tax_data=property_tax_data,
                         tax_summary=tax_summary,
                         current_year=current_year,
                         today=get_toronto_date())

@app.route('/condo/update_config', methods=['POST'])
def update_condo_config():
    """Update condo configuration"""
    try:
        mortgage = float(request.form.get('mortgage', 0))
        condo_fee = float(request.form.get('condo_fee', 0))
        property_tax = float(request.form.get('property_tax', 0))
        rent_amount = float(request.form.get('rent_amount', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO condo_config (mortgage, condo_fee, property_tax, rent_amount)
            VALUES (?, ?, ?, ?)
        ''', (mortgage, condo_fee, property_tax, rent_amount))
        
        conn.commit()
        conn.close()
        
        flash('Condo configuration updated successfully!', 'success')
        return redirect(url_for('condo'))
        
    except ValueError:
        flash('Please enter valid numeric values', 'error')
        return redirect(url_for('condo'))
    except Exception as e:
        flash(f'Error updating configuration: {str(e)}', 'error')
        return redirect(url_for('condo'))

@app.route('/condo/update_monthly/<int:year>/<int:month>', methods=['POST'])
def update_monthly_data(year, month):
    """Update monthly tracking data"""
    try:
        tenant_paid = float(request.form.get('tenant_paid', 0))
        enwin_bill = float(request.form.get('enwin_bill', 0))
        enbridge_bill = float(request.form.get('enbridge_bill', 0))
        who_paid_utilities = request.form.get('who_paid_utilities', 'Me')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO condo_monthly_tracking 
            (year, month, tenant_paid, enwin_bill, enbridge_bill, who_paid_utilities, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (year, month, tenant_paid, enwin_bill, enbridge_bill, who_paid_utilities))
        
        conn.commit()
        conn.close()
        
        flash(f'Updated data for {year}-{month:02d}', 'success')
        return redirect(url_for('condo'))
        
    except ValueError:
        flash('Please enter valid numeric values', 'error')
        return redirect(url_for('condo'))
    except Exception as e:
        flash(f'Error updating monthly data: {str(e)}', 'error')
        return redirect(url_for('condo'))

@app.route('/condo/toggle_tenant_payment/<int:year>/<int:month>', methods=['POST'])
def toggle_tenant_payment(year, month):
    """Toggle tenant payment status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current rent amount from config
        cursor.execute('SELECT rent_amount FROM condo_config ORDER BY id DESC LIMIT 1')
        config = cursor.fetchone()
        rent_amount = float(config['rent_amount']) if config else 2000.00
        
        # Get current status
        cursor.execute('''
            SELECT tenant_paid FROM condo_monthly_tracking 
            WHERE year = ? AND month = ?
        ''', (year, month))
        result = cursor.fetchone()
        
        if result and result['tenant_paid'] > 0:
            # Mark as unpaid
            new_amount = 0
        else:
            # Mark as paid
            new_amount = rent_amount
        
        cursor.execute('''
            INSERT OR REPLACE INTO condo_monthly_tracking 
            (year, month, tenant_paid, tenant_paid_date, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (year, month, new_amount, get_toronto_date() if new_amount > 0 else None))
        
        conn.commit()
        conn.close()
        
        status = 'paid' if new_amount > 0 else 'unpaid'
        flash(f'Tenant payment marked as {status} for {year}-{month:02d}', 'success')
        return redirect(url_for('condo'))
        
    except Exception as e:
        flash(f'Error updating tenant payment: {str(e)}', 'error')
        return redirect(url_for('condo'))

@app.route('/condo/toggle_property_tax/<int:tax_id>', methods=['POST'])
def toggle_property_tax_payment(tax_id):
    """Toggle property tax payment status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute('SELECT paid FROM property_tax_schedule WHERE id = ?', (tax_id,))
        result = cursor.fetchone()
        
        if result:
            new_status = 0 if result['paid'] else 1
            paid_date = get_toronto_date() if new_status else None
            
            cursor.execute('''
                UPDATE property_tax_schedule 
                SET paid = ?, paid_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, paid_date, tax_id))
            
            conn.commit()
            conn.close()
            
            status = 'paid' if new_status else 'unpaid'
            flash(f'Property tax installment marked as {status}', 'success')
        else:
            flash('Property tax installment not found', 'error')
        
        return redirect(url_for('condo'))
        
    except Exception as e:
        flash(f'Error updating property tax: {str(e)}', 'error')
        return redirect(url_for('condo'))
    
if __name__ == '__main__':
    # Add pytz to requirements
    app.run(debug=True, host='0.0.0.0', port=5001)