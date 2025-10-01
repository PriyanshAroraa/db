from http.server import BaseHTTPRequestHandler
import pandas as pd
import json
from sqlalchemy import create_engine
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Database configuration
        DB_USER = os.environ.get('DB_USER', '')
        DB_PASS = os.environ.get('DB_PASS', '^lm*rNX>3')
        DB_HOST = os.environ.get('DB_HOST', '')
        DB_PORT = os.environ.get('DB_PORT', '')
        DB_NAME = os.environ.get('DB_NAME', '')
        
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        TARGET_USER_IDS = "10111491, 10211493, 10411491, 10711491, 11011491"
        
        try:
            engine = create_engine(DATABASE_URL)
            
            # Fetch bot data
            queries = {
                'total_pnl': f"""
                    SELECT user_id, SUM(amount) / 1000000 AS total_pnl_IGGT
                    FROM player_token_transaction
                    WHERE user_id IN ({TARGET_USER_IDS})
                        AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                    GROUP BY user_id
                """,
                'reserve_balance': f"""
                    SELECT user_id, SUM(amount) / 1000000 AS reserve_balance_IGGT
                    FROM player_token_account
                    WHERE user_id IN ({TARGET_USER_IDS})
                    GROUP BY user_id
                """,
                'in_play_balance': f"""
                    SELECT t.user_id, SUM(ABS(t.amount)) / 1000000 AS in_play_balance_IGGT
                    FROM player_token_transaction t
                    LEFT JOIN full_WC_result r ON t.source_trx_id = r.event_id
                    WHERE t.user_id IN ({TARGET_USER_IDS})
                        AND t.amount < 0 AND t.ctx_type = 1
                        AND r.event_id IS NULL
                    GROUP BY t.user_id
                """,
                'races_entered': f"""
                    SELECT user_id, COUNT(*) AS races_entered
                    FROM full_WC_horse_snapshot
                    WHERE user_id IN ({TARGET_USER_IDS})
                    GROUP BY user_id
                """,
                'daily_pnl': f"""
                    SELECT user_id, DATE(FROM_UNIXTIME(created_at)) AS date,
                           SUM(amount) / 1000000 AS daily_pnl_IGGT
                    FROM player_token_transaction
                    WHERE ctx_type = 1 AND user_id IN ({TARGET_USER_IDS})
                        AND FROM_UNIXTIME(created_at) >= '2025-09-18'
                    GROUP BY user_id, date
                    ORDER BY user_id, date
                """
            }
            
            data = {}
            for key, query in queries.items():
                try:
                    df = pd.read_sql(query, engine)
                    data[key] = df.to_dict('records')
                except Exception as e:
                    data[key] = []
            
            # Add bot names
            BOT_NAMES = {
                10111491: "Alba",
                10211493: "Eirean", 
                10411491: "Kernow",
                10711491: "Cymru",
                11011491: "Albion"
            }
            
            response = {
                'success': True,
                'data': data,
                'bot_names': BOT_NAMES,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            response = {
                'success': False,
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        return
