# Annual Load Factor Analysis Feature

## Overview

Extended the Load Factor Rate Analysis Tool to support full-year analysis in addition to single-month analysis. This enhancement allows users to calculate effective utility rates across an entire year, properly accounting for monthly variations in TOU schedules, flat demand tiers, and hour distributions.

## Key Features

### 1. Analysis Period Selection

Users can now choose between:
- **Single Month**: Analyze effective rates for one specific month
- **Full Year**: Calculate annual effective rates accounting for all 12 months

### 2. Monthly Variability Handling

The annual analysis properly accounts for:

#### TOU Demand Periods
- Only charges for demand in months when each period is active
- Displays the number of months each demand period is applicable
- Properly aggregates costs across active months

#### Flat Demand Charges
- Handles tariffs with multiple flat demand rate tiers (e.g., summer vs winter rates)
- Separates each unique tier with its own set of columns
- Shows the number of months each tier applies
- Calculates costs based on tier-specific rates and month counts

#### Energy Periods
- Uses annual hour percentages to calculate max physical load factor
- Renormalizes energy distribution month-by-month for active periods
- Properly accounts for periods that are only active in certain seasons

#### Hours and Calendar
- Uses actual days in each month (28-31 days)
- Accounts for varying weekday/weekend distributions
- Properly calculates annual energy totals

## Implementation Details

### New Functions

#### `_calculate_annual_period_hour_percentages()`
Calculates what percentage of the year's hours each energy period represents, accounting for the actual calendar distribution across all 12 months.

```python
def _calculate_annual_period_hour_percentages(tariff_data: Dict[str, Any], year: int = 2024) -> Dict[int, float]:
    """
    Calculate what percentage of the year's hours each energy period is present.
    
    Returns:
        Dictionary mapping period index to percentage of year (0-100)
    """
```

#### `_get_active_demand_periods_for_year()`
Determines which demand periods are present anywhere in the year and counts how many months each is active.

```python
def _get_active_demand_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Returns:
        Dictionary mapping period index to number of months it's active
    """
```

#### `_get_active_energy_periods_for_year()`
Determines which energy periods are present anywhere in the year and counts how many months each is active.

```python
def _get_active_energy_periods_for_year(tariff_data: Dict[str, Any]) -> Dict[int, int]:
    """
    Returns:
        Dictionary mapping period index to number of months it's active
    """
```

#### `_calculate_annual_load_factor_rates()`
Core calculation function for annual analysis. Loops through all 12 months, calculates monthly costs accounting for:
- Which periods are active each month
- Correct flat demand tier for each month
- Proper energy distribution renormalization
- Actual hours in each month

```python
def _calculate_annual_load_factor_rates(
    tariff_data: Dict[str, Any],
    demand_inputs: Dict[str, float],
    energy_percentages: Dict[str, float],
    has_tou_demand: bool,
    has_flat_demand: bool,
    demand_period_month_counts: Dict[int, int],
    energy_period_month_counts: Dict[int, int]
) -> pd.DataFrame:
    """
    Calculate effective utility rates for different load factors over a full year.
    
    Returns:
        DataFrame with annual load factor analysis results
    """
```

### Enhanced Functions

#### `_render_load_factor_analysis_tool()`
**Changes:**
- Added radio button to select "Single Month" or "Full Year"
- Conditionally shows month selector only for single month analysis
- Updates TOU demand UI to show month counts for annual analysis
- Updates flat demand UI to explain tier handling for annual analysis
- Updates energy distribution UI to show annual hour percentages and month counts
- Routes to appropriate calculation function based on analysis period

#### `_calculate_comprehensive_load_factor_breakdown()`
**Changes:**
- Added parameters for `analysis_period`, `demand_period_month_counts`, `energy_period_month_counts`
- Uses annual hour percentages for full year analysis
- **TOU Demand columns (annual):**
  - Adds "# Months" column for each demand period
  - Multiplies demand cost by number of active months
