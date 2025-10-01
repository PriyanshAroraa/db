import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def get_database_config():
    """Get database configuration from environment variables"""
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME')
    
    if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
        raise ValueError("Missing database configuration. Please check your .env file.")
    
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return DATABASE_URL

def get_bot_config():
    """Get bot configuration from environment variables"""
    BOT_USER_IDS_STR = os.getenv('BOT_USER_IDS', '10111491,10211493,10411491,10711491,11011491')
    BOT_USER_IDS_LIST = [int(x.strip()) for x in BOT_USER_IDS_STR.split(',')]
    TARGET_USER_IDS = ", ".join(map(str, BOT_USER_IDS_LIST))
    
    BOT_NAMES = {
        10111491: "Alba",
        10211493: "Eirean", 
        10411491: "Kernow",
        10711491: "Cymru",
        11011491: "Albion"
    }
    
    return BOT_NAMES, TARGET_USER_IDS

def fetch_bot_data():
    """Fetch all bot performance data from database"""
    try:
        DATABASE_URL = get_database_config()
        _, TARGET_USER_IDS = get_bot_config()
        
        engine = create_engine(DATABASE_URL)
        
        queries = {
            'total_pnl': f"""
                SELECT
                    user_id,
                    SUM(amount) / 1000000 AS total_pnl_IGGT
                FROM player_token_transaction
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                GROUP BY user_id
            """,
            'reserve_balance': f"""
                SELECT
                    user_id,
                    SUM(amount) / 1000000 AS reserve_balance_IGGT
                FROM player_token_account
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id
            """,
            'in_play_balance': f"""
                SELECT
                    t.user_id,
                    SUM(ABS(t.amount)) / 1000000 AS in_play_balance_IGGT
                FROM player_token_transaction t
                LEFT JOIN full_WC_result r ON t.source_trx_id = r.event_id
                WHERE t.user_id IN ({TARGET_USER_IDS})
                    AND t.amount < 0
                    AND t.ctx_type = 1
                    AND r.event_id IS NULL
                GROUP BY t.user_id
            """,
            'races_entered': f"""
                SELECT
                    user_id,
                    COUNT(*) AS races_entered
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id
            """,
            'daily_pnl': f"""
                SELECT
                    user_id,
                    DATE(FROM_UNIXTIME(created_at)) AS date,
                    SUM(amount) / 1000000 AS daily_pnl_IGGT
                FROM player_token_transaction
                WHERE ctx_type = 1
                    AND user_id IN ({TARGET_USER_IDS})
                    AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                GROUP BY user_id, date
                ORDER BY user_id, date
            """,
            'weekly_pnl': f"""
                SELECT
                    user_id,
                    YEARWEEK(FROM_UNIXTIME(created_at), 1) AS week,
                    SUM(amount) / 1000000 AS weekly_pnl_IGGT
                FROM player_token_transaction
                WHERE ctx_type = 1
                    AND user_id IN ({TARGET_USER_IDS})
                    AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                GROUP BY user_id, week
                ORDER BY user_id, week
            """
        }
        
        data = {}
        for key, query in queries.items():
            try:
                df = pd.read_sql(query, engine)
                data[key] = df.to_dict('records')
                print(f"SUCCESS {key}: {len(df)} records")
            except Exception as e:
                print(f"ERROR {key}: Error - {e}")
                data[key] = []
        
        return data
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def save_data_to_files(data):
    """Save data to JSON files for the dashboard"""
    if data is None:
        print("No data to save")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save main data file
    data_file = 'bot_data.json'
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Data saved to {data_file}")
    
    # Save timestamp file
    timestamp_file = 'last_updated.txt'
    with open(timestamp_file, 'w') as f:
        f.write(datetime.now().isoformat())
    print(f"Timestamp saved to {timestamp_file}")
    
    # Create backup
    backup_file = f'backup_bot_data_{timestamp}.json'
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Backup saved to {backup_file}")

