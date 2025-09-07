from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from datetime import datetime, timedelta
import sqlite3
import os
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/favicon_io/<path:filename>')
def favicon_io(filename):
    return send_from_directory('favicon_io', filename)

@app.template_filter('tojsonfilter')
def to_json_filter(value):
    def convert_row_to_dict(obj):
        if hasattr(obj, 'keys'):
            return dict(obj)
        elif isinstance(obj, list):
            return [convert_row_to_dict(item) for item in obj]
        else:
            return obj
    
    converted_value = convert_row_to_dict(value)
    return json.dumps(converted_value)

def get_db_connection():
    conn = sqlite3.connect('finance_tracker.db')
    conn.row_factory = sqlite3.Row
    
    # Fix SQLite date adapter deprecation warning
    def adapt_date_iso(val):
        return val.isoformat()
    
    def convert_date(val):
        return datetime.fromisoformat(val.decode()).date()
    
    sqlite3.register_adapter(datetime.date, adapt_date_iso)
    sqlite3.register_converter("DATE", convert_date)
    
    return conn

def get_current_budget_period():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
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
    
    today = datetime.now().date()
    end_date = datetime.strptime(budget_period['end_date'], '%Y-%m-%d').date()
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
    
    cursor.execute('''
        SELECT 
            CASE 
                WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%coffee%' THEN 'Coffee'
                WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' THEN 'Gas'
                WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%domino%' THEN 'Food'
                WHEN LOWER(item) LIKE '%weed%' OR LOWER(item) LIKE '%cannabis%' THEN 'Cannabis'
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
                         spending_by_category=spending_by_category)

@app.route('/personal')
def personal():
    today = datetime.now().date()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM personal_log WHERE date = ?', (today,))
    today_data = cursor.fetchone()
    
    cursor.execute('''
        SELECT * FROM personal_log 
        ORDER BY date DESC 
        LIMIT 10
    ''')
    recent_entries = cursor.fetchall()
    
    conn.close()
    
    return render_template('personal.html', 
                         today_data=today_data, 
                         recent_entries=recent_entries,
                         today=today)

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
    return redirect(url_for('personal'))

@app.route('/spending')
def spending():
    today = datetime.now().date()
    budget_period = get_current_budget_period()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM spending_log 
        WHERE date = ? 
        ORDER BY created_at DESC
    ''', (today,))
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
    ''', (today,))
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
                         today=today)

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
    today = datetime.now().date()
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
    
    # Detailed spending by category using spending_log with intelligent categorization
    cursor.execute('''
        SELECT 
            CASE 
                WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%coffee%' THEN 'Coffee'
                WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' OR LOWER(item) LIKE '%petro%' THEN 'Gas'
                WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%domino%' OR LOWER(item) LIKE '%metro%' OR LOWER(item) LIKE '%wendys%' OR LOWER(item) LIKE '%pizza%' OR LOWER(item) LIKE '%taco%' OR LOWER(item) LIKE '%burger%' OR LOWER(item) LIKE '%arbys%' THEN 'Food'
                WHEN LOWER(item) LIKE '%dispo%' OR LOWER(item) LIKE '%weed%' OR LOWER(item) LIKE '%cannabis%' THEN 'Cannabis'
                WHEN LOWER(item) LIKE '%gym%' OR LOWER(item) LIKE '%fit%' OR LOWER(item) LIKE '%workout%' THEN 'Fitness'
                WHEN LOWER(item) LIKE '%gift%' THEN 'Gifts'
                WHEN LOWER(item) LIKE '%wash%' OR LOWER(item) LIKE '%car%' THEN 'Car Care'
                ELSE 'Other'
            END as category,
            SUM(price) as total,
            COUNT(*) as count
        FROM spending_log 
        WHERE date >= ?
        GROUP BY category
        ORDER BY total DESC
    ''', (thirty_days_ago,))
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
    
    today = datetime.now().date()
    
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
    
    # Update ETF holdings
    cursor.execute('UPDATE etf_holdings SET purchase_value = ? WHERE etf_symbol = "NAS"', (nas_value,))
    cursor.execute('UPDATE etf_holdings SET purchase_value = ? WHERE etf_symbol = "BTCC"', (btcc_value,))
    cursor.execute('UPDATE etf_holdings SET purchase_value = ? WHERE etf_symbol = "ZSP"', (zsp_value,))
    
    conn.commit()
    conn.close()
    
    flash('ETF holdings updated successfully!', 'success')
    return redirect(url_for('portfolio'))

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics data - FIXED to show actual last 30 days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
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
    spending_dict = {row['date']: row['total'] for row in daily_spending}
    
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
    daily_activities = [dict(row) for row in cursor.fetchall()]
    
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
    
    # Category spending over time using spending_log
    cursor.execute('''
        SELECT 
            CASE 
                WHEN LOWER(item) LIKE '%tim%' OR LOWER(item) LIKE '%coffee%' THEN 'Coffee'
                WHEN LOWER(item) LIKE '%gas%' OR LOWER(item) LIKE '%fuel%' OR LOWER(item) LIKE '%petro%' THEN 'Gas'
                WHEN LOWER(item) LIKE '%food%' OR LOWER(item) LIKE '%restaurant%' OR LOWER(item) LIKE '%mcdonald%' OR LOWER(item) LIKE '%domino%' OR LOWER(item) LIKE '%metro%' OR LOWER(item) LIKE '%wendys%' OR LOWER(item) LIKE '%pizza%' OR LOWER(item) LIKE '%taco%' OR LOWER(item) LIKE '%burger%' OR LOWER(item) LIKE '%arbys%' THEN 'Food'
                WHEN LOWER(item) LIKE '%dispo%' OR LOWER(item) LIKE '%weed%' OR LOWER(item) LIKE '%cannabis%' THEN 'Cannabis'
                WHEN LOWER(item) LIKE '%gym%' OR LOWER(item) LIKE '%fit%' OR LOWER(item) LIKE '%workout%' THEN 'Fitness'
                WHEN LOWER(item) LIKE '%gift%' THEN 'Gifts'
                WHEN LOWER(item) LIKE '%wash%' OR LOWER(item) LIKE '%car%' THEN 'Car Care'
                ELSE 'Other'
            END as category,
            strftime('%Y-%m', date) as month,
            SUM(price) as total
        FROM spending_log 
        WHERE date >= date('now', '-6 months')
        GROUP BY category, strftime('%Y-%m', date)
        ORDER BY month, category
    ''')
    category_trends = [dict(row) for row in cursor.fetchall()]
    
    # Weekly spending averages
    cursor.execute('''
        SELECT 
            strftime('%Y-%W', date) as week,
            AVG(daily_total) as avg_daily
        FROM (
            SELECT date, SUM(price) as daily_total
            FROM spending_log
            WHERE date >= date('now', '-12 weeks')
            GROUP BY date
        )
        GROUP BY strftime('%Y-%W', date)
        ORDER BY week
    ''')
    weekly_averages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'category_trends': category_trends,
        'weekly_averages': weekly_averages
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
    today = datetime.now().date()
    
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)