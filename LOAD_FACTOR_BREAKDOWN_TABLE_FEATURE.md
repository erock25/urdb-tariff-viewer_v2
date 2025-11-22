# Load Factor Comprehensive Breakdown Table Feature

## Overview

Added a comprehensive breakdown table to the **Load Factor Rate Analysis Tool** in the Utility Cost Analysis. This new table appears below the "Effective Rate vs Load Factor" chart and provides complete visibility into energy and demand cost components for **all load factors** in a single wide table.

## Location

The comprehensive breakdown table is located in the **💰 Utility Cost Analysis** tab, within the **"🔍 Load Factor Rate Analysis Tool"** expandable section, positioned directly below the "Effective Rate vs Load Factor" chart.

## New Features

### Comprehensive Breakdown Table
A single, wide table that shows **all load factors** with detailed breakdowns including:

#### Base Columns (from Detailed Results Table):
- **Load Factor**: Load factor percentage (1% to 100%)
- **Average Load (kW)**: Average load at this load factor
- **Total Energy (kWh)**: Total energy consumption

#### Energy Rate Period Columns (for each period):
For **every** energy rate period in the tariff:
- **[Period Name] (kWh)**: Energy consumption in this period
- **[Period Name] Rate ($/kWh)**: Energy rate for this period (base rate + adjustments)
- **[Period Name] Cost ($)**: Energy cost for this period

**Important:** All energy periods are shown, even if not present in the selected month (shows 0 kWh). Rates are always displayed for all periods.

#### TOU Demand Period Columns (for each period):
For **every** TOU demand period in the tariff:
- **[Period Name] Demand (kW)**: Demand value for this period
- **[Period Name] Rate ($/kW)**: Demand rate for this period (base rate + adjustments)
- **[Period Name] Demand Cost ($)**: Demand cost for this period

**Important:** All TOU demand periods are shown (shows 0 kW if not specified). Rates are always displayed for all periods.

#### Flat Demand Columns (if applicable):
- **Flat Demand (kW)**: Monthly flat demand value
- **Flat Demand Rate ($/kW)**: Flat demand rate (base rate + adjustments, varies by month for some tariffs)
- **Flat Demand Cost ($)**: Flat demand charge

#### Summary Columns:
- **Total Demand Charges ($)**: Sum of all demand charges
- **Total Energy Charges ($)**: Sum of all energy charges
- **Fixed Charges ($)**: Fixed monthly charges
- **Total Cost ($)**: Complete monthly cost
- **Effective Rate ($/kWh)**: Cost per kWh at this load factor

## Technical Implementation

### New Functions

#### `_calculate_comprehensive_load_factor_breakdown()`
**Location:** `src/components/cost_calculator.py`

**Purpose:** Calculates comprehensive breakdown with all load factors and detailed rate components for all periods.

**Parameters:**
- `results`: Original results DataFrame from load factor calculations
- `tariff_data`: Tariff data dictionary
- `demand_inputs`: User-specified demand values for each period
- `energy_percentages`: User-specified energy distribution percentages
- `selected_month`: Month index (0-11)
- `has_tou_demand`: Whether tariff has TOU demand charges
- `has_flat_demand`: Whether tariff has flat demand charges

**Returns:**
- Wide DataFrame with one row per load factor and columns for all rate components

**Key Logic:**
- Iterates through all load factors from the original results
- For each load factor:
  - Calculates energy breakdown for **all** energy periods (not just active ones)
  - Includes **all** TOU demand periods
  - Includes flat demand if applicable
  - Respects the same energy distribution logic as main calculations:
    - Below max valid load factor: Uses user-specified energy percentages
    - Above max valid load factor: Uses hour percentages (24/7 operation)
  - Periods not present in the selected month show 0 kWh or 0 kW
- Includes total rates (base rate + adjustments) for all calculations
- Uses proper period labels from tariff data

### Modified Functions

#### `_display_load_factor_results()`
**Location:** `src/components/cost_calculator.py`

**Changes:**
1. **Updated function signature** to accept additional optional parameters:
   - `tariff_data`, `demand_inputs`, `energy_percentages`
   - `selected_month`, `has_tou_demand`, `has_flat_demand`

2. **Added comprehensive breakdown section** after the chart:
   - Conditional rendering (only if tariff data is available)
   - Single wide table showing all load factors
   - Dynamically builds column configuration for all periods
   - Adaptive height based on number of load factors
   - Horizontal scrolling enabled for wide tables

#### `_render_load_factor_analysis_tool()`
**Location:** `src/components/cost_calculator.py`

**Changes:**
- Updated call to `_display_load_factor_results()` to pass additional parameters needed for comprehensive breakdown table generation

## User Experience

### Workflow
1. User configures demand inputs and energy distribution in the Load Factor Analysis Tool
2. Clicks "Calculate Effective Rates"
3. Views summary metrics and detailed results table (existing features)
4. Views "Effective Rate vs Load Factor" chart (existing feature)
5. **NEW:** Below the chart, views comprehensive breakdown table showing:
   - All calculated load factors in rows
   - All base metrics (Average Load, Total Energy)
   - Energy consumption and cost for **every** energy rate period
   - Demand and cost for **every** TOU demand period
   - Flat demand and cost (if applicable)
   - Complete summary columns (Total Demand, Total Energy, Fixed, Total Cost, Effective Rate)

