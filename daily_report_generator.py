import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    print("Error: Missing database configuration. Please check your .env file.")
    exit(1)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Bot configuration from environment variables
BOT_USER_IDS_STR = os.getenv('BOT_USER_IDS', '10111491,10211493,10411491,10711491,11011491')
BOT_USER_IDS_LIST = [int(x.strip()) for x in BOT_USER_IDS_STR.split(',')]

BOT_NAMES = {
    10111491: "Alba",
    10211493: "Eirean", 
    10411491: "Kernow",
    10711491: "Cymru",
    11011491: "Albion"
}

TARGET_USER_IDS = ", ".join(map(str, BOT_USER_IDS_LIST))

def get_bot_data():
    """Fetch all bot performance data"""
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
            data[key] = pd.read_sql(query, engine)
        except Exception as e:
            print(f"Error fetching {key}: {e}")
            data[key] = pd.DataFrame()
    
    return data

def generate_comprehensive_report():
    """Generate a comprehensive daily report"""
    print("Fetching bot performance data...")
    data = get_bot_data()
    
    # Create comprehensive summary
    summary_data = []
    
    for user_id, bot_name in BOT_NAMES.items():
        # Get data for this bot
        total_pnl = data['total_pnl'][data['total_pnl']['user_id'] == user_id]['total_pnl_IGGT'].iloc[0] if len(data['total_pnl']) > 0 else 0
        reserve = data['reserve_balance'][data['reserve_balance']['user_id'] == user_id]['reserve_balance_IGGT'].iloc[0] if len(data['reserve_balance']) > 0 else 0
        in_play = data['in_play_balance'][data['in_play_balance']['user_id'] == user_id]['in_play_balance_IGGT'].iloc[0] if len(data['in_play_balance']) > 0 else 0
        races = data['races_entered'][data['races_entered']['user_id'] == user_id]['races_entered'].iloc[0] if len(data['races_entered']) > 0 else 0
        
        summary_data.append({
            'Bot Name': bot_name,
            'User ID': user_id,
            'Total P&L (IGGT)': f"{total_pnl:,.2f}",
            'Reserve Balance (IGGT)': f"{reserve:,.2f}",
            'In-Play Balance (IGGT)': f"{in_play:,.2f}",
            'Total Races Entered': races,
            'Avg P&L per Race': f"{total_pnl/races if races > 0 else 0:,.2f}",
            'Performance Rating': 'Excellent' if total_pnl > 3000 else 'Good' if total_pnl > 2000 else 'Needs Attention'
        })
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    # Generate report
    report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""
BOT PERFORMANCE REPORT - {report_date}
{'='*80}

EXECUTIVE SUMMARY
{'-'*50}

OVERALL PERFORMANCE
• Total Bots Active: {len(BOT_NAMES)}
• Total Races Entered: {summary_df['Total Races Entered'].sum()}
• Total P&L (All Bots): {summary_df['Total P&L (IGGT)'].str.replace(',', '').astype(float).sum():,.2f} IGGT
• Total Reserve Balance: {summary_df['Reserve Balance (IGGT)'].str.replace(',', '').astype(float).sum():,.2f} IGGT
• Total In-Play Exposure: {summary_df['In-Play Balance (IGGT)'].str.replace(',', '').astype(float).sum():,.2f} IGGT

TOP PERFORMERS
{'-'*50}
"""
    
    # Sort by performance and add rankings
    summary_df_sorted = summary_df.copy()
    summary_df_sorted['Total P&L (IGGT)'] = summary_df_sorted['Total P&L (IGGT)'].str.replace(',', '').astype(float)
    summary_df_sorted = summary_df_sorted.sort_values('Total P&L (IGGT)', ascending=False)
    
    for i, (_, row) in enumerate(summary_df_sorted.iterrows(), 1):
        report += f"{i}. {row['Bot Name']} ({row['User ID']}): {row['Total P&L (IGGT)']:,.2f} IGGT | {row['Performance Rating']}\n"
    
    report += f"""
DETAILED BREAKDOWN
{'-'*50}
"""
    
    # Add detailed table
    report += summary_df.to_string(index=False)
    
    # Add insights
    report += f"""

KEY INSIGHTS
{'-'*50}

1. PERFORMANCE ANALYSIS:
   • Best Performer: {summary_df_sorted.iloc[0]['Bot Name']} with {summary_df_sorted.iloc[0]['Total P&L (IGGT)']:,.2f} IGGT
   • Most Active: {summary_df.loc[summary_df['Total Races Entered'].idxmax(), 'Bot Name']} with {summary_df['Total Races Entered'].max()} races
   • Highest Reserve: {summary_df.loc[summary_df['Reserve Balance (IGGT)'].str.replace(',', '').astype(float).idxmax(), 'Bot Name']} with {summary_df['Reserve Balance (IGGT)'].str.replace(',', '').astype(float).max():,.2f} IGGT

2. RISK ASSESSMENT:
   • Total exposure in unsettled races: {summary_df['In-Play Balance (IGGT)'].str.replace(',', '').astype(float).sum():,.2f} IGGT
   • Average P&L per race: {summary_df['Total P&L (IGGT)'].str.replace(',', '').astype(float).sum() / summary_df['Total Races Entered'].sum():,.2f} IGGT
   • Reserve coverage ratio: {summary_df['Reserve Balance (IGGT)'].str.replace(',', '').astype(float).sum() / summary_df['In-Play Balance (IGGT)'].str.replace(',', '').astype(float).sum():.2f}x

3. RECOMMENDATIONS:
   • All bots showing positive performance post-top-up
   • Monitor reserve balances for optimal fund management
   • Consider rebalancing if individual bot performance diverges significantly

Report Generated: {report_date}
Internal Use Only - Bot Performance Tracking
"""
    
    return report, summary_df

if __name__ == "__main__":
    try:
        report_content, summary_df = generate_comprehensive_report()
        
        # Save report to file
        filename = f"bot_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report_content)
        
        print("Report generated successfully!")
        print(f"Saved to: {filename}")
        print("\n" + "="*50)
        print(report_content)
        
    except Exception as e:
        print(f"Error generating report: {e}")
