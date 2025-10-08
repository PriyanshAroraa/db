# 🐴 Horse Performance Data - Database Schema Documentation

## Overview
This document explains where to find horse-level performance data for bot optimization analysis.

---

## 📊 DATA SOURCES MAP

### 1. **HORSE INVENTORY** - Basic Horse Information

**Table:** `player_horse`  
**Key:** `user_id`, `_id` (horse_id)

**Contains:**
- Horse name, grade, bloodline, generation
- Trainer assignment
- Gender, age, status
- Link IDs: `user_horse_economy_id`, `user_horse_genome_id`, `orig_ghuid`

**Query Example:**
```sql
SELECT user_id, _id, name, grade, bloodline, generation, trainer_id
FROM player_horse
WHERE user_id IN (10111491, 10211493, ...)
```

---

### 2. **HORSE PERFORMANCE SUMMARY** - Overall Stats

**Table:** `full_WC_horse_snapshot`  
**Key:** `user_id`, `user_horse_id`

**Contains:**
- Total races, wins, shows, places
- Average rating
- Speed, stamina, acceleration stats
- Career earnings
- Final position in each race

**Query Example:**
```sql
SELECT user_id, user_horse_id, name,
       COUNT(*) as total_races,
       AVG(final_position) as avg_position,
       SUM(CASE WHEN final_position = 1 THEN 1 ELSE 0 END) as wins
FROM full_WC_horse_snapshot
WHERE user_id = 10111491
GROUP BY user_id, user_horse_id, name
```

**CRITICAL:** Each row is a snapshot from one race  
**JOIN KEY:** `user_horse_id` = unique identifier per horse

---

### 3. **RACE DISTANCE DATA** - Which distances each horse races at

**Method:** Join `full_WC_horse_snapshot` → `full_WC_entrant` → `full_WC_event`

**Chain:**
1. `full_WC_horse_snapshot._id` = `horse_snapshot_id`
2. `full_WC_entrant.horse_snapshot_id` → `full_WC_entrant.event_id`
3. `full_WC_event._id` = `event_id` → Has `distance` column!

**Distance Codes:**
- `1` = 1000m (5 furlongs) - **Sprint**
- `2` = 1200m (6 furlongs) - **Sprint**
- `3` = 1400m (7 furlongs) - **Mile**
- `4` = 1600m (8 furlongs) - **Mile**
- `5` = 1800m (9 furlongs) - **Mile**
- `6` = 2000m (10 furlongs) - **Marathon**

**Query Example:**
```sql
SELECT 
    hs.user_horse_id,
    hs.name,
    e.distance,
    hs.final_position,
    COUNT(*) as races
FROM full_WC_horse_snapshot hs
INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id 
    AND hs.Zone = ent.Zone
INNER JOIN full_WC_event e ON ent.event_id = e._id 
    AND ent.Zone = e.Zone
WHERE hs.user_id = 10111491
GROUP BY hs.user_horse_id, hs.name, e.distance
```

---

### 4. **RACE SURFACE DATA** - Dirt vs Turf Performance

**Same Tables:** `full_WC_horse_snapshot` → `full_WC_entrant` → `full_WC_event`

**Surface Codes:**
- `1` = **Dirt**
- `2` = **Turf**

**Also Available:**
- `weather` - Weather conditions
- `condition` - Track condition (fast, muddy, etc.)

**Query Example:**
```sql
SELECT 
    hs.user_horse_id,
    hs.name,
    e.surface,
    CASE 
        WHEN e.surface = 1 THEN 'Dirt'
        WHEN e.surface = 2 THEN 'Turf'
    END as surface_name,
    AVG(hs.final_position) as avg_position,
    COUNT(*) as races
FROM full_WC_horse_snapshot hs
INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id
INNER JOIN full_WC_event e ON ent.event_id = e._id
GROUP BY hs.user_horse_id, hs.name, e.surface
```

---

### 5. **STABLE COMPOSITION** - Overview per Bot

**Table:** `player_horse`

**Metrics:**
- Total horses per bot
- Grade distribution (Grade 1, 2, 3)
- Bloodline distribution
- Average generation

---

### 6. **AGGREGATE RACE DATA** - Bot-Level Stats

**Tables:**
- `player_daily_fact_distance` - Daily distance breakdown
- `player_daily_fact_grade` - Daily grade breakdown
- `player_daily_fact_track` - Daily track preferences

**Use for:** Bot-level patterns, not horse-specific