- **Flat Demand columns (annual):**
  - Creates separate column groups for each unique tier
  - Each tier group includes:
    - `Flat Demand (Tier X) # Months`
    - `Flat Demand (Tier X) Demand (kW)`
    - `Flat Demand (Tier X) Rate ($/kW)`
    - `Flat Demand (Tier X) Cost ($)`
  - Costs reflect per-tier rates multiplied by months at that tier

#### `_display_load_factor_results()`
**Changes:**
- Added parameters for `analysis_period`, `demand_period_month_counts`, `energy_period_month_counts`
- Updates caption text to explain annual analysis when applicable
- Passes new parameters to comprehensive breakdown function

## User Interface Changes

### Analysis Period Selector
```
📅 Analysis Period
○ Single Month    ● Full Year
```

### TOU Demand Inputs (Annual)
When "Full Year" is selected, demand inputs show:
```
Peak Period (3 months)
($15.50/kW)
[Input: kW]

Off-Peak Period (9 months)
($8.25/kW)
[Input: kW]
```

### Flat Demand Input (Annual)
For tariffs with multiple tiers:
```
ℹ️ This tariff has 2 different flat demand rate tiers across the year. 
Enter the same demand value for all tiers (will be applied to appropriate months).

Maximum Monthly Demand (kW)
[Input: kW]
```

### Energy Distribution (Annual)
Energy inputs show annual context:
```
Peak
📊 8.5% of year's hours
($0.1850/kWh)
[Input: %]
Help: Active in 6 months
```

### Comprehensive Breakdown Table (Annual)

**TOU Demand Section:**
```
| Summer Peak # Months | Summer Peak Demand (kW) | Summer Peak Rate ($/kW) | Summer Peak Cost ($) |
|---------------------|-------------------------|------------------------|---------------------|
| 6                   | 100.0                   | $15.50                 | $9,300.00           |

| Winter Peak # Months | Winter Peak Demand (kW) | Winter Peak Rate ($/kW) | Winter Peak Cost ($) |
|---------------------|-------------------------|------------------------|---------------------|
| 6                   | 100.0                   | $12.75                 | $7,650.00           |
```

**Flat Demand Section (Multiple Tiers):**
```
| Flat Demand (Tier 0) # Months | ... Demand (kW) | ... Rate ($/kW) | ... Cost ($) |
|-------------------------------|-----------------|-----------------|--------------|
| 6                             | 100.0           | $10.00          | $6,000.00    |

| Flat Demand (Tier 1) # Months | ... Demand (kW) | ... Rate ($/kW) | ... Cost ($) |
|-------------------------------|-----------------|-----------------|--------------|
| 6                             | 100.0           | $12.00          | $7,200.00    |
```

## Calculation Logic

### Annual Cost Calculation

For each load factor:

1. **Calculate Annual Energy:**
   ```
   For each month:
     Monthly Energy = Average Load × Hours in Month
   Annual Energy = Sum of all monthly energies
   ```

2. **Calculate Annual Demand Charges:**
   ```
   TOU Demand Charges:
     For each demand period:
       Annual Cost = Demand (kW) × Rate ($/kW) × # Months Active
   
   Flat Demand Charges:
     For each unique tier:
       Tier Cost = Demand (kW) × Tier Rate ($/kW) × # Months at Tier
     Annual Cost = Sum of all tier costs
   ```

3. **Calculate Annual Energy Charges:**
   ```
   For each month:
     Determine active energy periods for this month
     Renormalize user's energy distribution to active periods only
     Calculate monthly energy cost using month-specific periods
   Annual Energy Cost = Sum of all monthly energy costs
   ```

4. **Calculate Effective Rate:**
   ```
   Total Annual Cost = Demand Charges + Energy Charges + Fixed Charges × 12
   Effective Rate = Total Annual Cost / Annual Energy
   ```

### Energy Distribution Renormalization

In months where some periods are inactive, the user's energy distribution is renormalized:

