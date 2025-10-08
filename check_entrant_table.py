import pandas as pd
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_config():
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME')
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return DATABASE_URL

try:
    DATABASE_URL = get_database_config()
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("=" * 80)
    print("CHECKING full_WC_entrant TABLE (7.3M records!)")
    print("=" * 80)
    
    # Get structure
    cols = inspector.get_columns('full_WC_entrant')
    print("\nColumns:")
    for col in cols:
        print(f"  {col['name']:<30} {str(col['type']):<20}")
    
    # Check for Tayport
    print("\n" + "=" * 80)
    print("SEARCHING FOR TAYPORT IN ENTRANT TABLE")
    print("=" * 80)
    
    query1 = """
        SELECT COUNT(*) as count
        FROM full_WC_entrant
        WHERE user_horse_id = 274848022531
    """
    count = pd.read_sql(query1, engine)
    print(f"\nTayport race entries: {count.iloc[0]['count']}")
    
    # Get Tayport's race entries
    query2 = """
        SELECT *
        FROM full_WC_entrant
        WHERE user_horse_id = 274848022531
        LIMIT 10
    """
    tayport_entries = pd.read_sql(query2, engine)
    
    if not tayport_entries.empty:
        print("\nTayport's race entries (sample):")
        print(tayport_entries.transpose())
        
        # Now join with event to get distance/surface!
        print("\n" + "=" * 80)
        print("JOINING ENTRANT WITH EVENT TO GET DISTANCE/SURFACE!")
        print("=" * 80)
        
        query3 = """
            SELECT 
                ent.user_horse_id,
                ent.user_id,
                ent.event_id,
                ent.final_position,
                ent.stall,
                e.distance,
                CASE 
                    WHEN e.distance = 1 THEN '1000m (5f Sprint)'
                    WHEN e.distance = 2 THEN '1200m (6f Sprint)'
                    WHEN e.distance = 3 THEN '1400m (7f Mile)'
                    WHEN e.distance = 4 THEN '1600m (8f Mile)'
                    WHEN e.distance = 5 THEN '1800m (9f Mile)'
                    WHEN e.distance = 6 THEN '2000m (10f Marathon)'
                END as distance_name,
                e.surface,
                CASE 
                    WHEN e.surface = 1 THEN 'Dirt'
                    WHEN e.surface = 2 THEN 'Turf'
                    ELSE 'Unknown'
                END as surface_name,
                e.weather,
                e.`condition`,
                e.track_name,
                ent.Zone
            FROM full_WC_entrant ent
            INNER JOIN full_WC_event e ON ent.event_id = e._id AND ent.Zone = e.Zone
            WHERE ent.user_horse_id = 274848022531
            ORDER BY ent.event_id DESC
        """
        tayport_races_full = pd.read_sql(query3, engine)
        
        print(f"\nFOUND {len(tayport_races_full)} COMPLETE RACE RECORDS FOR TAYPORT!")
        
        print("\n" + "=" * 80)
        print("TAYPORT - DISTANCE PERFORMANCE")
        print("=" * 80)
        
        # Group by distance
        dist_perf = tayport_races_full.groupby(['distance', 'distance_name']).agg({
            'event_id': 'count',
            'final_position': ['mean', 'min'],
        }).reset_index()
        dist_perf.columns = ['distance', 'distance_name', 'races', 'avg_position', 'best_position']
        
        # Add wins
        wins_by_dist = tayport_races_full[tayport_races_full['final_position'] == 1].groupby('distance').size()
        dist_perf['wins'] = dist_perf['distance'].map(wins_by_dist).fillna(0)
        
        # Add top 3
        top3_by_dist = tayport_races_full[tayport_races_full['final_position'] <= 3].groupby('distance').size()
        dist_perf['top_3'] = dist_perf['distance'].map(top3_by_dist).fillna(0)
        
        print(f"\n{'Distance':<25} {'Races':<7} {'Avg Pos':<9} {'Best':<6} {'Wins':<6} {'Top 3':<7}")
        print("-" * 80)
        for _, row in dist_perf.iterrows():
            print(f"{row['distance_name']:<25} {int(row['races']):<7} {row['avg_position']:>7.2f}  "
                  f"{int(row['best_position']):<6} {int(row['wins']):<6} {int(row['top_3']):<7}")
        
        # Surface performance
        print("\n" + "=" * 80)
        print("TAYPORT - SURFACE PERFORMANCE (DIRT vs TURF)")
        print("=" * 80)
        
        surf_perf = tayport_races_full.groupby(['surface', 'surface_name']).agg({
            'event_id': 'count',
            'final_position': ['mean', 'min'],
        }).reset_index()
        surf_perf.columns = ['surface', 'surface_name', 'races', 'avg_position', 'best_position']
        
        # Add wins
        wins_by_surf = tayport_races_full[tayport_races_full['final_position'] == 1].groupby('surface').size()
        surf_perf['wins'] = surf_perf['surface'].map(wins_by_surf).fillna(0)
        
        # Add top 3
        top3_by_surf = tayport_races_full[tayport_races_full['final_position'] <= 3].groupby('surface').size()
        surf_perf['top_3'] = surf_perf['surface'].map(top3_by_surf).fillna(0)
        
        print(f"\n{'Surface':<15} {'Races':<7} {'Avg Pos':<9} {'Best':<6} {'Wins':<6} {'Top 3':<7}")
        print("-" * 80)
        for _, row in surf_perf.iterrows():
            print(f"{row['surface_name']:<15} {int(row['races']):<7} {row['avg_position']:>7.2f}  "
                  f"{int(row['best_position']):<6} {int(row['wins']):<6} {int(row['top_3']):<7}")
        
        # Sample races
        print("\n" + "=" * 80)
        print("SAMPLE RACES (Latest 10):")
        print("=" * 80)
        sample = tayport_races_full.head(10)[['distance_name', 'surface_name', 'final_position', 'track_name']]
        print(sample.to_string(index=False))
        
    else:
        print("No entries found for Tayport")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