---

### 7. **FINANCIAL DATA** - P&L Tracking

**Table:** `player_token_transaction`  
**Key:** `user_id`, `source_trx_id` (links to race event)

**Contains:**
- Amount won/lost (divide by 1,000,000 for IGGT)
- Transaction type (ctx_type = 1 for races)
- Timestamp

---

### 8. **TRAITS & ATTRIBUTES** - Horse Characteristics

**Current Status:** ❌ **NOT AVAILABLE FOR BOTS**

**Tables checked (no bot data):**
- `full_OC_user_horse_genome` - Empty for bots
- `full_OC_user_horse_economy` - Empty for bots
- `full_OC_user_horse_buff` - Empty for bots
- `full_OC_user_equipment` - Empty for bots

**Alternative:**
- Infer from performance stats (stamina, speed, acceleration)
- Calculate from actual race results

---

## 🔑 KEY TABLE RELATIONSHIPS

```
player_horse (basic info)
    └─> _id = horse_id

full_WC_horse_snapshot (performance snapshots)
    ├─> user_horse_id (matches across snapshots)
    └─> _id = snapshot_id
            └─> full_WC_entrant.horse_snapshot_id
                    └─> event_id
                            └─> full_WC_event (has distance, surface, weather!)

player_token_transaction (P&L)
    └─> source_trx_id (may link to race/event)
```

---

## 📝 CRITICAL NOTES

### Zone Consistency
- **MUST match Zone** when joining tables
- Each record has a `Zone` field (WC1, WC2, WC5, etc.)
- Join condition: `AND hs.Zone = ent.Zone`

### Snapshot = Race Instance
- Each row in `full_WC_horse_snapshot` = one race
- Multiple snapshots per `user_horse_id` = multiple races
- Group by `user_horse_id` to get horse-level stats

### Missing Data
- Some snapshots may not have entrant records (race incomplete/cancelled)
- Only 19/25 Tayport races found in entrant table
- This is normal - not all snapshots become final races

---

## 🎯 OPTIMIZATION QUERIES

### Get Horse Distance Specialization
```sql
SELECT 
    hs.name,
    CASE 
        WHEN e.distance IN (1, 2) THEN 'Sprint'
        WHEN e.distance IN (3, 4, 5) THEN 'Mile'
        WHEN e.distance = 6 THEN 'Marathon'
    END as category,
    COUNT(*) as races,
    AVG(hs.final_position) as avg_position,
    SUM(CASE WHEN hs.final_position = 1 THEN 1 ELSE 0 END) as wins
FROM full_WC_horse_snapshot hs
INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id AND hs.Zone = ent.Zone
INNER JOIN full_WC_event e ON ent.event_id = e._id AND ent.Zone = e.Zone
WHERE hs.user_id = 10111491
GROUP BY hs.user_horse_id, hs.name, category
```

### Get Surface Preference
```sql
SELECT 
    hs.name,
    CASE WHEN e.surface = 1 THEN 'Dirt' ELSE 'Turf' END as surface,
    COUNT(*) as races,
    AVG(hs.final_position) as avg_position
FROM full_WC_horse_snapshot hs
INNER JOIN full_WC_entrant ent ON hs._id = ent.horse_snapshot_id AND hs.Zone = ent.Zone
INNER JOIN full_WC_event e ON ent.event_id = e._id AND ent.Zone = e.Zone
WHERE hs.user_id = 10111491
    AND e.surface IN (1, 2)
GROUP BY hs.user_horse_id, hs.name, surface
```

---

## 📈 PERFORMANCE ANALYSIS WORKFLOW

1. **Get horse roster** from `player_horse`
2. **Get performance summary** from `full_WC_horse_snapshot` (grouped)
3. **Join with entrant + event** to get distance/surface breakdown
4. **Calculate specialization** from aggregated stats
5. **Identify optimization opportunities** (wrong distances, wrong competition level)

---

## 🚀 READY FOR JONATHAN'S OPTIMIZATION MODEL

This data structure enables:
- **Multivariate analysis** of performance factors
- **Horse specialization** identification (sprinter/miler/marathoner)
- **Surface preference** analysis (dirt vs turf)
- **Optimal race selection** recommendations
- **Stable composition** optimization

**Jonathan's Quote:** "We really need to be at a much more granular level to optimize... at the horse level, at the race level, at the tactics"

**Status:** ✅ **WE NOW HAVE THIS DATA!**

