# Personal Finance & Activity Tracker

A comprehensive Flask-based web application for tracking personal finances, daily activities, investment portfolio, and savings goals. Built with a focus on detailed analytics and insights into spending habits and lifestyle patterns.

## 🌟 Features

### 📊 Dashboard
- **Budget Overview**: Visual progress bar with 14-day budget periods
- **Real-time Spending Analytics**: Daily spend limits and remaining budget calculations
- **Activity Statistics**: 30-day and all-time activity frequency tracking
- **Enhanced Spending Categorization**: Automatic categorization of expenses by merchant/type
- **Interactive Charts**: Powered by Chart.js for spending trends and activity visualization

### 💰 Spending Tracker
- **Expense Management**: Add, view, and delete spending entries with date selection
- **Smart Categorization**: Automatic categorization for TIMS, McDonalds, Dispo, LCBO, Gas, Food, and more
- **Budget Period Tracking**: 14-day rolling budget periods with detailed breakdowns
- **Daily & Period Totals**: Real-time calculation of spending against budget limits

### 🏃‍♂️ Personal Activity Tracking
- **Daily Activity Logging**: Track Gym, Jiu Jitsu, Skateboarding, Work, Coitus, Sauna, Supplements
- **Notes Support**: Add detailed notes for each day's activities
- **Historical Data**: View recent entries and patterns over time
- **Percentage Analytics**: All-time activity frequency percentages

### 📈 Advanced Analytics
- **Rich Spending Insights**: Weekly, monthly, and quarterly spending analysis
- **Detailed Category Breakdown**: Comprehensive categorization with frequency counts
- **Top Items Analysis**: Most frequently purchased items and spending patterns
- **Trend Visualization**: Interactive charts showing spending and activity trends over time
- **Category Trends**: Visual representation of spending distribution across categories

### 💼 Portfolio Management
- **Investment Tracking**: Track stocks and ETFs with real-time price updates
- **Performance Analytics**: Portfolio value tracking and performance metrics
- **Automatic Updates**: Scheduled ETF price updates and portfolio rebalancing
- **Individual Asset Management**: Add, update, and remove portfolio positions

### 💎 Savings Calculator
- **Expense Planning**: Track and categorize various expense types
- **Savings Goals**: Calculate required savings for planned expenses
- **Default Expense Management**: Set up recurring or standard expense amounts
- **Configuration Settings**: Customize savings calculations and parameters

### 🔒 Privacy Features
- **Hidden Content Toggle**: Discretely hide sensitive activity data with a toggle button
- **Secure Data Storage**: Local SQLite database with no external data sharing

## 🛠️ Technical Stack

- **Backend**: Flask 2.3.3 (Python web framework)
- **Database**: SQLite with automatic schema management
- **Frontend**: Bootstrap 5, Chart.js, vanilla JavaScript
- **Data Processing**: Pandas 2.0.3, openpyxl 3.1.2
- **Time Handling**: pytz 2023.3 (Toronto timezone support)
- **HTTP Requests**: requests 2.31.0 for external API calls

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip package manager

### Installation

1. **Clone or download the project**:
   ```bash
   cd personalWebApp
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv virtualEnv
   
   # On Linux/macOS:
   source virtualEnv/bin/activate
   
   # On Windows:
   virtualEnv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   Open your browser and navigate to `http://localhost:5001`

### 🐳 Docker Deployment

