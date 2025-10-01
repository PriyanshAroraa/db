from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')
TARGET_USER_IDS = os.getenv('BOT_USER_IDS', '10111491,10211493,10411491,10711491,11011491')

def fetch_bot_data():
    """Fetch all bot performance data"""
    try:
        # Create database connection
        connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        # Define queries
        queries = {
            "Total_PnL": f"""
                SELECT
                    user_id,
                    SUM(ABS(amount)) / 1000000 AS total_pnl_IGGT
                FROM
                    player_token_transaction
                WHERE
                    user_id IN ({TARGET_USER_IDS})
                    AND ctx_type = 1
                    AND amount > 0
                GROUP BY
                    user_id;
            """,
            "Reserve_Balance": f"""
                SELECT
                    user_id,
                    SUM(ABS(amount)) / 1000000 AS reserve_balance_IGGT
                FROM
                    player_token_transaction
                WHERE
                    user_id IN ({TARGET_USER_IDS})
                    AND ctx_type = 1
                    AND amount > 0
                    AND source_trx_id IS NULL
                GROUP BY
                    user_id;
            """,
            "In_Play_Balance": f"""
                SELECT
                    t.user_id,
                    SUM(ABS(t.amount)) / 1000000 AS in_play_balance_IGGT
                FROM
                    player_token_transaction t
                LEFT JOIN
                    full_WC_result r ON t.source_trx_id = r.event_id
                WHERE
                    t.user_id IN ({TARGET_USER_IDS})
                    AND t.amount < 0
                    AND t.ctx_type = 1
                    AND r.event_id IS NULL
                GROUP BY
                    t.user_id;
            """,
            "Races_Entered": f"""
                SELECT
                    user_id,
                    COUNT(*) AS races_entered
                FROM
                    full_WC_horse_snapshot
                WHERE
                    user_id IN ({TARGET_USER_IDS})
                GROUP BY
                    user_id;
            """,
            "Daily_PnL": f"""
                SELECT
                    user_id,
                    DATE(FROM_UNIXTIME(created_at)) AS date,
                    SUM(ABS(amount)) / 1000000 AS daily_pnl_IGGT
                FROM
                    player_token_transaction
                WHERE
                    user_id IN ({TARGET_USER_IDS})
                    AND ctx_type = 1
                    AND amount > 0
                    AND created_at >= UNIX_TIMESTAMP('2024-09-18')
                GROUP BY
                    user_id, DATE(FROM_UNIXTIME(created_at))
                ORDER BY
                    date DESC;
            """,
            "Weekly_PnL": f"""
                SELECT
                    user_id,
                    YEARWEEK(FROM_UNIXTIME(created_at)) AS week,
                    SUM(ABS(amount)) / 1000000 AS weekly_pnl_IGGT
                FROM
                    player_token_transaction
                WHERE
                    user_id IN ({TARGET_USER_IDS})
                    AND ctx_type = 1
                    AND amount > 0
                    AND created_at >= UNIX_TIMESTAMP('2024-09-18')
                GROUP BY
                    user_id, YEARWEEK(FROM_UNIXTIME(created_at))
                ORDER BY
                    week DESC;
            """
        }
        
        results = {}
        
        for query_name, query in queries.items():
            try:
                df = pd.read_sql(query, engine)
                results[query_name] = df.to_dict('records')
                print(f"✅ {query_name}: {len(df)} records")
            except Exception as e:
                print(f"❌ {query_name}: {str(e)}")
                results[query_name] = []
        
        return results
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def handler(request):
    """Vercel serverless function handler"""
    if request.method == 'GET':
        # Fetch data
        data = fetch_bot_data()
        
        if data:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(data)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to fetch data'})
            }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Method not allowed'})
    }
