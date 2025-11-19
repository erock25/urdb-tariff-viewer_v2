# Tariff Builder Recent Updates Summary

## Overview
This document summarizes the recent enhancements made to the Tariff Builder component to improve user experience and reduce configuration time.

## Features Added

### 1. Same Weekday/Weekend Schedule Option (Energy & Demand)
**Location**: Advanced schedule editors for both energy and demand rates

**What it does:**
- Adds a checkbox: "Weekday and weekend schedules are the same"
- When checked, users only need to configure the weekday schedule
- Weekend schedule automatically matches weekday schedule
- Eliminates redundant configuration for tariffs with identical schedules

**Benefits:**
- Reduces configuration time by ~50% for applicable tariffs
- Prevents inconsistencies between weekday and weekend schedules
- Clearer workflow with contextual messaging

**Files Modified:**
- `src/components/tariff_builder.py`
  - `_render_advanced_schedule_editor()` - Energy schedules
  - `_render_advanced_demand_schedule_editor()` - Demand schedules
  - `_apply_templates_to_schedule()` - Core application logic

### 2. Zero-Rate Period Hint for TOU Demand Charges
**Location**: Demand Charge Structure section, after "Number of Demand Periods" input

**What it does:**
- Displays an informative tip about including zero-rate periods
- Explains that $0.00 rate periods can be used for non-charged hours
- Clarifies distinction between TOU and flat monthly demand charges

**Hint Text:**
> 💡 **Tip**: If your tariff has hours when no TOU-based demand charge applies (separate from flat monthly demands), include a period with a $0.00 rate. This allows you to schedule those zero-charge hours in the demand schedule below.

**Benefits:**
- Guides users on proper configuration of partial-day demand charges
- Prevents confusion about how to handle non-charged hours
- Reduces configuration errors

**Files Modified:**
- `src/components/tariff_builder.py`
  - `_render_demand_charges_section()`

### 3. Demand Period Labels
**Location**: TOU Demand Charge Structure section

**What it does:**
- Adds "Period Label" text input for each demand period
- Stores labels in `demandlabels` array (matching URDB format)
- Displays labels throughout all demand schedule interfaces
- Defaults to "Period {i}" if not specified

**Where Labels Appear:**
- Demand period configuration expanders
- Simple mode: hour-by-hour schedule selectors
- Advanced mode: template editor selectors
- Schedule preview: heatmap legends
- Current schedule displays

**Example Labels:**
- "Peak" for high-rate periods
- "Mid-Peak" for shoulder periods
- "Off-Peak" for low-rate periods
- "No Charge" for zero-rate periods

**Benefits:**
- Improved clarity and readability
- Matches existing energy rate label functionality
- Better documentation of tariff structure
- Reduces chance of configuration errors

**Files Modified:**
- `src/components/tariff_builder.py`
  - `_render_demand_charges_section()` - Label input fields
  - `_render_simple_demand_schedule_editor()` - Use labels in selectors
  - `_render_template_editor()` - Use labels in template editor
  - Demand schedule preview section - Use labels in legends

## Data Structure Changes

### New/Updated Fields

#### Energy Schedules
- `energy_schedule_same_for_weekday_weekend` (session state): Boolean flag

#### Demand Schedules
- `demand_schedule_same_for_weekday_weekend` (session state): Boolean flag
- `demandlabels` (URDB field): List[str] - Custom labels for each demand period

## Backward Compatibility

All features are backward compatible:
- Same schedule checkboxes default to unchecked (original behavior)
- Zero-rate hint is informational only
- Demand labels default to "Period {i}" if not present
- Existing tariff files load without issues

## User Workflow Improvements

### Before
1. Configure weekday energy schedule (3 steps)
2. Switch to weekend, configure again (3 steps)
3. Configure weekday demand schedule (3 steps)
4. Switch to weekend, configure again (3 steps)
5. Work with generic "Period 0, 1, 2" labels throughout
6. Potentially confused about zero-charge hours

### After
1. Check "same schedule" if applicable
2. Configure weekday schedule once (3 steps)
3. Weekend automatically matches
4. Use meaningful labels like "Peak", "Off-Peak", "No Charge"
5. Clear guidance on zero-rate period usage

**Time Saved**: Up to 50% reduction in configuration time for typical tariffs

## Documentation

- `SAME_SCHEDULE_FEATURE.md` - Detailed documentation of same schedule feature
- `DEMAND_PERIOD_LABELS_FEATURE.md` - Detailed documentation of demand labels
- `TARIFF_BUILDER_UPDATES_SUMMARY.md` - This summary document

## Testing Status

All changes:
- ✅ Pass Python compilation
- ✅ Pass linter checks
- ✅ Maintain backward compatibility
- ✅ Follow existing code patterns
- ✅ Include appropriate user hints and help text

## Future Enhancement Ideas

- Bidirectional schedule sync (weekend → weekday)
- Warning when enabling "same schedule" with different existing schedules
- Label templates/presets for common tariff structures
- Bulk copy/paste operations for schedules
- Visual comparison of weekday vs weekend schedules

