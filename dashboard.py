import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Bot Performance Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database configuration from environment variables
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    st.error("❌ Missing database configuration. Please check your environment variables.")
    st.stop()

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_bot_data():
    """Load bot performance data with caching"""
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
            st.error(f"Error loading {key}: {e}")
            data[key] = pd.DataFrame()
    
    return data

def create_performance_overview(data):
    """Create performance overview metrics"""
    # Merge all data
    overview = data['total_pnl'].merge(data['reserve_balance'], on='user_id', how='left')
    overview = overview.merge(data['in_play_balance'], on='user_id', how='left')
    overview = overview.merge(data['races_entered'], on='user_id', how='left')
    
    # Add bot names
    overview['bot_name'] = overview['user_id'].map(BOT_NAMES)
    
    # Fill NaN values
    overview = overview.fillna(0)
    
    return overview

def main():
    st.title("🤖 Bot Performance Dashboard")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading bot performance data..."):
        data = load_bot_data()
    
    if not data['total_pnl'].empty:
        overview = create_performance_overview(data)
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_pnl = overview['total_pnl_IGGT'].sum()
            st.metric(
                label="Total P&L (IGGT)",
                value=f"{total_pnl:,.0f}",
                delta=f"{total_pnl/len(overview):,.0f} avg"
            )
        
        with col2:
            total_races = overview['races_entered'].sum()
            st.metric(
                label="Total Races",
                value=f"{total_races:,}",
                delta=f"{total_races/len(overview):,.0f} avg per bot"
            )
        
        with col3:
            total_reserve = overview['reserve_balance_IGGT'].sum()
            st.metric(
                label="Total Reserve (IGGT)",
                value=f"{total_reserve:,.0f}",
                delta=f"{total_reserve/len(overview):,.0f} avg"
            )
        
        with col4:
            total_inplay = overview['in_play_balance_IGGT'].sum()
            st.metric(
                label="In-Play Exposure (IGGT)",
                value=f"{total_inplay:,.0f}",
                delta=f"{total_inplay/len(overview):,.0f} avg"
            )
        
        st.markdown("---")
        
        # Performance Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Bot Performance Comparison")
            
            # Performance bar chart
            fig_perf = px.bar(
                overview,
                x='bot_name',
                y='total_pnl_IGGT',
                title="Total P&L by Bot",
                color='total_pnl_IGGT',
                color_continuous_scale='RdYlGn'
            )
            fig_perf.update_layout(
                xaxis_title="Bot Name",
                yaxis_title="P&L (IGGT)",
                showlegend=False
            )
            st.plotly_chart(fig_perf, use_container_width=True)
        
        with col2:
            st.subheader("🏁 Races Entered")
            
            # Races bar chart
            fig_races = px.bar(
                overview,
                x='bot_name',
                y='races_entered',
                title="Total Races by Bot",
                color='races_entered',
                color_continuous_scale='Blues'
            )
            fig_races.update_layout(
                xaxis_title="Bot Name",
                yaxis_title="Number of Races",
                showlegend=False
            )
            st.plotly_chart(fig_races, use_container_width=True)
        
        # Balance Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Balance Analysis")
            
            # Reserve vs In-Play
            fig_balance = go.Figure()
            fig_balance.add_trace(go.Bar(
                name='Reserve Balance',
                x=overview['bot_name'],
                y=overview['reserve_balance_IGGT'],
                marker_color='lightblue'
            ))
            fig_balance.add_trace(go.Bar(
                name='In-Play Balance',
                x=overview['bot_name'],
                y=overview['in_play_balance_IGGT'],
                marker_color='orange'
            ))
            
            fig_balance.update_layout(
                title="Reserve vs In-Play Balances",
                xaxis_title="Bot Name",
                yaxis_title="Balance (IGGT)",
                barmode='group'
            )
            st.plotly_chart(fig_balance, use_container_width=True)
        
        with col2:
            st.subheader("📈 Performance Efficiency")
            
            # P&L per race
            overview['pnl_per_race'] = overview['total_pnl_IGGT'] / overview['races_entered'].replace(0, 1)
            
            fig_efficiency = px.scatter(
                overview,
                x='races_entered',
                y='total_pnl_IGGT',
                size='pnl_per_race',
                hover_name='bot_name',
                title="P&L vs Races (Bubble Size = P&L per Race)",
                color='total_pnl_IGGT',
                color_continuous_scale='RdYlGn'
            )
            fig_efficiency.update_layout(
                xaxis_title="Total Races",
                yaxis_title="Total P&L (IGGT)"
            )
            st.plotly_chart(fig_efficiency, use_container_width=True)
        
        # Time Series Analysis
        if not data['daily_pnl'].empty:
            st.subheader("📅 Daily Performance Trends")
            
            # Prepare daily data
            daily_data = data['daily_pnl'].copy()
            daily_data['bot_name'] = daily_data['user_id'].map(BOT_NAMES)
            daily_data['date'] = pd.to_datetime(daily_data['date'])
            
            # Daily trend line chart
            fig_trend = px.line(
                daily_data,
                x='date',
                y='daily_pnl_IGGT',
                color='bot_name',
                title="Daily P&L Trends by Bot"
            )
            fig_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Daily P&L (IGGT)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # Detailed Data Table
        st.subheader("📋 Detailed Bot Performance")
        
        # Prepare detailed table
        detailed_table = overview[['bot_name', 'user_id', 'total_pnl_IGGT', 'reserve_balance_IGGT', 
                                 'in_play_balance_IGGT', 'races_entered']].copy()
        detailed_table.columns = ['Bot Name', 'User ID', 'Total P&L (IGGT)', 'Reserve Balance (IGGT)', 
                                 'In-Play Balance (IGGT)', 'Total Races']
        
        # Add performance rating
        detailed_table['Performance Rating'] = detailed_table['Total P&L (IGGT)'].apply(
            lambda x: '🟢 Excellent' if x > 3000 else '🟡 Good' if x > 2000 else '🔴 Needs Attention'
        )
        
        st.dataframe(detailed_table, use_container_width=True)
        
        # Download buttons
        st.subheader("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = detailed_table.to_csv(index=False)
            st.download_button(
                label="Download CSV Report",
                data=csv_data,
                file_name=f"bot_performance_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown(
            f"<div style='text-align: center; color: gray;'>"
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Internal Use Only - Bot Performance Tracking"
            f"</div>",
            unsafe_allow_html=True
        )
    
    else:
        st.error("❌ Unable to load bot performance data. Please check database connection.")

if __name__ == "__main__":
    main()
