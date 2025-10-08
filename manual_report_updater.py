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
            # ============================================
            # BOT-LEVEL QUERIES (Original)
            # ============================================
            'Total_PnL': f"""
                SELECT
                    user_id,
                    SUM(amount) / 1000000 AS total_pnl_IGGT
                FROM player_token_transaction
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND ctx_type = 1
                    AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                GROUP BY user_id
            """,
            'Reserve_Balance': f"""
                SELECT
                    user_id,
                    amount / 1000000 AS reserve_balance_IGGT
                FROM player_token_account
                WHERE user_id IN ({TARGET_USER_IDS})
            """,
            'In_Play_Balance': f"""
                SELECT
                    t.user_id,
                    SUM(ABS(t.amount)) / 1000000 AS in_play_balance_IGGT
                FROM player_token_transaction t
                LEFT JOIN full_WC_result r ON t.source_trx_id = r.event_id
                WHERE t.user_id IN ({TARGET_USER_IDS})
                    AND t.amount < 0
                    AND t.ctx_type = 1
                    AND r.event_id IS NULL
                    AND FROM_UNIXTIME(t.created_at) >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                GROUP BY t.user_id
            """,
            'Races_Entered': f"""
                SELECT
                    user_id,
                    COUNT(*) AS races_entered
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id
            """,
            'Daily_PnL': f"""
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
            'Weekly_PnL': f"""
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
            """,
            
            # ============================================
            # HORSE-LEVEL QUERIES
            # ============================================
            
            # 1. Individual Horse Performance Summary
            'Horse_Performance': f"""
                SELECT 
                    hs.user_id,
                    hs.user_horse_id,
                    hs.name as horse_name,
                    hs.generation as gen,
                    hs.grade,
                    hs.gender,
                    hs.age,
                    hs.trainer_id,
                    COUNT(DISTINCT hs._id) as total_races,
                    AVG(hs.final_position) as avg_finish_position,
                    SUM(CASE WHEN hs.final_position = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN hs.final_position <= 3 THEN 1 ELSE 0 END) as top_3_finishes,
                    AVG(hs.rating) as avg_rating,
                    AVG(hs.speed) as avg_speed,
                    AVG(hs.stamina) as avg_stamina,
                    AVG(hs.acceleration) as avg_acceleration,
                    SUM(hs.career_earnings) / 1000000 as total_career_earnings_IGGT
                FROM full_WC_horse_snapshot hs
                WHERE hs.user_id IN ({TARGET_USER_IDS})
                    AND hs.user_horse_id > 0
                GROUP BY hs.user_id, hs.user_horse_id, hs.name, hs.generation, hs.grade, 
                         hs.gender, hs.age, hs.trainer_id
                ORDER BY hs.user_id, total_races DESC
            """,
            
            # 2. Recent Race Performance (Last 100 races with details)
            'Recent_Race_Performance': f"""
                SELECT 
                    user_id,
                    user_horse_id,
                    name as horse_name,
                    _id as snapshot_id,
                    created_ts as race_date,
                    final_position,
                    grade,
                    rating,
                    speed,
                    stamina,
                    acceleration,
                    wins,
                    shows,
                    place,
                    career_earnings / 1000000 as career_earnings_IGGT,
                    trend
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND final_position IS NOT NULL
                ORDER BY user_id, created_ts DESC
                LIMIT 500
            """,
            
            # 3. Horse Performance by Grade
            'Horse_Performance_By_Grade': f"""
                SELECT 
                    user_id,
                    user_horse_id,
                    name as horse_name,
                    grade,
                    CASE 
                        WHEN grade = 1 THEN 'Starter'
                        WHEN grade = 2 THEN 'Regular'
                        WHEN grade = 3 THEN 'Pro'
                        ELSE 'Unknown'
                    END as grade_name,
                    COUNT(DISTINCT _id) as races_at_grade,
                    AVG(final_position) as avg_position,
                    SUM(CASE WHEN final_position = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN final_position <= 3 THEN 1 ELSE 0 END) as top_3_finishes,
                    AVG(rating) as avg_rating
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND grade IS NOT NULL
                GROUP BY user_id, user_horse_id, name, grade
                ORDER BY user_id, user_horse_id, grade
            """,
            
            # 4. Horse Traits Analysis (from snapshot data)
            'Horse_Traits_Performance': f"""
                SELECT 
                    user_id,
                    user_horse_id,
                    name as horse_name,
                    COUNT(DISTINCT _id) as total_races,
                    AVG(final_position) as avg_position,
                    -- Speed traits
                    MAX(speed_trait_1) as speed_trait_1,
                    MAX(speed_trait_2) as speed_trait_2,
                    AVG(speed_trait_1_pwr) as speed_trait_1_power,
                    AVG(speed_trait_2_pwr) as speed_trait_2_power,
                    -- Stamina traits
                    MAX(stamina_trait_1) as stamina_trait_1,
                    MAX(stamina_trait_2) as stamina_trait_2,
                    AVG(stamina_trait_1_pwr) as stamina_trait_1_power,
                    AVG(stamina_trait_2_pwr) as stamina_trait_2_power,
                    -- Acceleration traits
                    MAX(acceleration_trait_1) as acceleration_trait_1,
                    MAX(acceleration_trait_2) as acceleration_trait_2,
                    AVG(acceleration_trait_1_pwr) as acceleration_trait_1_power,
                    AVG(acceleration_trait_2_pwr) as acceleration_trait_2_power
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id, user_horse_id, name
                ORDER BY user_id, total_races DESC
            """,
            
            # 5. Horse Skills from Snapshot
            'Horse_Skills_From_Races': f"""
                SELECT 
                    user_id,
                    user_horse_id,
                    name as horse_name,
                    COUNT(*) as races_analyzed,
                    AVG(skill_first_out) as avg_skill_first_out,
                    AVG(skill_front) as avg_skill_front,
                    AVG(skill_rail) as avg_skill_rail,
                    AVG(skill_closing) as avg_skill_closing,
                    AVG(skill_dueling) as avg_skill_dueling,
                    AVG(skill_turning) as avg_skill_turning,
                    AVG(skill_working) as avg_skill_working,
                    AVG(skill_breezing) as avg_skill_breezing,
                    AVG(skill_drafting) as avg_skill_drafting,
                    AVG(skill_final_kick) as avg_skill_final_kick,
                    AVG(skill_overtaking) as avg_skill_overtaking
                FROM full_WC_horse_snapshot
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id, user_horse_id, name
                ORDER BY user_id, races_analyzed DESC
            """,
            
            # 10. Stable Composition (Horses per bot) - Using player_horse
            'Stable_Composition': f"""
                SELECT 
                    user_id,
                    COUNT(*) as total_horses,
                    SUM(CASE WHEN grade = 1 THEN 1 ELSE 0 END) as grade_1_horses,
                    SUM(CASE WHEN grade = 2 THEN 1 ELSE 0 END) as grade_2_horses,
                    SUM(CASE WHEN grade = 3 THEN 1 ELSE 0 END) as grade_3_horses,
                    SUM(CASE WHEN bloodline = 1 THEN 1 ELSE 0 END) as bloodline_1_horses,
                    SUM(CASE WHEN bloodline = 2 THEN 1 ELSE 0 END) as bloodline_2_horses,
                    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as active_horses,
                    AVG(gen) as avg_generation
                FROM player_horse
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND oc_shard > 0
                GROUP BY user_id
                ORDER BY user_id
            """,
            
            # 11. Horse Inventory (List of all bot horses)
            'Horse_Inventory': f"""
                SELECT 
                    user_id,
                    _id as horse_id,
                    name as horse_name,
                    grade,
                    bloodline,
                    gen as generation,
                    gender,
                    age,
                    trainer_id,
                    status,
                    horse_type_id,
                    modified_utc as last_updated
                FROM player_horse
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND oc_shard > 0
                ORDER BY user_id, grade DESC, name
            """,
            
            # 12. ALL HORSES - Complete Distance Performance
            'All_Horses_Distance_Performance': f"""
                SELECT 
                    hs.user_id,
                    hs.user_horse_id,
                    hs.name as horse_name,
                    e.distance,
                    CASE 
                        WHEN e.distance = 1 THEN '1000m (5f)'
                        WHEN e.distance = 2 THEN '1200m (6f)'
                        WHEN e.distance = 3 THEN '1400m (7f)'
                        WHEN e.distance = 4 THEN '1600m (8f)'
                        WHEN e.distance = 5 THEN '1800m (9f)'
                        WHEN e.distance = 6 THEN '2000m (10f)'
                        ELSE 'Unknown'
                    END as distance_name,
                    CASE 
                        WHEN e.distance IN (1, 2) THEN 'Sprint'
                        WHEN e.distance IN (3, 4, 5) THEN 'Mile'
                        WHEN e.distance = 6 THEN 'Marathon'
                        ELSE 'Unknown'
                    END as distance_category,
                    COUNT(DISTINCT ent.event_id) as races_at_distance,
                    AVG(hs.final_position) as avg_position,
                    MIN(hs.final_position) as best_position,
                    MAX(hs.final_position) as worst_position,
                    SUM(CASE WHEN hs.final_position = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN hs.final_position <= 3 THEN 1 ELSE 0 END) as top_3_finishes,
                    AVG(hs.rating) as avg_rating
                FROM full_WC_horse_snapshot hs
                INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id 
                    AND hs.Zone = ent.Zone
                INNER JOIN full_WC_event e ON ent.event_id = e._id 
                    AND ent.Zone = e.Zone
                WHERE hs.user_id IN ({TARGET_USER_IDS})
                    AND e.distance IS NOT NULL
                GROUP BY hs.user_id, hs.user_horse_id, hs.name, e.distance
                ORDER BY hs.user_id, hs.user_horse_id, e.distance
            """,
            
            # 13. ALL HORSES - Surface Performance (Dirt vs Turf)
            'All_Horses_Surface_Performance': f"""
                SELECT 
                    hs.user_id,
                    hs.user_horse_id,
                    hs.name as horse_name,
                    e.surface,
                    CASE 
                        WHEN e.surface = 1 THEN 'Dirt'
                        WHEN e.surface = 2 THEN 'Turf'
                        ELSE 'Unknown'
                    END as surface_name,
                    e.weather,
                    e.`condition`,
                    COUNT(DISTINCT ent.event_id) as races,
                    AVG(hs.final_position) as avg_position,
                    MIN(hs.final_position) as best_position,
                    MAX(hs.final_position) as worst_position,
                    SUM(CASE WHEN hs.final_position = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN hs.final_position <= 3 THEN 1 ELSE 0 END) as top_3_finishes,
                    AVG(hs.rating) as avg_rating
                FROM full_WC_horse_snapshot hs
                INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id 
                    AND hs.Zone = ent.Zone
                INNER JOIN full_WC_event e ON ent.event_id = e._id 
                    AND ent.Zone = e.Zone
                WHERE hs.user_id IN ({TARGET_USER_IDS})
                    AND e.surface IS NOT NULL
                GROUP BY hs.user_id, hs.user_horse_id, hs.name, e.surface, e.weather, e.`condition`
                ORDER BY hs.user_id, hs.user_horse_id, races DESC
            """,
            
            # 14. ALL HORSES - Complete Race Details (with distance & surface)
            'All_Horses_Complete_Races': f"""
                SELECT 
                    hs.user_id,
                    hs.user_horse_id,
                    hs.name as horse_name,
                    ent.event_id,
                    e.distance,
                    CASE 
                        WHEN e.distance IN (1, 2) THEN 'Sprint'
                        WHEN e.distance IN (3, 4, 5) THEN 'Mile'
                        WHEN e.distance = 6 THEN 'Marathon'
                    END as distance_category,
                    e.surface,
                    CASE WHEN e.surface = 1 THEN 'Dirt' ELSE 'Turf' END as surface_name,
                    hs.final_position,
                    hs.rating,
                    e.track_name,
                    hs.created_ts as race_date,
                    hs.Zone
                FROM full_WC_horse_snapshot hs
                INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id 
                    AND hs.Zone = ent.Zone
                INNER JOIN full_WC_event e ON ent.event_id = e._id 
                    AND ent.Zone = e.Zone
                WHERE hs.user_id IN ({TARGET_USER_IDS})
                ORDER BY hs.user_id, hs.created_ts DESC
                LIMIT 2000
            """
            ,
            
            # 14. Distance Breakdown by Bot (which races they enter)
            'Bot_Distance_Breakdown': f"""
                SELECT 
                    user_id,
                    distance,
                    CASE 
                        WHEN distance = 1 THEN '1000m'
                        WHEN distance = 2 THEN '1200m'
                        WHEN distance = 3 THEN '1400m'
                        WHEN distance = 4 THEN '1600m'
                        WHEN distance = 5 THEN '1800m'
                        WHEN distance = 6 THEN '2000m'
                        ELSE 'Unknown'
                    END as distance_name,
                    CASE 
                        WHEN distance IN (1, 2) THEN 'Sprint'
                        WHEN distance IN (3, 4, 5) THEN 'Mile'
                        WHEN distance = 6 THEN 'Marathon'
                    END as distance_category,
                    SUM(count) as total_races,
                    ROUND(SUM(count) * 100.0 / SUM(SUM(count)) OVER (PARTITION BY user_id), 2) as pct_of_total
                FROM player_daily_fact_distance
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id, distance
                ORDER BY user_id, distance
            """,
            
            # 13. Grade Distribution by Bot
            'Bot_Grade_Distribution': f"""
                SELECT 
                    user_id,
                    grade,
                    CASE 
                        WHEN grade = 1 THEN 'Starter'
                        WHEN grade = 2 THEN 'Regular'
                        WHEN grade = 3 THEN 'Pro'
                        ELSE 'Unknown'
                    END as grade_name,
                    SUM(count) as total_races,
                    ROUND(SUM(count) * 100.0 / SUM(SUM(count)) OVER (PARTITION BY user_id), 2) as pct_of_total
                FROM player_daily_fact_grade
                WHERE user_id IN ({TARGET_USER_IDS})
                    AND grade > 0
                GROUP BY user_id, grade
                ORDER BY user_id, grade
            """,
            
            # 14. Track Preferences by Bot
            'Bot_Track_Preferences': f"""
                SELECT 
                    user_id,
                    track_id,
                    SUM(count) as total_races,
                    ROUND(SUM(count) * 100.0 / SUM(SUM(count)) OVER (PARTITION BY user_id), 2) as pct_of_total
                FROM player_daily_fact_track
                WHERE user_id IN ({TARGET_USER_IDS})
                GROUP BY user_id, track_id
                ORDER BY user_id, total_races DESC
            """,
            
            # 15. Horse Distance Analysis (Inferred from bot pattern + horse performance)
            'Horse_Distance_Analysis': f"""
                SELECT 
                    ph.user_id,
                    ph.name as horse_name,
                    ph.grade,
                    hp.total_races,
                    hp.wins,
                    hp.avg_finish_position,
                    hp.avg_stamina,
                    hp.avg_speed,
                    hp.avg_acceleration,
                    -- Calculate likely distance specialization from stats
                    CASE 
                        WHEN hp.avg_stamina > 85 AND hp.avg_speed > 80 AND hp.avg_acceleration < 75 THEN 'Mile/Marathon'
                        WHEN hp.avg_stamina < 75 AND hp.avg_acceleration > 75 THEN 'Sprint'
                        WHEN hp.avg_stamina > 80 AND hp.avg_speed < 75 THEN 'Marathon'
                        ELSE 'Mile'
                    END as inferred_specialization,
                    hp.avg_rating
                FROM player_horse ph
                INNER JOIN (
                    SELECT 
                        user_id,
                        user_horse_id,
                        name,
                        COUNT(*) as total_races,
                        SUM(CASE WHEN final_position = 1 THEN 1 ELSE 0 END) as wins,
                        AVG(final_position) as avg_finish_position,
                        AVG(stamina) as avg_stamina,
                        AVG(speed) as avg_speed,
                        AVG(acceleration) as avg_acceleration,
                        AVG(rating) as avg_rating
                    FROM full_WC_horse_snapshot
                    WHERE user_id IN ({TARGET_USER_IDS})
                    GROUP BY user_id, user_horse_id, name
                ) hp ON ph.user_id = hp.user_id
                WHERE ph.user_id IN ({TARGET_USER_IDS})
                    AND ph.oc_shard > 0
                ORDER BY ph.user_id, hp.total_races DESC
            """
        }
        
        data = {}
        for key, query in queries.items():
            try:
                df = pd.read_sql(query, engine)
                data[key] = df.to_dict('records')
                print(f"SUCCESS {key}: {len(df)} records")
                
                # Debug: Show sample data for key queries
                if key in ['Total_PnL', 'Reserve_Balance', 'In_Play_Balance'] and len(data[key]) > 0:
                    print(f"   Sample data: {data[key][0]}")
                    
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
