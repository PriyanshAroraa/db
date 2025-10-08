# 🤖 Bot Performance Dashboard

A comprehensive dashboard for monitoring trading bot performance with automated reporting and real-time analytics.

## 📋 Features

### Bot-Level Analytics
- **📊 Real-time Metrics**: Total P&L, races entered, balances
- **📈 Interactive Charts**: Performance comparison, trends, efficiency analysis
- **💰 Balance Analysis**: Reserve vs in-play balance tracking
- **📅 Time Series**: Daily and weekly performance trends

### 🐴 Horse-Level Analytics (NEW!)
- **Individual Horse Performance**: 54 horses tracked across 5 bots
- **Distance Specialization**: Sprint/Mile/Marathon performance breakdown
- **Surface Analysis**: Dirt vs Turf preferences per horse
- **Race Entry Tracking**: 861+ complete race records with details
- **Optimization Insights**: Identify which horses should race where

### System Features
- **📥 Export Functionality**: CSV reports and data downloads
- **🔄 Manual Updates**: Run updates locally to avoid IP restrictions
- **☁️ Vercel Deployment**: Host on Vercel with static files
- **📄 Complete Documentation**: Horse data schema and optimization guides

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or download the project
cd bot-dashboard

# Run setup script
python setup.py

# Edit .env file with your database credentials
# (Copy from env.txt and update with your actual values)
```

### 2. Update Data

```bash
# Run manual updater to fetch latest data
python manual_report_updater.py
```

### 3. View Dashboard

```bash
# Run static dashboard (reads from JSON files)
streamlit run static_dashboard.py

# Or run live dashboard (connects directly to database)
streamlit run dashboard.py
```

## 📁 Project Structure

```
bot-dashboard/
├── 📊 dashboard.py                      # Live dashboard (connects to DB)
├── 📊 static_dashboard.py               # Static dashboard (reads JSON files)
├── 🔄 manual_report_updater.py          # Manual data updater (NOW WITH HORSE-LEVEL DATA!)
├── 📄 daily_report_generator.py         # Generate text reports
├── 🔧 setup.py                          # Setup script
├── 📝 README.md                         # This file
├── 🐴 HORSE_DATA_DOCUMENTATION.md       # Horse data schema & query guide
├── 📄 COMPLETE_HORSE_DATA_SUMMARY.txt   # Complete analysis summary
├── 🌐 static_dashboard.html             # Vercel static dashboard
├── ⚙️ vercel.json                       # Vercel configuration
├── 📋 requirements.txt                  # Python dependencies
├── 🔐 env.txt                           # Your environment file
├── 📋 env_example.txt                   # Environment template
└── 📊 bot_data.json                     # Generated data file (with horse-level data!)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your database credentials:

```env
# Database Configuration
DB_USER=your_database_username
DB_PASS=your_database_password
DB_HOST=your_database_host
DB_PORT=3306
DB_NAME=your_database_name

# Bot Configuration
BOT_USER_IDS=10111491,10211493,10411491,10711491,11011491
```

### Bot Configuration

The dashboard monitors these bots by default:
- **Alba** (10111491)
- **Eirean** (10211493)
- **Kernow** (10411491)
- **Cymru** (10711491)
- **Albion** (11011491)

## 📊 Usage

### Manual Updates

Since database access may be restricted by IP, use the manual updater:

```bash
# Update data from database
python manual_report_updater.py

# This creates:
# - bot_data.json (for dashboard)
# - bot_performance_report_YYYYMMDD_HHMMSS.txt (for reports)
# - last_updated.txt (timestamp)
```

### Dashboard Access

**Static Dashboard (Recommended):**
- Reads from `bot_data.json`
- No database connection required
- Perfect for hosting/deployment

**Live Dashboard:**
- Connects directly to database
- Real-time data
- Requires database access

### Report Generation

```bash
# Generate comprehensive daily report
python daily_report_generator.py

# Output: bot_performance_report_YYYYMMDD_HHMMSS.txt
```

## ☁️ Vercel Deployment

### 1. Prepare for Deployment

```bash
# Ensure all files are ready
python setup.py
python manual_report_updater.py
```

### 2. Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login and deploy
vercel login
vercel
```

### 3. Configure Environment Variables

In Vercel dashboard, set:
- `DB_USER`
- `DB_PASS`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `BOT_USER_IDS`

### 4. Access Your Dashboard

Your dashboard will be available at:
- `https://your-project.vercel.app`

## 📈 Dashboard Features

