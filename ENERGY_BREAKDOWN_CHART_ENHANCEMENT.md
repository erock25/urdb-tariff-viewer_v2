# Enhancement: Energy Charge Breakdown by Period in Load Factor Chart

## Overview

Updated the "📈 Effective Rate vs Load Factor" chart in the Load Factor Rate Analysis Tool to display energy charges broken down by individual energy rate periods, providing much more granular visibility into cost composition.

## Changes Made

### Before
The chart showed energy charges as a single aggregated green bar in the stacked cost breakdown.

### After
The chart now displays **separate stacked bars for each energy rate period**, allowing users to see exactly how much cost comes from each rate period (e.g., Peak, Mid-Peak, Off-Peak) at every load factor.

## Implementation Details

### Modified File
**`src/components/cost_calculator.py`** - `_display_load_factor_results()` function

### Key Changes

#### 1. Calculate Comprehensive Breakdown Earlier
Moved the comprehensive breakdown calculation to occur **before** creating the chart (instead of after), allowing us to access per-period energy cost data:

```python
# Get comprehensive breakdown for energy period details
if tariff_data is not None and demand_inputs is not None and energy_percentages is not None:
    comprehensive_df = _calculate_comprehensive_load_factor_breakdown(...)
```

#### 2. Add Separate Traces for Each Energy Period
Instead of one "Energy Charges" trace, now creates individual traces for each energy period:

```python
# Add energy period traces
for period_idx in range(len(energy_structure)):
    period_label = energy_labels[period_idx] if period_idx < len(energy_labels) else f"Period {period_idx}"
    cost_col = f'{period_label} Cost ($)'
    
    if cost_col in comprehensive_df.columns:
        fig.add_trace(go.Bar(
            x=results['Load Factor Value'] * 100,
            y=comprehensive_df[cost_col],
            name=f'{period_label} Energy',
            marker_color=energy_colors[color_idx],
            yaxis='y2',
            hovertemplate=f"<b>Load Factor: %{{x:.0f}}%</b><br>{period_label}: $%{{y:.2f}}<extra></extra>"
        ))
```

#### 3. Color Palette for Energy Periods
Defined a green-based color palette with 8 distinct shades to visually differentiate energy periods:

```python
energy_colors = [
    'rgba(34, 197, 94, 0.9)',   # Green
    'rgba(16, 185, 129, 0.8)',  # Emerald
    'rgba(5, 150, 105, 0.7)',   # Dark green
    'rgba(132, 204, 22, 0.7)',  # Lime
    'rgba(101, 163, 13, 0.7)',  # Olive
    'rgba(74, 222, 128, 0.6)',  # Light green
    'rgba(22, 163, 74, 0.6)',   # Forest green
    'rgba(187, 247, 208, 0.7)', # Very light green
]
```

#### 4. Fallback Behavior
If comprehensive breakdown data is unavailable, the chart falls back to showing aggregated energy charges (original behavior):

```python
else:
    # Fallback to aggregate energy charges if breakdown not available
    fig.add_trace(go.Bar(
        x=results['Load Factor Value'] * 100,
        y=results['Energy Charges ($)'],
        name='Energy Charges',
        ...
    ))
```

### Chart Structure

**Stacked Bar Layers (bottom to top):**
1. **Energy Period 1** (e.g., Off-Peak) - Darkest green
2. **Energy Period 2** (e.g., Mid-Peak) - Medium green
3. **Energy Period 3** (e.g., Peak) - Lighter green
4. ... (additional periods as needed)
5. **Demand Charges** - Orange
6. **Fixed Charges** - Gray

**Line Overlay:**
- **Effective Rate ($/kWh)** - Blue line with markers (left y-axis)

## Benefits

### 1. **Granular Cost Visibility**
Users can immediately see:
- Which energy periods contribute most to total cost
- How period-specific costs change with load factor
- The relative magnitude of each rate period's impact

### 2. **Rate Optimization Insights**
Helps identify:
- High-cost periods worth targeting for load shifting
- Periods where small load factor changes have big cost impacts
- Opportunities for operational adjustments

### 3. **Better Decision Making**
Enables:
- More informed load shifting strategies
- Understanding of which periods drive effective rate changes
- Quantification of savings potential by period

### 4. **Visual Clarity**
- Stacked bars clearly show cost composition
- Color-coded by period for easy identification
- Hover tooltips show exact dollar amounts per period
- Legend identifies each period

## Example Scenarios