### Benefits
- **Complete Visibility**: All load factors and all rate components in one table
- **Easy Comparison**: Compare energy distribution across load factors side-by-side
- **Period Coverage**: See all periods (even inactive ones) for complete understanding
- **Data Export**: Can easily copy/export entire table for external analysis
- **Validation**: Quickly verify energy distribution and demand charge calculations
- **Transparency**: Every rate component broken down for all load factors

## Example Use Cases

### 1. Complete Energy Distribution Analysis
User can see at a glance:
- How energy is distributed across all TOU periods at each load factor
- Which periods show 0 kWh (not present in selected month)
- How distribution changes from user-specified (below max valid LF) to hour-based (at 100% LF)
- Cost contribution of each energy period at different load factors

### 2. Comprehensive Demand Cost Analysis
User can see in one table:
- All TOU demand periods and their costs (constant across load factors)
- Flat demand and its cost (constant across load factors)
- Total demand charges at each load factor
- How demand charges compare to energy charges

### 3. Load Factor Optimization
User can:
- Identify which load factor provides the best effective rate
- See exactly how costs break down at optimal load factor
- Compare energy vs. demand cost ratios at different load factors
- Analyze cost trends across the full load factor range

### 4. Tariff Understanding
User can:
- See all available energy periods in the tariff structure
- Identify which periods are active in the selected month (non-zero kWh)
- Understand the complete rate structure at a glance
- Validate that their inputs are being applied correctly

## Data Consistency

The comprehensive breakdown table calculations are **identical** to those used in the main load factor analysis:
- Uses same rate structures and adjustments
- Respects same energy distribution logic (user percentages vs. hour percentages)
- Matches the "Energy Charges ($)" and "Demand Charges ($)" shown in the results table
- All period costs sum to total charges
- Ensures complete transparency and accuracy

## Formatting

### Table Structure
- Single wide table with horizontal scrolling support
- All load factors shown as rows
- Columns organized in logical groups:
  1. Base metrics (Load Factor, Average Load, Total Energy)
  2. Energy period details (kWh and Cost for each period)
  3. TOU demand details (kW and Cost for each period)
  4. Flat demand details (kW and Cost)
  5. Summary totals (Total Demand, Total Energy, Fixed, Total Cost, Effective Rate)

### Column Configuration
- **Numeric columns**: Properly formatted with appropriate decimal places
  - Energy values: No decimals (e.g., "1,234 kWh")
  - Demand values: 2 decimals (e.g., "100.00 kW")
  - Cost values: 2 decimals with $ prefix (e.g., "$123.45")
  - Effective rate: 4 decimals with $ prefix (e.g., "$0.1234/kWh")
- **Column widths**: Optimized for readability
  - Small width for compact columns (Load Factor, individual periods)
  - Medium width for summary columns
- **Hidden index**: Cleaner table appearance

### Dynamic Features
- **Adaptive height**: Table height adjusts based on number of load factors
- **Horizontal scrolling**: Enabled for tables with many periods
- **Column headers**: Clear, concise labels for all periods
- **Help text**: Caption explains that inactive periods show 0 values
- **Excel Export**: Download buttons for both Detailed Results and Comprehensive Breakdown tables

### Visual Design
- Consistent with existing application styling
- Professional formatting throughout
- Easy to read and interpret
- Optimized for data export and analysis

## Excel Export Functionality

Both tables include Excel export capabilities for further analysis:

### 1. Detailed Results Table Export
- **Button**: "📥 Download Detailed Results as Excel"
- **File name**: `load_factor_detailed_results.xlsx`
- **Sheet name**: "Load Factor Analysis"
- **Contents**: All columns from the Detailed Results Table
  - Load Factor, Average Load (kW), Total Energy (kWh)
  - Demand Charges ($), Energy Charges ($), Fixed Charges ($)
  - Total Cost ($), Effective Rate ($/kWh)

### 2. Comprehensive Breakdown Table Export
- **Button**: "📥 Download Comprehensive Breakdown as Excel"
- **File name**: `load_factor_comprehensive_breakdown.xlsx`
- **Sheet name**: "Comprehensive Breakdown"
- **Contents**: Complete breakdown with all periods
  - All base columns
  - All energy period columns (kWh and Cost)
  - All TOU demand columns (kW and Cost)
  - Flat demand columns (if applicable)
  - All summary columns

### Export Features
- **One-click download**: Click button to immediately download Excel file
- **Excel format (.xlsx)**: Compatible with Microsoft Excel, Google Sheets, LibreOffice, etc.
- **Preserves data**: All values exported exactly as displayed
- **No formatting**: Raw numerical data for easy analysis
- **Ready for analysis**: Import into other tools, create pivot tables, generate charts

## Notes

- The comprehensive breakdown table only appears when tariff data and inputs are available
- Shows all load factors from 1% to max valid LF, plus 100% (typically 51-101 rows)
- **All** energy and demand periods are included, regardless of whether they're active in the selected month
- Inactive periods (not present in selected month) show 0 kWh or 0 kW
- All rates shown include base rates + adjustments for consistency
- Energy distribution respects the same logic as the main calculation engine:
  - Below max valid LF: Uses user-specified percentages
  - At 100% LF: Uses hour percentages (24/7 operation)
- Table can be scrolled horizontally to view all columns
- Data can be easily copied/exported for external analysis
- Demand values and costs remain constant across all load factors (as expected)
- Excel files are generated dynamically and downloaded directly to browser's default download location