**Example:**
- User specifies: Summer Peak 40%, Off-Peak 60%
- January: Only Off-Peak is active
- Renormalized for January: Off-Peak 100% (60%/60% = 100%)

This ensures physically realistic operation where the facility only operates during available periods.

### Maximum Load Factor (Annual)

Uses annual hour percentages:
```
Max LF = min(Annual Hour % / Energy %) for all periods with energy > 0
```

## Use Cases

### Use Case 1: Seasonal TOU Tariff
**Scenario:** Tariff has separate summer and winter demand periods.
- Summer periods: June-September (4 months)
- Winter periods: October-May (8 months)

**Benefit:** Annual analysis correctly charges:
- Summer demand for 4 months
- Winter demand for 8 months
- Properly weights energy costs by seasonal distribution

### Use Case 2: Month-Varying Flat Demand
**Scenario:** Tariff has higher flat demand charges in summer.
- Tier 0 ($8/kW): 8 months
- Tier 1 ($12/kW): 4 months

**Benefit:** Annual analysis:
- Shows separate columns for each tier
- Indicates month counts
- Calculates correct weighted average effective rate

### Use Case 3: Complex Seasonal Schedule
**Scenario:** Tariff has multiple energy periods with different seasonal availability.
- Peak periods only exist June-August
- Shoulder periods exist March-May, September-November
- Off-peak exists all year

**Benefit:** Annual analysis:
- Shows annual hour percentages accounting for availability
- Only charges for energy in periods when they exist
- Renormalizes distribution month-by-month

## Benefits

✅ **Accurate Annual Rates:** Properly accounts for monthly variability  
✅ **Seasonal Tariff Support:** Handles summer/winter rate structures  
✅ **Clear Presentation:** Shows exactly how many months each charge applies  
✅ **Flexible Analysis:** Users can quickly switch between monthly and annual views  
✅ **Physical Realism:** Energy distribution renormalizes to available periods  
✅ **Comprehensive Breakdown:** Detailed table shows all components  

## Technical Notes

### Performance
- Annual calculation loops through 12 months
- Computational complexity: O(12 × load_factors × periods)
- Typical performance: < 1 second for most tariffs

### Accuracy
- Uses actual calendar days for each month
- Accounts for weekday/weekend distribution
- Properly handles February (28/29 days)
- Fixed charges multiplied by 12 for annual

### Edge Cases Handled
- Periods active in 0 months (excluded from UI)
- Periods active in all 12 months (shown without special handling)
- Tariffs with only one flat demand tier (single column group)
- Energy periods with 0 hours in a month (skipped in renormalization)

## Future Enhancements

Potential future improvements:
- Leap year support (currently uses 2024 as reference)
- Export annual results to CSV with month-by-month breakdown
- Visualization of how effective rate varies by month
- Comparison tool: show monthly rates for each month side-by-side

## Related Files

- `src/components/cost_calculator.py` - Main implementation
- `LOAD_FACTOR_ANALYSIS_FEATURE.md` - Original feature documentation
- `LOAD_FACTOR_PHYSICS_FIX.md` - Physics constraint documentation
- `DEMAND_PERIOD_FILTERING_ENHANCEMENT.md` - Period filtering documentation

## Testing Recommendations

### Test Case 1: Uniform Tariff
- Tariff with no seasonal variation
- Verify annual rate = 12 × monthly rate
- Verify all periods show "12 months"

### Test Case 2: Summer/Winter Tariff
- Tariff with 2 demand tiers (summer/winter)
- Verify correct month counts (e.g., 6/6 or 4/8)
- Verify costs reflect proper tier allocation

### Test Case 3: Complex Seasonal
- Tariff with periods active in different month combinations
- Verify renormalization works correctly
- Verify energy costs match expected seasonal patterns

### Test Case 4: Edge Cases
- Tariff with period active only 1 month
- Tariff with many flat demand tiers
- Very high/low load factors

