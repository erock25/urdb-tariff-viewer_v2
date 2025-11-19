# Same Weekday/Weekend Schedule Feature

## Overview
Added a new feature to the Tariff Builder that allows users to indicate when weekday and weekend energy rate schedules are identical. This eliminates the need to complete the full schedule configuration process twice when the schedules are the same.

## Changes Made

### Modified Functions in `src/components/tariff_builder.py`

#### 1. `_render_advanced_schedule_editor(data: Dict, num_periods: int)`
- Added a checkbox option: "Weekday and weekend schedules are the same"
- Stores user preference in session state (`energy_schedule_same_for_weekday_weekend`)
- When enabled:
  - Only displays weekday schedule editing interface
  - Hides the Weekday/Weekend radio button toggle
  - Shows an informational message indicating that both schedules will be edited together
  - Updates the tip text to remove mention of separate weekday/weekend configuration

#### 2. `_render_advanced_demand_schedule_editor(data: Dict, num_periods: int)`
- Applied the same checkbox functionality for demand schedules
- Stores preference in session state (`demand_schedule_same_for_weekday_weekend`)
- Provides identical user experience for demand schedule configuration

#### 3. `_apply_templates_to_schedule(data: Dict, rate_type: str, same_schedule: bool = False)`
- Added new `same_schedule` parameter (defaults to False for backward compatibility)
- When `same_schedule=True`:
  - Automatically copies all weekday schedule data to weekend schedules
  - Bypasses the separate weekend template processing
- When `same_schedule=False`:
  - Maintains original behavior with separate weekday and weekend template processing

## User Experience

### Before
Users had to:
1. Select "Weekday" from the radio button
2. Complete all 3 steps (Manage Templates, Edit Templates, Assign to Months)
3. Select "Weekend" from the radio button
4. Repeat all 3 steps for weekend schedule
5. Even if schedules were identical

### After
Users can now:
1. Check the box "Weekday and weekend schedules are the same"
2. Complete all 3 steps once for the weekday schedule
3. Weekend schedule automatically matches the weekday schedule
4. Saves significant time when tariffs have identical weekday/weekend schedules

## Benefits

1. **Time Savings**: Reduces configuration time by approximately 50% for tariffs with identical schedules
2. **Error Prevention**: Eliminates potential for inconsistencies between weekday and weekend schedules
3. **Better UX**: Clearer workflow with contextual messaging about what's being edited
4. **Backward Compatible**: Unchecked by default, maintains existing behavior for tariffs with different schedules

## Technical Implementation

### Session State Variables
- `energy_schedule_same_for_weekday_weekend`: Boolean flag for energy schedules
- `demand_schedule_same_for_weekday_weekend`: Boolean flag for demand schedules

### Data Flow
1. User checks the "same schedule" checkbox
2. Session state is updated
3. UI adapts to show only weekday editing interface
4. Templates are edited for weekday only
5. During `_apply_templates_to_schedule()`, weekday data is copied to weekend
6. Both preview tabs show identical schedules

## Testing Recommendations

1. **Test with checkbox enabled**:
   - Create weekday templates
   - Assign templates to months
   - Verify weekend schedule matches weekday in preview tabs

2. **Test with checkbox disabled**:
   - Verify original behavior is maintained
   - Create different weekday and weekend templates
   - Verify schedules remain independent

3. **Test toggling checkbox**:
   - Start with different schedules
   - Enable checkbox
   - Verify weekend adopts weekday schedule
   - Disable checkbox
   - Verify weekend schedule is preserved

## Future Enhancements

Potential improvements could include:
- Option to copy existing weekend schedule to weekday (bidirectional sync)
- Warning when enabling checkbox if weekend schedules differ from weekday
- Bulk operations to sync schedules after initial configuration

