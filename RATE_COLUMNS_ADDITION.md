# Rate Columns Addition to Comprehensive Breakdown Table

## Overview

Added rate columns to the Comprehensive Breakdown Table in the Load Factor Rate Analysis tool, providing complete transparency on all energy and demand rates used in the calculations.

## Changes Made

### New Columns Added

#### 1. Energy Period Rate Columns
For **every** energy rate period in the tariff:
- **Column Name:** `[Period Name] Rate ($/kWh)`
- **Format:** 4 decimal places with $ prefix (e.g., "$0.1234")
- **Value:** Total rate including base rate + adjustments
- **Location:** Between `[Period Name] (kWh)` and `[Period Name] Cost ($)` columns

**Example:**
- Peak (kWh)
- **Peak Rate ($/kWh)** ← NEW
- Peak Cost ($)

#### 2. TOU Demand Period Rate Columns
For **every** TOU demand period in the tariff:
- **Column Name:** `[Period Name] Rate ($/kW)`
- **Format:** 2 decimal places with $ prefix (e.g., "$12.34")
- **Value:** Total rate including base rate + adjustments
- **Location:** Between `[Period Name] Demand (kW)` and `[Period Name] Demand Cost ($)` columns

**Example:**
- Summer Peak Demand (kW)
- **Summer Peak Rate ($/kW)** ← NEW
- Summer Peak Demand Cost ($)

#### 3. Flat Demand Rate Column
For flat monthly demand (if applicable):
- **Column Name:** `Flat Demand Rate ($/kW)`
- **Format:** 2 decimal places with $ prefix (e.g., "$12.34")
- **Value:** Total rate including base rate + adjustments (varies by month for some tariffs)
- **Location:** Between `Flat Demand (kW)` and `Flat Demand Cost ($)` columns

**Example:**
- Flat Demand (kW)
- **Flat Demand Rate ($/kW)** ← NEW
- Flat Demand Cost ($)

## Key Features

### 1. Always Displayed
Rate columns are **always** shown for all periods, regardless of:
- Whether the period is active in the selected month
- Whether energy is allocated to that period
- Whether demand is specified for that period

This ensures complete rate transparency and allows users to see the full tariff structure at a glance.

### 2. Total Rates
All rate columns display **total rates** (base rate + adjustments), which are the actual rates used in cost calculations. This ensures:
- Consistency with displayed costs
- Transparency in calculations
- Easy verification of results

### 3. Proper Formatting
- **Energy rates:** 4 decimal places for precision ($/kWh)
- **Demand rates:** 2 decimal places ($/kW)
- All rates shown with $ prefix for clarity
- Small column width to keep table compact

## Technical Implementation

### Code Changes

#### `_calculate_comprehensive_load_factor_breakdown()` Function

**Energy Period Rates:**
```python
# Get rate for this period (always show rate even if not used)
rate = energy_structure[period_idx][0].get('rate', 0)
adj = energy_structure[period_idx][0].get('adj', 0)
total_rate = rate + adj

comprehensive_row[f'{period_label} (kWh)'] = period_energy
comprehensive_row[f'{period_label} Rate ($/kWh)'] = total_rate  # NEW
comprehensive_row[f'{period_label} Cost ($)'] = period_cost
```

**TOU Demand Period Rates:**
```python
# Get rate for this period (always show rate even if not used)
rate = demand_structure[i][0].get('rate', 0)
adj = demand_structure[i][0].get('adj', 0)
total_rate = rate + adj

comprehensive_row[f'{period_label} Demand (kW)'] = demand_value
comprehensive_row[f'{period_label} Rate ($/kW)'] = total_rate  # NEW
comprehensive_row[f'{period_label} Demand Cost ($)'] = demand_cost
```

**Flat Demand Rate:**
```python
# Get rate (always show rate)
rate = flat_structure.get('rate', 0)
adj = flat_structure.get('adj', 0)
total_rate = rate + adj

comprehensive_row['Flat Demand (kW)'] = demand_value
comprehensive_row['Flat Demand Rate ($/kW)'] = total_rate  # NEW
comprehensive_row['Flat Demand Cost ($)'] = demand_cost
```

#### `_display_load_factor_results()` Function

Added column configuration for all rate columns:

```python
# Energy period rate columns
column_config[f'{period_label} Rate ($/kWh)'] = st.column_config.NumberColumn(
    f'{period_label} Rate ($/kWh)', format="$%.4f", width="small"
)

# TOU demand rate columns
column_config[f'{period_label} Rate ($/kW)'] = st.column_config.NumberColumn(
    f'{period_label} Rate ($/kW)', format="$%.2f", width="small"
)

# Flat demand rate column
column_config['Flat Demand Rate ($/kW)'] = st.column_config.NumberColumn(
    'Flat Demand Rate ($/kW)', format="$%.2f", width="small"
)
```

