# Arizona PI Debugging Session - August 2024

## **Session Overview**
This document tracks the debugging session for a discrepancy in Performance Index (PI) calculations for Arizona vs Seattle Week 16, 2019. The manual calculation shows PI ≈ 0.70, but the computed table shows PI ≈ -0.026.

## **Background Context**

### **Recent Database Improvements**
- ✅ **Enhanced Free Agent Collection**: Increased from 100 to 800 free agents per position
- ✅ **Data Completeness**: Now includes previously missing players like Malik Turner
- ✅ **Database Rebuild**: Complete rebuild for 2019-2024 with improved data
- ✅ **Defense Tables**: Rebuilt defense weekly stats and defense adjusted PI tables

### **The Original Issue**
- **Problem**: Seattle Week 16, 2019 WR receiving yards were incomplete (33 yards vs expected 56+)
- **Root Cause**: Malik Turner was missing from the dataset due to limited free agent fetching
- **Solution**: Increased free agent fetch size to 800 per position
- **Result**: Now have complete data with Malik Turner included

## **Current Investigation: PI Calculation Discrepancy**

### **The Discrepancy**
- **Manual Calculation**: PI = 0.702 (Arizona performed very well)
- **Computed Table Value**: PI = -0.026 (very close to zero)
- **Difference**: 0.728 (significant discrepancy)

### **Manual Calculation Method**
```python
# Our verification script approach:
seattle_2019 = df[(df['nfl_team'] == 'SEA') & (df['year'] == 2019) & (df['position'] == 'WR')]
seattle_weekly_wr = seattle_2019.groupby('week')['receivingYards'].sum()

# Leave-one-out baseline (excluding Week 16)
baseline_excluding_week16 = seattle_weekly_wr[seattle_weekly_wr['week'] != 16]['receivingYardsWR'].mean()
# Result: 187.80 yards

# Actual Week 16 performance
actual_week16 = seattle_weekly_wr[seattle_weekly_wr['week'] == 16]['receivingYardsWR'].iloc[0]
# Result: 56 yards

# PI calculation
pi = (baseline_excluding_week16 - actual_week16) / baseline_excluding_week16
pi = (187.80 - 56) / 187.80 = 0.702
```

### **Computed Calculation Method**
```python
# From analysis/compute_defense_adjusted_metrics.py:
def offense_leave_one_out_baseline(df: pd.DataFrame, stat_cols):
    # For each game, calculate baseline excluding that specific game
    for idx, row in df_copy.iterrows():
        year = row['year']
        offense_team = row['offense_team']
        week = row['week']
        
        # Get all other games for this offense team in this year (excluding current game)
        other_games = df_copy[
            (df_copy['year'] == year) & 
            (df_copy['offense_team'] == offense_team) & 
            ~((df_copy['year'] == year) & (df_copy['offense_team'] == offense_team) & (df_copy['week'] == week))
        ]
        
        # Calculate mean for each stat column
        for c in stat_cols:
            mean_val = other_games[c].mean()
            df_copy.at[idx, f"expected_{c}"] = mean_val
```

## **Key Data Points**

### **Seattle 2019 WR Receiving Yards (Complete Data)**
```
Week  1: 133 yards
Week  2: 194 yards
Week  3: 299 yards
Week  4: 116 yards
Week  5: 141 yards
Week  6: 209 yards
Week  7: 212 yards
Week  8: 157 yards
Week  9: 293 yards
Week 10: 158 yards
Week 12: 147 yards
Week 13: 156 yards
Week 14: 180 yards
Week 15: 249 yards
Week 16: 56 yards  ← Target game
Week 17: 173 yards
```

### **Arizona 2019 Defensive Performance**
```
Week  1 vs DET: 202 yards
Week  2 vs BAL: 102 yards
Week  3 vs CAR: 149 yards
Week  4 vs SEA: 116 yards
Week  5 vs CIN: 200 yards
Week  6 vs ATL: 191 yards
Week  7 vs NYG: 176 yards
Week  8 vs NO:  180 yards
Week  9 vs SF:  180 yards
Week 10 vs TB:  206 yards
Week 11 vs SF:  260 yards
Week 13 vs LAR: 300 yards
Week 14 vs PIT: 115 yards
Week 15 vs CLE: 122 yards
Week 16 vs SEA: 56 yards  ← Target game
Week 17 vs LAR: 206 yards
```

## **Debug Scripts Created**

### **1. `utils/verify_arizona_pi.py`**
- Verifies manual PI calculation using Seattle's offensive baseline
- Shows PI = 0.702 (Arizona performed well)

### **2. `utils/debug_computed_pi.py`**
- Simulates the exact computed PI calculation logic
- Shows PI = 0.702 (should match manual calculation)
- But table shows PI = -0.026 (discrepancy)

### **3. `utils/test_malik_turner_complete.py`**
- Verifies Malik Turner is now included in the dataset
- Confirms Seattle Week 16, 2019 total WR yards = 56

## **Current Working Files**

### **Data Files**
- `data/fantasy_weekly_stats_complete.parquet` - Complete player stats (74,991 rows)
- `data/defense_weekly_stats.parquet` - Defense weekly stats (43,325 rows)
- `data/defense_adjusted_pi.parquet` - Defense adjusted PI (193 defense team/year combinations)

### **Analysis Files**
- `analysis/compute_defense_adjusted_metrics.py` - PI calculation logic
- `utils/debug_computed_pi.py` - Debug script for computed PI
- `utils/verify_arizona_pi.py` - Manual PI verification

### **Documentation**
- `ai/context/DATABASE_BUILD_COMPLETE.md` - Database build guide
- `ai/context/DEFENSE_PI_BUILD_COMPLETE.md` - Defense PI build guide

## **Next Steps for Investigation**

### **Immediate Tasks**
1. **Trace the PI calculation logic** in `compute_defense_adjusted_metrics.py`
2. **Check if there's a different baseline being used** (defensive vs offensive)
3. **Verify the data flow** from defense weekly stats to PI calculation
4. **Check for any data filtering or preprocessing** that might affect the calculation

### **Potential Issues to Investigate**
1. **Baseline Method**: Is it using offensive baseline (Seattle's performance) or defensive baseline (Arizona's performance)?
2. **Data Filtering**: Are there any filters removing certain games from the baseline calculation?
3. **PI Formula**: Is the PI formula being applied correctly?
4. **Data Type Issues**: Are there any numerical precision issues?

### **Debugging Approach**
1. **Add logging** to the PI calculation to see exactly what baseline is being used
2. **Compare intermediate values** between manual and computed calculations
3. **Check if the issue is specific to this game** or affects other games too
4. **Verify the defense weekly stats** are being processed correctly

## **Expected Outcome**
The goal is to understand why the computed PI calculation produces PI = -0.026 instead of the expected PI = 0.702, and to ensure the PI calculation logic is working correctly for all games.

## **Environment Setup**
- **Python**: Virtual environment with required packages
- **Working Directory**: `/Users/kellar/Develop/Projects/fantasy-football`
- **Key Dependencies**: pandas, numpy, pymongo, espn_api
- **Data Sources**: ESPN Fantasy API, ESPN Gamelog API, MongoDB

---

**Last Updated**: August 2024  
**Status**: Active investigation - PI calculation discrepancy identified  
**Next Session**: Continue debugging the computed PI calculation logic
