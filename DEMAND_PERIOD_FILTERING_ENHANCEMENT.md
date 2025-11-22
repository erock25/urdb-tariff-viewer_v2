# Enhancement: TOU Demand Period Filtering for Load Factor Rate Analysis

## Overview

Extended the Load Factor Rate Analysis tool to intelligently filter TOU demand periods based on the selected month's schedule. The tool now only displays and allows input for demand periods that are actually scheduled in the selected month, matching the existing behavior for energy periods.

## Changes Made

### 1. New Helper Function

Added `_get_active_demand_periods_for_month()` in `src/components/cost_calculator.py`:

```python
def _get_active_demand_periods_for_month(tariff_data: Dict[str, Any], month: int) -> set:
    """
    Determine which demand periods are actually present in a given month.
    
    Args:
        tariff_data: Tariff data dictionary
        month: Month index (0-11)
    
    Returns:
        Set of period indices that appear in the selected month
    """
    active_periods = set()
    
    # Get schedules
    weekday_schedule = tariff_data.get('demandweekdayschedule', [])
    weekend_schedule = tariff_data.get('demandweekendschedule', [])
    
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
- Parses both `demandweekdayschedule` and `demandweekendschedule` arrays
- Extracts all unique period indices for the selected month (0-11)
- Returns a set of period indices that actually appear in that month's schedule

### 2. Updated TOU Demand UI

Modified `_render_load_factor_analysis_tool()` to:

1. **Call the helper function** to get active demand periods for the selected month
2. **Show informational message** when some demand periods are filtered out
3. **Only display input fields** for active demand periods
4. **Updated input keys** to include selected month, ensuring proper state reset when month changes

#### Before:
```python
# Showed ALL demand periods regardless of month
for i in range(num_demand_periods):
    # ... display input for every period
```

#### After:
```python
# Get active demand periods for the selected month
active_demand_periods = _get_active_demand_periods_for_month(tariff_data, selected_month)

# Show info about which periods are active
if len(active_demand_periods) < num_demand_periods:
    inactive_periods = set(range(num_demand_periods)) - active_demand_periods
    inactive_labels = [demand_labels[i] if i < len(demand_labels) else f"Period {i}" 
                     for i in sorted(inactive_periods)]
    st.info(f"ℹ️ Only showing demand periods present in {month_names[selected_month]}. "
           f"The following demand periods are not scheduled this month: {', '.join(inactive_labels)}")

# Only show active periods
active_demand_periods_list = sorted(list(active_demand_periods))
for idx, i in enumerate(active_demand_periods_list):
    # ... display input only for active periods
```

## Benefits

✅ **Prevents user errors** - Users cannot enter demand values for periods that don't exist in the selected month  
✅ **Cleaner UI** - Fewer input fields = less confusion, especially for tariffs with seasonal demand periods  
✅ **Automatic validation** - Based on the tariff's actual TOU demand schedule  
✅ **Consistent behavior** - Matches the existing energy period filtering functionality  
✅ **Works with any tariff** - Automatically adapts to any tariff structure  

## Use Cases

### Example 1: Seasonal Demand Periods
A tariff has separate "Summer Peak" and "Winter Peak" demand periods:
- **June (Summer)**: Only shows "Summer Peak" demand period
- **January (Winter)**: Only shows "Winter Peak" demand period

### Example 2: Complex TOU Structures
A tariff has multiple demand periods but some only apply during specific months:
- The tool automatically hides non-applicable periods
- Users see only relevant inputs for their selected month
- Info message clearly indicates which periods are excluded

## Implementation Details

- **Location**: `src/components/cost_calculator.py`
- **New function**: `_get_active_demand_periods_for_month()` (lines ~717-740)
- **Modified section**: TOU Demand Charges rendering (lines ~825-855)
- **Data sources**: `demandweekdayschedule` and `demandweekendschedule` from tariff data
- **Period indices**: 0-based integer indices matching the `demandratestructure` array

## Testing Recommendations

1. **Test with seasonal tariffs**: Verify correct filtering between summer/winter months
2. **Test with non-seasonal tariffs**: Ensure all periods show when schedules are uniform
3. **Test month switching**: Verify UI updates correctly when changing months
4. **Test edge cases**: Empty schedules, missing schedule data, etc.

## Related Enhancements

This enhancement complements the existing energy period filtering:
- `_get_active_energy_periods_for_month()` - Filters energy periods (already implemented)
- `_get_active_demand_periods_for_month()` - Filters demand periods (this enhancement)

Both functions follow the same pattern and provide consistent user experience across the tool.