## User Benefits

### 1. Complete Transparency
Users can now see:
- Exact rates for all energy periods
- Exact rates for all demand periods
- How rates compare across different periods
- Which periods have higher/lower rates

### 2. Easy Verification
Users can easily verify that:
- Costs = kWh × Rate (for energy)
- Costs = kW × Rate (for demand)
- Calculations are correct
- Expected rates are being applied

### 3. Rate Comparison
Users can:
- Compare energy rates across TOU periods
- Compare demand rates across TOU periods
- Identify highest/lowest rate periods
- Understand rate structure at a glance

### 4. Better Analysis
With rate columns visible, users can:
- Calculate custom scenarios in Excel after export
- Understand cost drivers (high rates vs. high consumption)
- Identify opportunities for load shifting to lower-rate periods
- Make informed operational decisions

### 5. Documentation
The comprehensive table now includes:
- All inputs (energy, demand)
- All rates (energy, demand)
- All costs (energy, demand)
- All summary totals
- Complete information for reporting and compliance

## Example Table Structure

### Before (3 columns per energy period):
- Peak (kWh) | Peak Cost ($)
- Off-Peak (kWh) | Off-Peak Cost ($)

### After (3 columns per energy period):
- Peak (kWh) | **Peak Rate ($/kWh)** | Peak Cost ($)
- Off-Peak (kWh) | **Off-Peak Rate ($/kWh)** | Off-Peak Cost ($)

### Example Data:
| Load Factor | Peak (kWh) | **Peak Rate ($/kWh)** | Peak Cost ($) | Off-Peak (kWh) | **Off-Peak Rate ($/kWh)** | Off-Peak Cost ($) |
|------------|-----------|---------------------|--------------|---------------|-------------------------|-----------------|
| 50%        | 18,600    | **$0.2500**         | $4,650.00    | 18,600        | **$0.1200**             | $2,232.00       |
| 100%       | 37,200    | **$0.2500**         | $9,300.00    | 37,200        | **$0.1200**             | $4,464.00       |

## Data Consistency

### Rate Calculation
All rates are calculated using the same logic as cost calculations:
```python
rate = structure[idx][0].get('rate', 0)
adj = structure[idx][0].get('adj', 0)
total_rate = rate + adj
```

### Verification
Users can verify calculations:
- **Energy:** Peak Cost ($4,650) = Peak (kWh) (18,600) × Peak Rate ($0.2500) ✓
- **Demand:** Demand Cost ($1,234) = Demand (kW) (100) × Demand Rate ($12.34) ✓

### Export Compatibility
Rate columns are included in Excel exports:
- Proper numeric formatting preserved
- Can create custom formulas using rate columns
- Verify calculations in external tools

## Files Modified

1. **src/components/cost_calculator.py**
   - Modified `_calculate_comprehensive_load_factor_breakdown()` to add rate columns to comprehensive_row dictionary
   - Modified `_display_load_factor_results()` to add rate column configurations
   - No changes to calculation logic

2. **LOAD_FACTOR_BREAKDOWN_TABLE_FEATURE.md**
   - Updated column descriptions to include rate columns
   - Added notes about rates always being displayed

3. **COMPREHENSIVE_BREAKDOWN_TABLE_UPDATE.md**
   - Updated table structure section to include rate columns
   - Updated example scenarios to show rate columns

4. **EXCEL_EXPORT_FEATURE.md**
   - Updated exported columns list to include rate columns

5. **RATE_COLUMNS_ADDITION.md** (new)
   - This comprehensive documentation of the rate columns addition

## Testing Validation

✅ No linter errors
✅ Rate columns added to data structure
✅ Rate columns added to column configuration
✅ Proper formatting (4 decimals for energy, 2 for demand)
✅ Documentation updated

## Notes

- Rates are shown for **all** periods, even if not active in the selected month
- Rates include both base rate and adjustments (total rate)
- Rate columns are positioned between quantity (kWh/kW) and cost ($) columns for logical flow
- For tariffs with seasonal rates, the appropriate rate for the selected month is shown
- Flat demand rate may vary by month for some tariffs (uses correct tier based on selected month)

## Summary

The addition of rate columns to the Comprehensive Breakdown Table provides complete transparency into all aspects of the load factor analysis. Users can now see not only how much energy/demand and what it costs, but also the exact rates being applied. This enables better verification, analysis, and understanding of utility rate structures.