### Scenario 1: Peak-Heavy Tariff
**Tariff:** High peak rates June-August, 12-8 PM
**Visualization shows:**
- Large dark green bar (Peak energy) at higher load factors
- Smaller light green bars (Off-Peak) provide base cost
- Clear visual impact of peak period on total cost

**Insight:** "Peak energy is 60% of my cost despite being only 15% of hours"

### Scenario 2: Load Factor Sensitivity
**At 50% LF:** Peak period shows $500/month
**At 60% LF:** Peak period jumps to $800/month (+60%)
**At 70% LF:** Peak period reaches $1,100/month (+120% from 50%)

**Insight:** "Operating above 50% LF dramatically increases peak costs"

### Scenario 3: Multi-Period Comparison
Three periods visible in stack:
- Off-Peak (bottom): ~$300 at all load factors
- Mid-Peak (middle): Grows from $200 to $600
- Peak (top): Grows from $100 to $800

**Insight:** "Peak and Mid-Peak grow faster with LF than Off-Peak"

## User Interface

### Hover Interaction
When hovering over any bar segment:
```
Load Factor: 75%
Peak Energy: $850.23
```

### Legend
- Horizontal layout above chart
- Each period labeled with name + "Energy"
- Color-coded to match bars
- Click to toggle visibility

### Tooltips
- Period-specific dollar amounts
- Load factor percentage
- Clean formatting with no extraneous text

## Technical Notes

### Performance
- Minimal performance impact
- Comprehensive breakdown already calculated for table
- Reusing same calculation for chart reduces redundancy

### Scalability
- Supports any number of energy periods (2-8+ typical)
- Color palette cycles if >8 periods exist
- Legend wraps automatically for many periods

### Data Source
Uses the comprehensive breakdown DataFrame which includes:
- Per-period energy consumption (kWh)
- Per-period rates ($/kWh)
- Per-period costs ($)
- Proper handling of periods active/inactive in given month

### Chart Properties
- **Stacked bars:** `barmode='stack'`
- **Dual y-axes:** Costs (right), Effective Rate (left)
- **Height:** 500px (unchanged)
- **Responsive:** `use_container_width=True`

## Backward Compatibility

✅ **Fully backward compatible**
- If comprehensive breakdown unavailable → shows aggregated energy
- If tariff has no TOU structure → shows single energy bar
- No breaking changes to existing functionality

## Testing Recommendations

### Test Case 1: Simple TOU (2 Periods)
- Peak and Off-Peak
- Verify two distinct green shades
- Check stacking order (Off-Peak on bottom)

### Test Case 2: Complex TOU (4+ Periods)
- Multiple shoulder/mid-peak periods
- Verify all periods visible and distinct
- Check legend readability

### Test Case 3: Seasonal Variation
- Summer/Winter periods
- Verify correct periods show based on month selection
- Check period costs reflect seasonal rates

### Test Case 4: High Load Factors
- LF approaching maximum valid
- Verify period distribution changes appropriately
- Check for periods transitioning to hour percentage allocation

## Related Features

This enhancement complements:
- **Comprehensive Breakdown Table** - Same data, tabular format
- **Energy Rate Heatmap** - Visual schedule of when periods occur
- **Hour Percentage Labels** - Shows time each period is available
- **Load Factor Physics** - Constrains maximum feasible LF

## Future Enhancements

Potential improvements:
1. **Demand Period Breakdown** - Split demand bar by TOU demand periods
2. **Percentage Labels** - Show % contribution on each bar segment
3. **Rate Labels** - Display $/kWh rate for each period on hover
4. **Comparison Mode** - Overlay multiple scenarios
5. **Period Highlighting** - Click period in legend to highlight across all LFs

## Code Quality

✅ **No Linter Errors** - Clean implementation
✅ **Reuses Existing Logic** - Leverages comprehensive breakdown calculation
✅ **Fallback Handling** - Graceful degradation if data unavailable
✅ **Color Consistency** - Green theme for energy maintains visual coherence
✅ **Documentation** - Clear inline comments

## Summary

This enhancement transforms the Load Factor chart from showing aggregated energy costs to revealing the detailed composition by rate period. Users gain immediate visual insight into which periods drive their costs and how those costs scale with load factor, enabling more informed operational and strategic decisions.

The implementation efficiently reuses existing calculation logic, maintains backward compatibility, and provides a professional, intuitive visualization that scales from simple to complex tariff structures.

