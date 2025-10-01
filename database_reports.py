import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# --- 1. CONFIGURATION ---

# !!! IMPORTANT: Fill in your actual credentials here !!!
DB_USER = "customer_services"
DB_PASS = "BbZ3mlu^lm*rNX>3"
DB_HOST = "mysql-analytics-warehouse.cqiyzuvvkkfc.us-east-1.rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "analytics_db"
REPORT_OUTPUT_FILE = "report_results.txt"

# Construct the full SQLAlchemy connection string
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# List of target user IDs
TARGET_USER_IDS = (
    "10111491, 10211493, 10411491, 10711491, 11011491"
)

# Define all the SQL queries from your DBeaver scripts
SQL_QUERIES = {
    "Total_Net_PnL": f"""
        -- Query 1: Total Net P&L (Including Topup) since 2025-09-18
        SELECT
            user_id,
            SUM(amount) / 1000000 AS total_pnl_including_topup_IGGT
        FROM
            player_token_transaction
        WHERE
            user_id IN ({TARGET_USER_IDS})
            AND FROM_UNIXTIME(created_at) >= '2025-09-18'
        GROUP BY
            user_id;
    """,
    "In_Play_Balance": f"""
        -- Query 2: Current In-Play Balance (Staked money on unsettled races)
        SELECT
            t.user_id,
            SUM(ABS(t.amount)) / 1000000 AS in_play_balance_IGGT
        FROM
            player_token_transaction t
        LEFT JOIN
            full_WC_result r ON t.source_trx_id = r.event_id
        WHERE
            t.user_id IN ({TARGET_USER_IDS})
            AND t.amount < 0 -- Only entry fees (stakes)
            AND t.ctx_type = 1
            AND r.event_id IS NULL -- Race has not been settled yet
        GROUP BY
            t.user_id;
    """,
    "Reserve_Balance": f"""
        -- Query 3: Current Reserve Balance
        SELECT
            user_id,
            SUM(amount) / 1000000 AS reserve_balance_IGGT
        FROM
            player_token_account
        WHERE
            user_id IN ({TARGET_USER_IDS})
        GROUP BY
            user_id;
    """,
    "Races_Entered": f"""
        -- Query 4: Total Races Entered
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
    "Daily_Net_PnL": f"""
        -- Query 5: Daily Net P&L (Broken down by day)
        SELECT
            user_id,
            'DAILY' AS report_type,
            DATE(FROM_UNIXTIME(created_at)) AS report_group,
            SUM(amount) / 1000000 AS net_profit_loss_IGGT
        FROM
            player_token_transaction
        WHERE
            ctx_type = 1
            AND user_id IN ({TARGET_USER_IDS})
            AND FROM_UNIXTIME(created_at) >= '2025-09-18'
        GROUP BY
            user_id,
            report_group
        ORDER BY
            user_id,
            report_group;
    """,
    "Weekly_Net_PnL": f"""
        -- Query 6: Weekly Net P&L (Broken down by week)
        SELECT
            user_id,
            'WEEKLY' AS report_type,
            YEARWEEK(FROM_UNIXTIME(created_at), 1) AS report_group, -- Use mode 1 for week starting on Monday
            SUM(amount) / 1000000 AS net_profit_loss_IGGT
        FROM
            player_token_transaction
        WHERE
            ctx_type = 1
            AND user_id IN ({TARGET_USER_IDS})
            AND FROM_UNIXTIME(created_at) >= '2025-09-18'
        GROUP BY
            user_id,
            report_group
        ORDER BY
            user_id,
            report_group;
    """
}

# --- 2. EXECUTION FUNCTION ---

def run_reports_and_save_to_txt():
    """
    Connects to the MySQL database, executes all defined queries,
    and saves the results to a single text file.
    """
    try:
        # Create the database engine
        engine = create_engine(DATABASE_URL)
        print("Database connection engine created successfully.")
    except Exception as e:
        print(f"Error creating database engine: {e}")
        return

    report_content = []
    
    # Add a header for the report
    report_content.append("="*80)
    report_content.append(f"Analytics Data Warehouse Report - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"Database: {DB_NAME} on {DB_HOST}")
    report_content.append(f"Target Users: {TARGET_USER_IDS}")
    report_content.append("="*80)
    
    # Execute each query
    for name, query in SQL_QUERIES.items():
        print(f"\n-> Running Query: {name}...")
        report_content.append(f"\n\n--- REPORT: {name.replace('_', ' ').upper()} ---")
        
        try:
            # Read data from the database into a pandas DataFrame
            df = pd.read_sql(query, engine)
            
            if df.empty:
                report_content.append("No results found for this query.")
            else:
                # Convert DataFrame to a well-formatted string for the TXT file
                # index=False prevents writing the DataFrame index numbers
                report_content.append(df.to_string(index=False))
            
            print(f"   Success: Fetched {len(df)} rows.")

        except Exception as e:
            error_msg = f"   !! ERROR EXECUTING QUERY '{name}': {e}"
            report_content.append(error_msg)
            print(error_msg)

    # Write all collected content to the final TXT file
    try:
        with open(REPORT_OUTPUT_FILE, 'w') as f:
            f.write('\n'.join(report_content))
        print(f"\n\n*** SUCCESS: All reports saved to {REPORT_OUTPUT_FILE} ***")
    except Exception as e:
        print(f"Error writing to output file: {e}")

# Run the main function
if __name__ == "__main__":
    # Ensure you have the 'pymysql' package installed: pip install pandas sqlalchemy pymysql
    run_reports_and_save_to_txt()
