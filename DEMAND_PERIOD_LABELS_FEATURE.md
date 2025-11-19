# Demand Period Labels Feature

## Overview
Added the ability to specify custom labels for TOU (Time-of-Use) demand rate periods in the Tariff Builder, matching the existing functionality available for energy rates. Users can now provide meaningful names like "Peak", "Mid-Peak", "Off-Peak", or "No Charge" instead of generic "Period 0", "Period 1", etc.

## Changes Made

### Modified Components in `src/components/tariff_builder.py`

#### 1. `_render_demand_charges_section()`
**Changes:**
- Added initialization of `demandlabels` array when demand periods are created/modified
- Added a text input field for "Period Label" at the top of each demand period expander
- Labels are stored immediately when user types them (not in a form)
- Updated schedule preview to use the actual demand labels instead of generic "Period {i}" text

**New Features:**
- Period Label input field with helpful examples: "e.g., 'Peak', 'Mid-Peak', 'Off-Peak', 'No Charge'"
- Automatic initialization with default "Period {i}" labels
- Labels persist when changing the number of periods (existing labels are preserved)

#### 2. `_render_simple_demand_schedule_editor(data: Dict, num_periods: int)`
**Changes:**
- Retrieves demand labels from data structure
- Updated selectbox `format_func` to display labels: `"{label} (Period {i})"`
- Updated the "Current Schedule" dataframe to show labels instead of generic period numbers

**Benefits:**
- Users can see meaningful period names when selecting schedules for each hour
- Current schedule display is more readable with actual period names

#### 3. `_render_template_editor(schedule_type: str, rate_type: str, num_periods: int, data: Dict)`
**Changes:**
- Added logic to use demand labels when `rate_type == 'demand'`
- Format function now displays demand labels in the hour-by-hour selectboxes
- Falls back to "P{x}" notation if labels aren't available

**Benefits:**
- Template editing interface shows meaningful period names
- Consistent labeling across all demand schedule editing interfaces

#### 4. Demand Schedule Preview
**Changes:**
- Updated both weekday and weekend schedule preview tabs to use `demandlabels`
- Heatmap legend now displays custom labels instead of generic period numbers

## Data Structure

### URDB Field: `demandlabels`
- Type: `List[str]`
- Length: Must match the number of demand periods
- Example: `["Peak", "Mid-Peak", "Off-Peak", "No Charge"]`
- Default: `["Period 0", "Period 1", "Period 2", ...]`

### Initialization Logic
```python
# When demand periods are created or modified:
if len(data['demandratestructure']) != num_periods:
    data['demandlabels'] = [f"Period {i}" for i in range(num_periods)]

# Ensure labels exist and have correct length:
if 'demandlabels' not in data or len(data['demandlabels']) != num_periods:
    data['demandlabels'] = [f"Period {i}" for i in range(num_periods)]
```

## User Experience

### Before
- Demand periods were only identified by numbers: "Period 0", "Period 1", etc.
- Users had to mentally map numbers to actual rate meanings
- Schedule displays and editors used generic numbering throughout

### After
- Users can assign meaningful names to each demand period
- Period labels appear in:
  - Demand period expander headers (can be updated)
  - Hour-by-hour schedule selectors in Simple mode
  - Template editor hour selectors in Advanced mode
  - Schedule preview heatmap legends
  - Current schedule dataframe displays
- Consistent labeling across all demand-related interfaces

## Example Use Case

### Tariff with Three Demand Periods:
1. **Period 0**: "No Charge" (Rate: $0.00/kW) - Off-peak hours, overnight
2. **Period 1**: "Mid-Peak" (Rate: $5.00/kW) - Shoulder hours
3. **Period 2**: "Peak" (Rate: $15.00/kW) - On-peak hours, 4pm-9pm

When configuring the schedule, users now see:
- "No Charge (Period 0)"
- "Mid-Peak (Period 1)"
- "Peak (Period 2)"

Instead of just:
- "Period 0"
- "Period 1"
- "Period 2"

## Implementation Details

### Label Input
- Located at the top of each demand period expander
- Updates immediately on change (no form submission required)
- Preserves existing labels when period count remains unchanged

### Label Usage
All demand schedule interfaces now use labels via:
```python
demand_labels = data.get('demandlabels', [f"Period {i}" for i in range(num_periods)])
```

### Backward Compatibility
- Works with existing tariff files that don't have `demandlabels`
- Falls back to "Period {i}" notation when labels aren't available
- Automatically initializes labels for new tariffs

## Benefits

1. **Improved Clarity**: Users immediately understand what each demand period represents
2. **Better Documentation**: Labels serve as inline documentation for the tariff structure
3. **Reduced Errors**: Less chance of assigning wrong periods when names are meaningful
4. **Consistency**: Matches the existing energy rate labeling functionality
5. **Professional Output**: Generated tariff files have well-documented demand structures

## Testing Recommendations

1. **Create new tariff with demand charges**:
   - Set number of demand periods (e.g., 3)
   - Verify default labels appear: "Period 0", "Period 1", "Period 2"
   - Change labels to custom names
   - Verify labels appear in all interfaces

2. **Test label persistence**:
   - Set custom labels
   - Navigate away and back to the section
   - Verify labels are preserved

3. **Test period count changes**:
   - Start with 2 periods, set labels
   - Increase to 3 periods
   - Verify existing labels preserved, new label gets default
   - Decrease back to 2 periods
   - Verify appropriate labels remain

4. **Test schedule interfaces**:
   - Use Simple mode: verify labels appear in hour selectors
   - Use Advanced mode: verify labels appear in template editor
   - Check preview tabs: verify labels appear in legends

5. **Test backward compatibility**:
   - Load an existing tariff file without `demandlabels`
   - Verify it defaults to "Period {i}" notation
   - Add labels and save
   - Verify labels persist in saved file

## Related Features

This feature complements:
- Energy period labels (`energytoulabels`)
- Same weekday/weekend schedule option
- Zero-rate period hint for non-charged hours
- Template-based schedule configuration

