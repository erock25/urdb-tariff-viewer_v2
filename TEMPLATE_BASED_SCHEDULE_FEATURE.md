# Template-Based TOU Schedule Feature

## Overview

The **Template-Based TOU Schedule** feature has been implemented to dramatically improve the user experience when creating Advanced (different by month) Energy and Demand TOU schedules in the Tariff Builder.

## The Problem It Solves

Previously, users had to:
- Edit one month at a time
- Manually copy schedules to all months
- Repeat this process for each unique schedule pattern
- No clear way to see which months shared the same schedule

This was tedious and error-prone, especially since most tariffs only have 2-3 unique schedules per year (e.g., Summer, Winter, Shoulder seasons).

## The New Template-Based Approach

### How It Works

The new system uses a **3-step workflow**:

#### Step 1: Manage Templates
- **Add templates** with descriptive names (e.g., "Summer Peak", "Winter Off-Peak", "Shoulder")
- **Delete templates** you no longer need
- **View templates** and see how many months are assigned to each

#### Step 2: Edit Templates
- Select a template to edit
- Define the 24-hour TOU schedule for that template
- Save the template
- Preview the template in a table format

#### Step 3: Assign Templates to Months
- Assign each month (Jan-Dec) to a template using dropdown menus
- See an instant summary of which months use which template
- Apply all assignments with one click

### Key Benefits

✅ **Faster workflow** - Define each unique schedule once, apply to many months  
✅ **Clear organization** - Named templates make it obvious what each schedule represents  
✅ **Better visibility** - Assignment summary shows the full year at a glance  
✅ **Easy updates** - Change a template and it updates all assigned months  
✅ **Reduced errors** - No need to manually copy schedules repeatedly  

## Where to Find It

### Energy Schedules
1. Navigate to **📅 Energy Schedule** tab in Tariff Builder
2. Select **"Advanced (different by month)"** mode
3. Choose **Weekday** or **Weekend** schedule type
4. Follow the 3-step template workflow

### Demand Schedules
1. Navigate to **🔌 Demand Charges** tab in Tariff Builder
2. After defining demand rates, scroll to the **Schedule** section
3. Select **"Advanced (different by month)"** mode
4. Choose **Weekday** or **Weekend** schedule type
5. Follow the 3-step template workflow

## Example Workflow

### Typical Use Case: Creating a 3-Season Tariff

**Scenario**: Your utility has different rates for Summer, Winter, and Shoulder months.

#### Step 1: Manage Templates
1. Start with the default "Template 1"
2. Rename or add:
   - "Summer Peak" 
   - "Winter Standard"
   - "Shoulder"

#### Step 2: Edit Templates
1. Select "Summer Peak"
   - Set higher rates during peak hours (e.g., 2-8 PM = Period 2)
   - Save template

2. Select "Winter Standard"
   - Set moderate rates (e.g., 8 AM-6 PM = Period 1, rest = Period 0)
   - Save template

3. Select "Shoulder"
   - Set flat rates (e.g., all hours = Period 0)
   - Save template

#### Step 3: Assign to Months
- January: Winter Standard
- February: Winter Standard
- March: Shoulder
- April: Shoulder
- May: Shoulder
- June: Summer Peak
- July: Summer Peak
- August: Summer Peak
- September: Shoulder
- October: Shoulder
- November: Winter Standard
- December: Winter Standard

Click **"Apply Month Assignments"** - Done! ✓

## Technical Details

### Data Structure

Templates are stored in Streamlit session state:
```python
st.session_state.energy_schedule_templates = {
    'weekday': {
        'Summer Peak': {
            'name': 'Summer Peak',
            'schedule': [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0],
            'assigned_months': [5, 6, 7]  # Jun, Jul, Aug
        },
        # ... more templates
    },
    'weekend': { /* similar structure */ }
}
```

### Final Schedule Generation

The `_apply_templates_to_schedule()` function automatically converts templates into the final schedule arrays that the calculation engine expects:
```python
data['energyweekdayschedule'] = [
    [0, 0, ..., 0],  # January (from assigned template)
    [0, 0, ..., 0],  # February (from assigned template)
    # ... 12 months total
]
```

## Backward Compatibility

✅ **Simple mode still works** - Users who want the same schedule for all months can still use Simple mode  
✅ **Existing tariffs** - The feature initializes templates from existing schedule data  
✅ **No breaking changes** - The underlying data format remains unchanged  

## Implementation Details

### New Functions Added

1. **`_initialize_default_templates()`** - Creates initial template from existing data
2. **`_get_template_key()`** - Helper to get session state key
3. **`_get_schedule_key()`** - Helper to get data schedule key
4. **`_render_template_manager()`** - UI for adding/deleting templates
5. **`_render_template_editor()`** - UI for editing 24-hour schedules
6. **`_render_month_assignment()`** - UI for assigning templates to months
7. **`_apply_templates_to_schedule()`** - Converts templates to final schedule arrays

### Modified Functions

- **`_render_advanced_schedule_editor()`** - Now uses template-based workflow
- **`_render_advanced_demand_schedule_editor()`** - Now uses template-based workflow

## User Feedback

The UI provides clear feedback at each step:
- ✓ Success messages when templates are saved
- ✓ Success messages when assignments are applied
- ℹ️ Info messages with helpful tips
- ⚠️ Warning messages if templates are missing
- ❌ Error messages for invalid operations

## Future Enhancements (Optional)

Possible future improvements:
- **Copy template** - Duplicate a template as a starting point
- **Import/Export templates** - Save template sets for reuse
- **Visual schedule comparison** - Side-by-side view of multiple templates
- **Smart suggestions** - Auto-detect similar patterns and suggest templates

---

## Summary

The template-based TOU schedule feature transforms a tedious month-by-month editing process into a streamlined 3-step workflow:
1. **Define** your 2-3 unique schedules as named templates
2. **Edit** each template once
3. **Assign** templates to months with a single form

This matches the typical utility rate structure where only a few unique schedules exist across the year, making tariff creation much faster and more intuitive.

