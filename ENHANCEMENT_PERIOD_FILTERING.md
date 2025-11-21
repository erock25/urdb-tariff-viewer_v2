# Enhancement: Intelligent Period Filtering for Load Factor Rate Analysis

## Overview

Enhanced the Load Factor Rate Analysis tool to intelligently filter energy periods based on the selected month's TOU schedule. The tool now only displays and allows input for energy periods that are actually scheduled in the selected month.

## Changes Made

### 1. New Helper Function

Added `_get_active_energy_periods_for_month()` in `src/components/cost_calculator.py`:

```python
def _get_active_energy_periods_for_month(tariff_data: Dict[str, Any], month: int) -> set:
    """
    Determine which energy periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    # Get schedules
    weekday_schedule = tariff_data.get('energyweekdayschedule', [])
    weekend_schedule = tariff_data.get('energyweekendschedule', [])
    
    # Check if month is valid and schedules exist
    if month < len(weekday_schedule):
        # Add all periods from weekday schedule for this month
        active_periods.update(weekday_schedule[month])
    
    if month < len(weekend_schedule):
        # Add all periods from weekend schedule for this month
        active_periods.update(weekend_schedule[month])
    
    return active_periods
```

**How it works:**
- Parses both `energyweekdayschedule` and `energyweekendschedule` arrays
- Extracts all unique period indices for the selected month (0-11)
- Returns a set of period indices that actually appear in that month's schedule

### 2. Updated Energy Distribution UI

Modified `_render_load_factor_analysis_tool()` to:

1. **Call the helper function** to get active periods for the selected month
2. **Show informational message** when some periods are filtered out
3. **Only display input fields** for active periods
4. **Auto-set default value** (100%) to the first active period

**Key changes:**
```python
# Get active periods for the selected month
active_periods = _get_active_energy_periods_for_month(tariff_data, selected_month)

# Show info about which periods are active
if len(active_periods) < num_energy_periods:
    inactive_periods = set(range(num_energy_periods)) - active_periods
    inactive_labels = [energy_labels[i] if i < len(energy_labels) else f"Period {i}" 
                     for i in sorted(inactive_periods)]
    st.info(f"ℹ️ Only showing periods present in {month_names[selected_month]}. "
           f"The following periods are not scheduled this month: {', '.join(inactive_labels)}")

# Only show active periods
active_periods_list = sorted(list(active_periods))
```

### 3. Documentation Updates

Updated `LOAD_FACTOR_ANALYSIS_FEATURE.md` to document:
- New intelligent period filtering feature
- Description of the new helper function
- User-facing behavior in the Notes section

## Benefits

### 1. **Prevents User Error**
Users can no longer accidentally enter percentages for periods that don't exist in the selected month. For example:
- Can't assign energy to "Summer Peak" in January if that period isn't scheduled
- Can't assign energy to "Winter Off-Peak" in July if that period isn't scheduled

### 2. **Clearer UI**
- Reduces cognitive load by only showing relevant options
- Info message clearly explains which periods are excluded and why

### 3. **More Accurate Calculations**
- Ensures calculations only use periods that are actually scheduled
- Prevents unrealistic scenarios where energy is allocated to non-existent periods

### 4. **Automatically Adapts**
- Works with any tariff structure (seasonal, time-of-use, flat rate)
- No configuration needed - automatically parses existing schedule data

## Example Scenarios

### Scenario 1: Seasonal Tariff
**Tariff Structure:**
- Period 0: Summer Peak
- Period 1: Summer Off-Peak  
- Period 2: Winter Peak
- Period 3: Winter Off-Peak

**Behavior:**
- **January (Winter Month)**: Only shows periods 2 and 3
  - Info: "Only showing periods present in January. The following periods are not scheduled this month: Summer Peak, Summer Off-Peak"
- **July (Summer Month)**: Only shows periods 0 and 1
  - Info: "Only showing periods present in July. The following periods are not scheduled this month: Winter Peak, Winter Off-Peak"

### Scenario 2: Consistent Year-Round Tariff
**Tariff Structure:**
- Period 0: Off-Peak
- Period 1: Mid-Peak
- Period 2: On-Peak
- All periods present in all months

**Behavior:**
- **Any Month**: Shows all 3 periods
  - No info message (all periods active)

### Scenario 3: Flat Rate Tariff
**Tariff Structure:**
- Period 0: Flat Rate (24/7, all year)

**Behavior:**
- **Any Month**: Shows only period 0
  - No info message (only 1 period exists)

## Testing

Created and ran comprehensive test cases to verify:
1. ✅ Seasonal tariffs correctly identify summer vs winter periods
2. ✅ Consistent tariffs show all periods for all months
3. ✅ Flat rate tariffs work correctly
4. ✅ Weekday and weekend schedules are both considered
5. ✅ Edge cases handled (empty schedules, invalid months)

## Technical Details

**Files Modified:**
- `src/components/cost_calculator.py` - Core implementation
- `LOAD_FACTOR_ANALYSIS_FEATURE.md` - Documentation update

**Backward Compatibility:**
- ✅ Fully backward compatible
- ✅ Works with existing tariff data
- ✅ No changes to calculation logic
- ✅ No changes to data structures

**Performance:**
- Minimal overhead (simple set operations on 12x24 arrays)
- Executes once per month selection change
- No noticeable performance impact

## Future Enhancements

Potential future improvements:
1. Show visual indicator of which hours each period covers
2. Add ability to view the full TOU schedule from within the tool
3. Suggest typical energy distributions based on period types
4. Allow importing energy distribution from load profile data