### Key Metrics
- **Total P&L**: Combined profit/loss across all bots
- **Total Races**: Number of races entered
- **Reserve Balance**: Available funds in accounts
- **In-Play Exposure**: Money staked in unsettled races

### Charts & Analysis
- **Performance Comparison**: P&L by bot
- **Races Analysis**: Activity levels
- **Balance Analysis**: Reserve vs in-play
- **Efficiency Scatter**: P&L vs races (bubble size = efficiency)
- **Daily Trends**: Time series performance
- **Detailed Table**: All metrics in one view

### Export Options
- **CSV Reports**: Download detailed data
- **Text Reports**: Comprehensive analysis
- **JSON Data**: Raw data for analysis

## 🔒 Security

### Database Security
- ✅ Environment variables for credentials
- ✅ No hardcoded passwords
- ✅ IP restrictions supported
- ✅ Manual update option

### Dashboard Security
- ✅ Internal use only
- ✅ No public data exposure
- ✅ Secure hosting options
- ✅ Access controls available

## 🆘 Troubleshooting

### Common Issues

**Database Connection Failed:**
```bash
# Check environment variables
cat .env

# Test connection
python manual_report_updater.py
```

**No Data in Dashboard:**
```bash
# Update data first
python manual_report_updater.py

# Check if bot_data.json exists
ls -la bot_data.json
```

**Vercel Deployment Issues:**
```bash
# Check environment variables in Vercel
# Verify API endpoint works
curl https://your-project.vercel.app/api/bot-data
```

### Manual Data Update Process

1. **Run Updater**: `python manual_report_updater.py`
2. **Commit Changes**: `git add . && git commit -m "Update bot data"`
3. **Push to GitHub**: `git push`
4. **Vercel Auto-Deploy**: Updates automatically

## 📞 Support

### File Structure
- `dashboard.py` - Live Streamlit dashboard
- `static_dashboard.py` - Static file-based dashboard
- `manual_report_updater.py` - Data update script
- `daily_report_generator.py` - Report generation
- `setup.py` - Initial setup

### Data Flow
1. **Database** → `manual_report_updater.py` → `bot_data.json`
2. **bot_data.json** → `static_dashboard.py` → **Dashboard**
3. **Database** → `daily_report_generator.py` → **Text Report**

---

## 🐴 Horse-Level Analytics (NEW!)

### Granular Performance Tracking

The system now provides **horse-level optimization data** as requested by Jonathan:

**Available Data:**
- **273 Distance Performance Records** - Each horse's performance at every distance (5f-10f)
- **247 Surface Performance Records** - Dirt vs Turf analysis per horse
- **861 Complete Race Records** - Full race history with distance, surface, position, rating
- **54 Horses Tracked** - Across all 5 bots
- **Distance Specialization** - Identify Sprinters, Milers, Marathoners
- **Surface Preferences** - Dirt vs Turf performance comparison

### Example Insights

**Tayport (Alba's Horse):**
- Specialization: **Sprinter**
- Best at: 1000m (5f) - 4.75 avg position
- Worst at: 1600m (8f Mile) - 8.00 avg position
- Issue: 0 wins despite good positioning → competition too tough

**Donegal (Eirean's Star):**
- Specialization: **Sprint Specialist**
- Win Rate: 21.7% (5 wins in 23 races)
- 1200m: 22% win rate
- 1600m: 40% win rate
- Status: **Optimal race selection**

### Documentation

📄 **HORSE_DATA_DOCUMENTATION.md** - Complete guide:
- Database schema for horse data
- How to query distance/surface performance
- Table relationships (snapshot → entrant → event)
- SQL examples for optimization queries

📄 **COMPLETE_HORSE_DATA_SUMMARY.txt** - Analysis summary:
- All horses analyzed
- Distance specializations
- Surface preferences
- Optimization recommendations

### Optimization Capabilities

This enables Jonathan's optimization vision:
- ✅ Horse-level performance tracking
- ✅ Distance specialization (Sprint/Mile/Marathon)
- ✅ Surface preference analysis (Dirt/Turf)
- ✅ Race selection optimization
- ✅ Identify mismatches (wrong distance/competition)
- ✅ Stable composition analysis
- ✅ Multivariate performance factors

**Status: READY for genetic algorithm optimization and break-even strategy!**

---

**🎉 Your bot performance monitoring system is ready!**

For questions or issues, check the troubleshooting section or review the code comments.

**For horse-level optimization, see `HORSE_DATA_DOCUMENTATION.md`**