def generate_summary_report(data):
    """Generate a summary report"""
    if not data or not data.get('total_pnl'):
        return "No data available"
    
    BOT_NAMES, _ = get_bot_config()
    
    # Create summary
    summary_data = []
    for record in data['total_pnl']:
        user_id = record['user_id']
        bot_name = BOT_NAMES.get(user_id, f"Bot {user_id}")
        total_pnl = record['total_pnl_IGGT']
        
        # Get other metrics
        reserve = next((r['reserve_balance_IGGT'] for r in data['reserve_balance'] if r['user_id'] == user_id), 0)
        in_play = next((r['in_play_balance_IGGT'] for r in data['in_play_balance'] if r['user_id'] == user_id), 0)
        races = next((r['races_entered'] for r in data['races_entered'] if r['user_id'] == user_id), 0)
        
        summary_data.append({
            'Bot Name': bot_name,
            'User ID': user_id,
            'Total P&L (IGGT)': f"{total_pnl:,.2f}",
            'Reserve Balance (IGGT)': f"{reserve:,.2f}",
            'In-Play Balance (IGGT)': f"{in_play:,.2f}",
            'Total Races': races,
            'Performance Rating': 'Excellent' if total_pnl > 3000 else 'Good' if total_pnl > 2000 else 'Needs Attention'
        })
    
    # Generate report
    report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""
BOT PERFORMANCE REPORT - {report_date}
{'='*80}

EXECUTIVE SUMMARY
{'-'*50}

OVERALL PERFORMANCE
• Total Bots Active: {len(summary_data)}
• Total Races Entered: {sum(int(s['Total Races']) for s in summary_data)}
• Total P&L (All Bots): {sum(float(s['Total P&L (IGGT)'].replace(',', '')) for s in summary_data):,.2f} IGGT
• Total Reserve Balance: {sum(float(s['Reserve Balance (IGGT)'].replace(',', '')) for s in summary_data):,.2f} IGGT
• Total In-Play Exposure: {sum(float(s['In-Play Balance (IGGT)'].replace(',', '')) for s in summary_data):,.2f} IGGT

TOP PERFORMERS
{'-'*50}
"""
    
    # Sort by performance
    sorted_data = sorted(summary_data, key=lambda x: float(x['Total P&L (IGGT)'].replace(',', '')), reverse=True)
    
    for i, bot in enumerate(sorted_data, 1):
        report += f"{i}. {bot['Bot Name']} ({bot['User ID']}): {bot['Total P&L (IGGT)']} IGGT | {bot['Performance Rating']}\n"
    
    report += f"""
DETAILED BREAKDOWN
{'-'*50}
"""
    
    # Add detailed table
    for bot in summary_data:
        report += f"""
Bot: {bot['Bot Name']} ({bot['User ID']})
  Total P&L: {bot['Total P&L (IGGT)']} IGGT
  Reserve Balance: {bot['Reserve Balance (IGGT)']} IGGT
  In-Play Balance: {bot['In-Play Balance (IGGT)']} IGGT
  Total Races: {bot['Total Races']}
  Performance: {bot['Performance Rating']}
"""
    
    report += f"""

Report Generated: {report_date}
Internal Use Only - Bot Performance Tracking
"""
    
    return report

def main():
    """Main function to update bot data"""
    print("Bot Performance Data Updater")
    print("=" * 50)
    
    try:
        print("Fetching data from database...")
        data = fetch_bot_data()
        
        if data:
            print("Saving data to files...")
            save_data_to_files(data)
            
            print("Generating summary report...")
            report = generate_summary_report(data)
            
            # Save report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f'bot_performance_report_{timestamp}.txt'
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"Report saved to {report_file}")
            
            print("\n" + "=" * 50)
            print("UPDATE COMPLETE!")
            print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Data files ready for dashboard")
            
        else:
            print("Failed to fetch data")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your .env file is configured correctly")

if __name__ == "__main__":
    main()