The application includes Docker support for easy deployment:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:5001
```

## 📁 Project Structure

```
personalWebApp/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── finance_tracker.db             # SQLite database (auto-created)
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container configuration
├── CLAUDE.md                      # Development instructions
├── templates/                     # Jinja2 HTML templates
│   ├── base.html                 # Base layout template
│   ├── dashboard.html            # Main dashboard
│   ├── analytics.html            # Advanced analytics
│   ├── personal.html             # Activity tracking
│   ├── spending.html             # Expense management
│   ├── portfolio.html            # Investment tracking
│   └── savings.html              # Savings calculator
├── static/                       # Static assets
├── img/                          # Images and icons
├── favicon_io/                   # Favicon files
├── virtualEnv/                   # Python virtual environment
├── auto_portfolio_update.py      # Portfolio automation script
├── update_portfolio.py           # Manual portfolio updater
├── setup_savings_table.py        # Database setup utility
├── daily_update.sh              # Automated daily updates
└── migration scripts/            # Data migration utilities
```

## 🎯 Key Features Explained

### Budget Management
- **14-Day Cycles**: Budget periods reset every 14 days automatically
- **Dynamic Calculations**: Real-time daily spend limits based on remaining budget and days
- **Default Budget**: $500 CAD per period (configurable)

### Smart Categorization
The application automatically categorizes expenses based on keywords:
- **TIMS**: Tim Hortons purchases
- **McDonalds**: McDonald's purchases  
- **Dispo**: Cannabis dispensary purchases
- **LCBO**: Alcohol purchases
- **Gas**: Fuel and gas station purchases
- **Food**: Restaurant and food purchases
- **Fitness**: Gym and workout expenses
- **Car Care**: Car wash and maintenance
- **Other**: Miscellaneous expenses

### Activity Tracking
Tracks daily activities with percentage analytics:
- **Gym**: Workout sessions
- **Jiu Jitsu**: Martial arts training
- **Skateboarding**: Recreation activity
- **Work**: Work days
- **Coitus**: Personal activity (can be hidden)
- **Sauna**: Wellness activity
- **Supplements**: Daily supplement intake

### Analytics Dashboard
- **Spending Trends**: Visual charts showing spending patterns over time
- **Activity Frequency**: Percentage-based activity analytics
- **Category Breakdown**: Pie charts and bar graphs for spending distribution
- **Time-based Analysis**: Weekly, monthly, and quarterly spending summaries

## 🔧 Configuration

### Database
The application uses SQLite with automatic table creation. Database file: `finance_tracker.db`

### Timezone
Configured for Toronto timezone (`America/Toronto`) using pytz.

### Budget Settings
Default budget amount can be modified in the `get_current_budget_period()` function in `app.py`.

## 📱 API Endpoints

The application provides REST API endpoints for data access:

- `GET /api/analytics` - General analytics data
- `GET /api/analytics/detailed` - Detailed category analytics  
- `GET /api/analytics/activities` - Activity frequency data
- `GET /api/portfolio` - Portfolio holdings and performance
- `POST /api/portfolio/update_daily` - Update portfolio values
- `POST /api/portfolio/auto_update` - Trigger automatic updates

## 🔄 Automation

### Portfolio Updates
- Automatic ETF price updates via scheduled scripts
- Real-time portfolio value calculations
- Performance tracking over time

### Daily Updates
The `daily_update.sh` script can be scheduled via cron for automated daily tasks.

## 🛡️ Security & Privacy

- **Local Storage**: All data stored locally in SQLite database
- **No External Sharing**: Personal data never transmitted to external services
- **Privacy Toggle**: Ability to hide sensitive activity data
- **Secure Sessions**: Flask session management with secret key

## 🚀 Future Enhancements

Potential improvements identified in development:
- User authentication for multi-user support
- Mobile app development using Flask API
- Bank API integration for automatic transaction import
- Advanced goal setting and achievement tracking
- Data export functionality (CSV, PDF reports)
- Backup and sync capabilities
- Push notifications for budget alerts
- Monthly/yearly reporting dashboards

## 🤝 Contributing

This is a personal finance application. If you'd like to adapt it for your own use:

1. Fork the repository
2. Customize categories and activities for your needs
3. Modify budget periods and amounts as required
4. Adapt the categorization logic in the SQL queries

## 📄 License

Personal use application. Feel free to adapt for your own financial tracking needs.

## 🆘 Troubleshooting

### Common Issues

1. **Database Errors**:
   - Delete `finance_tracker.db` and restart the app
   - Database will be recreated automatically

2. **Port Conflicts**:
   - Change port in `app.py` from 5001 to another available port
   - Update `docker-compose.yml` port mapping accordingly

3. **Template Not Found**:
   - Ensure `templates/` directory exists in the same location as `app.py`
   - Check template file names match the routes

4. **Charts Not Loading**:
   - Check internet connection (Chart.js loads from CDN)
   - Verify browser console for JavaScript errors

5. **Docker Issues**:
   - Ensure Docker and Docker Compose are installed
   - Check port 5001 is not in use by other services

### Development Mode

To run in development mode with debug enabled:

```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

---

**Note**: This application is designed for personal use and includes tracking of personal activities. The privacy toggle feature allows hiding sensitive data when needed.