# Heatmap Rate Values Display Feature

## Overview
Updated the schedule preview heatmaps in the Tariff Builder to display actual rate values (e.g., $5.00/kW) instead of just period indices (0, 1, 2). This enhancement applies to both energy and demand TOU schedules, making the previews more informative and useful.

## Changes Made

### Modified Function: `_show_schedule_heatmap()`

**New Parameters:**
- `rate_structure` (optional): List[List[Dict]] - The rate structure data containing rate and adjustment values
- `rate_type` (optional): str - Either 'energy' or 'demand' for proper formatting

**Enhanced Functionality:**

#### 1. Rate Value Display
When `rate_structure` is provided:
- Maps period indices to actual rate values
- Calculates total rate (base rate + adjustment) for each period
- Creates a heatmap showing actual dollar values instead of period numbers
- Formats values appropriately:
  - Demand rates: 4 decimal places (e.g., $5.0000/kW)
  - Energy rates: 4 decimal places (e.g., $0.1234/kWh)

#### 2. Enhanced Legend
The period legend now shows both the label and the actual rate:
- **Demand example**: "0: Peak ($15.0000/kW)"
- **Energy example**: "2: Off-Peak ($0.0850/kWh)"

#### 3. Backward Compatibility
When `rate_structure` is not provided:
- Falls back to displaying period indices (original behavior)
- Maintains compatibility with any code that doesn't pass rate structure

## Implementation Details

### Heatmap Value Calculation
```python
for period_idx in month_schedule:
    if period_idx < len(rate_structure):
        rate = rate_structure[period_idx][0].get('rate', 0.0)
        adj = rate_structure[period_idx][0].get('adj', 0.0)
        total_rate = rate + adj
        month_rates.append(total_rate)
```

### DataFrame Creation
- Creates a DataFrame with actual rate values instead of period indices
- Applies gradient coloring based on rate magnitude (green = low, red = high)
- Formats values with appropriate decimal precision

### Legend Enhancement
```python
if rate_structure is not None and i < len(rate_structure):
    rate = rate_structure[i][0].get('rate', 0.0)
    adj = rate_structure[i][0].get('adj', 0.0)
    total_rate = rate + adj
    if rate_type == 'demand':
        st.markdown(f"**{i}:** {label} (${total_rate:.4f}/kW)")
    else:
        st.markdown(f"**{i}:** {label} (${total_rate:.5f}/kWh)")
```

## Updated Call Sites

### 1. Energy Schedule Preview
```python
_show_schedule_heatmap(data['energyweekdayschedule'], "Weekday", data['energytoulabels'],
                      rate_structure=data.get('energyratestructure'),
                      rate_type='energy')
```

### 2. Demand Schedule Preview
```python
_show_schedule_heatmap(data['demandweekdayschedule'], "Demand Weekday", 
                      data.get('demandlabels', [f"Period {i}" for i in range(num_periods)]),
                      rate_structure=data.get('demandratestructure'),
                      rate_type='demand')
```

## User Experience

### Before
**Heatmap Display:**
- Shows period indices: 0, 1, 2, 3
- User must mentally map indices to rates
- Legend shows: "0: Peak", "1: Mid-Peak", "2: Off-Peak"

**Example cell value:** `2`

### After
**Heatmap Display:**
- Shows actual rate values: $15.00, $8.50, $0.00
- Immediate visual representation of cost
- Legend shows: "0: Peak ($15.0000/kW)", "1: Mid-Peak ($8.5000/kW)", "2: Off-Peak ($0.0000/kW)"

**Example cell value:** `$8.5000`

## Benefits

1. **Immediate Clarity**: Users can instantly see the actual rates that apply at each hour/month
2. **Better Visualization**: Color gradient now represents actual cost magnitude
3. **Easier Validation**: Can quickly verify rates are correct without cross-referencing
4. **Professional Presentation**: More informative and polished preview
5. **Decision Support**: Easier to identify high-cost periods and make schedule adjustments

## Example Use Cases

### Commercial Tariff with Demand Charges
A user configuring a tariff with three demand periods can now see:
- **Summer Peak Hours (4pm-9pm)**: Heatmap shows $15.0000/kW (red)
- **Summer Mid-Peak Hours (9am-4pm)**: Heatmap shows $5.0000/kW (yellow)
- **Off-Peak Hours (all other)**: Heatmap shows $0.0000/kW (green)

### Residential TOU Energy Rates
A user configuring energy rates can see:
- **Peak**: $0.2500/kWh (red)
- **Mid-Peak**: $0.1500/kWh (yellow)
- **Off-Peak**: $0.0850/kWh (green)

## Technical Notes

### Formatting
- Energy rates: `.5f` format (5 decimal places) for precision in $/kWh
- Demand rates: `.4f` format (4 decimal places) for $/kW
- Period indices: `.0f` format (integers) when rate structure not available

### Color Gradient
The existing `RdYlGn_r` (Red-Yellow-Green reversed) colormap is maintained:
- Green shades = Lower rates (better for customer)
- Yellow shades = Medium rates
- Red shades = Higher rates (more expensive)

### Data Flow
1. User sets rates in period configuration
2. User creates schedule assigning periods to hours
3. Heatmap function receives both rate structure and schedule
4. Function maps period indices → actual rates
5. Display shows rate values with appropriate coloring

## Files Modified
- `src/components/tariff_builder.py`
  - `_show_schedule_heatmap()` - Enhanced to display rate values
  - Energy schedule preview calls - Pass rate structure
  - Demand schedule preview calls - Pass rate structure

## Backward Compatibility
- Optional parameters with defaults ensure backward compatibility
- Functions still work if rate_structure is not provided
- Falls back to period index display if no rates available

## Testing Recommendations

1. **Test Energy Schedule Preview**:
   - Configure energy rates with different values
   - Set up a schedule
   - Verify heatmap shows actual $/kWh values
   - Check legend displays rates correctly

2. **Test Demand Schedule Preview**:
   - Configure demand rates including zero-rate period
   - Set up a schedule
   - Verify heatmap shows actual $/kW values
   - Check color gradient represents rate magnitude

3. **Test Legend Enhancement**:
   - Verify each period shows label and rate
   - Check formatting precision (4-5 decimal places)
   - Confirm units are displayed correctly

4. **Test Visual Gradient**:
   - Higher rates should appear in red/orange
   - Lower rates should appear in green
   - Zero rates should be clearly distinguishable

5. **Test Backward Compatibility**:
   - Ensure existing code still works
   - Verify fallback to period indices if needed

## Future Enhancements

Potential improvements:
- Add toggle to switch between rate values and period indices
- Display both rate value and period label in cells
- Add tooltips showing detailed rate breakdown (base + adjustment)
- Option to export heatmap as image or PDF
- Add comparison view for weekday vs weekend side-by-side

