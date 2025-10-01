import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Bot Performance Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

@st.cache_data
def load_bot_data_from_json():
    """Load bot performance data from JSON files"""
    try:
        # Check if data file exists
        if not os.path.exists('bot_data.json'):
            return None, "No data file found. Please run the manual updater first."
        
        # Load data
        with open('bot_data.json', 'r') as f:
            data = json.load(f)
        
        # Check if data is empty
        if not data or not data.get('total_pnl'):
            return None, "No data available in the file."
        
        return data, None
        
    except Exception as e:
        return None, f"Error loading data: {str(e)}"

def create_performance_overview(data):
    """Create performance overview metrics"""
    if not data:
        return pd.DataFrame()
    
    overview_data = []
    
    for record in data['total_pnl']:
        user_id = record['user_id']
        bot_name = BOT_NAMES.get(user_id, f"Bot {user_id}")
        total_pnl = record['total_pnl_IGGT']
        
        # Get other metrics
        reserve = next((r['reserve_balance_IGGT'] for r in data['reserve_balance'] if r['user_id'] == user_id), 0)
        in_play = next((r['in_play_balance_IGGT'] for r in data['in_play_balance'] if r['user_id'] == user_id), 0)
        races = next((r['races_entered'] for r in data['races_entered'] if r['user_id'] == user_id), 0)
        
        overview_data.append({
            'user_id': user_id,
            'bot_name': bot_name,
            'total_pnl_IGGT': total_pnl,
            'reserve_balance_IGGT': reserve,
            'in_play_balance_IGGT': in_play,
            'races_entered': races,
            'pnl_per_race': total_pnl / races if races > 0 else 0
        })
    
    return pd.DataFrame(overview_data)

def main():
    st.title("🤖 Bot Performance Dashboard")
    
    # Sidebar
    st.sidebar.title("📊 Dashboard Controls")
    
    # Check last update time
    if os.path.exists('last_updated.txt'):
        with open('last_updated.txt', 'r') as f:
            last_update = f.read().strip()
        st.sidebar.info(f"📅 Last Updated: {datetime.fromisoformat(last_update).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.sidebar.warning("⚠️ No update timestamp found")
    
    # Manual update button
    if st.sidebar.button("🔄 Update Data Now"):
        st.sidebar.info("Run: python manual_report_updater.py")
    
    # Load data
    data, error = load_bot_data_from_json()
    
    if error:
        st.error(f"❌ {error}")
        st.info("💡 Please run the manual updater: `python manual_report_updater.py`")
        return
    
    if not data:
        st.warning("⚠️ No data available")
        return
    
    overview = create_performance_overview(data)
    
    if overview.empty:
        st.warning("⚠️ No performance data available")
        return
    
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
        
        # P&L per race scatter plot
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
    if data.get('daily_pnl'):
        st.subheader("📅 Daily Performance Trends")
        
        # Prepare daily data
        daily_data = pd.DataFrame(data['daily_pnl'])
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
        if st.button("🔄 Refresh Dashboard"):
            st.cache_data.clear()
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: gray;'>"
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Internal Use Only - Bot Performance Tracking | "
        f"Data Source: Static Files (Manual Update Required)"
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
