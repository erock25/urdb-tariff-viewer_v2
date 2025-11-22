# Load Factor Analysis Tool

## Overview

The Load Factor Analysis Tool has been added to the **Utility Cost Analysis** section of the URDB JSON Viewer application. This tool allows users to calculate the effective utility rate ($/kWh) at different load factors for any tariff.

## Location

The tool is accessible in the **💰 Utility Cost Analysis** tab as an expandable section titled **"🔍 Load Factor Rate Analysis Tool"**.

## Features

### Input Parameters

1. **Month Selection**: Choose the month of interest (affects hours in month for energy calculations)

2. **TOU Demand Charges** (if applicable):
   - Specify maximum demand (kW) for each TOU demand period
   - Total rates displayed include base rate + adjustments
   - Hover over (?) icon to see base rate and adjustment breakdown

3. **Flat Monthly Demand Charge** (if applicable):
   - Specify maximum monthly demand (kW)
   - Total rate displayed includes base rate + adjustments (varies by month for some tariffs)
   - Hover over (?) icon to see base rate and adjustment breakdown
   - **Auto-correction**: If entered value is less than the highest TOU demand, the calculation will automatically use the higher TOU value (with real-time notification)

4. **Energy Distribution**:
   - Specify percentage breakdown of energy consumption across energy rate periods
   - **Only shows periods that are scheduled in the selected month** (based on `energyweekdayschedule` and `energyweekendschedule`)
   - **Displays percentage of month's hours** each period is present (e.g., "📊 45.2% of month's hours")
   - Must sum to 100%
   - Total rates displayed include base rate + adjustments
   - Hover over (?) icon to see base rate and adjustment breakdown, plus hour percentage
   - Info message displays which periods (if any) are not present in the selected month

### Calculated Load Factors

The tool **dynamically** calculates effective rates based on your energy distribution:

**Load Factor Range:** 1% to Maximum Valid Load Factor (in 1% increments), plus 100%

**Maximum Valid Load Factor** is determined by which TOU periods you allocate energy to:
- If you allocate energy to periods representing 50% of hours → Max valid LF = 50%
- If you allocate energy to periods representing 85% of hours → Max valid LF = 85%
- If you allocate energy to all periods (100% of hours) → Max valid LF = 100%

**Example:** If you allocate 100% energy to Off-Peak (which is 50.5% of month's hours):
- Calculates: 1%, 2%, 3%, ..., 49%, 50% (using your distribution)
- Then: 100% (using hour percentages for constant operation)
- Total: 51 data points

### How It Works

For each load factor:

1. **Average Load** = Peak Demand × Load Factor
2. **Total Energy** = Average Load × Hours in Month
3. **Demand Charges** = Sum of (Demand × Rate) for all specified demand periods
4. **Energy Charges** = Sum of (Energy in Period × Rate) for all energy periods
   - **Up to Maximum Valid LF:** Uses your specified energy distribution (operational flexibility to choose when to run)
   - **Above Maximum Valid LF:** Automatically uses the TOU schedule's hour percentages (facility must operate during periods where you allocated 0% energy)
   - **Maximum Valid LF** = Sum of hour percentages for periods where you allocated energy > 0%
5. **Total Cost** = Demand Charges + Energy Charges + Fixed Charges
6. **Effective Rate** = Total Cost ÷ Total Energy ($/kWh)

## Output

### Summary Metrics
- Peak Demand (kW)
- Lowest Effective Rate ($/kWh) with corresponding load factor
- Highest Effective Rate ($/kWh) with corresponding load factor

### Detailed Results Table
Shows for each load factor:
- Average Load (kW)
- Total Energy (kWh)
- Demand Charges ($)
- Energy Charges ($)
- Fixed Charges ($)
- Total Cost ($)
- Effective Rate ($/kWh)

### Visualization
Dual-axis chart showing:
- **Left Y-axis (line)**: Effective Rate ($/kWh) vs Load Factor
- **Right Y-axis (stacked bars)**: Cost breakdown (Energy, Demand, Fixed) vs Load Factor

## Use Cases

1. **Rate Comparison**: Compare effective rates across different load factor scenarios
2. **Load Factor Optimization**: Identify optimal load factor for minimum effective rate
3. **Budgeting**: Estimate costs for different operational scenarios
4. **What-If Analysis**: Test various demand and energy distribution assumptions

## Example

For a tariff with:
- Flat demand charge: 100 kW @ $0/kW
- 100% energy in "Winter Super-Off-Peak" period @ $0.1179/kWh
- Fixed charge: $447.44/month
- Month: July (744 hours)

Results:
- 1% Load Factor: $0.7193/kWh (1 kW avg, 744 kWh)
- 50% Load Factor: $0.1299/kWh (50 kW avg, 37,200 kWh)
- 100% Load Factor: $0.1239/kWh (100 kW avg, 74,400 kWh)

Higher load factors result in lower effective rates because fixed charges are spread over more energy consumption.

## Technical Details

**Location in Code**: `src/components/cost_calculator.py`

**Main Functions**:
- `_get_active_energy_periods_for_month()`: Determines which energy periods are scheduled in a given month
- `_calculate_period_hour_percentages()`: Calculates what percentage of the month's hours each period is present
- `_render_load_factor_analysis_tool()`: UI rendering
- `_calculate_load_factor_rates()`: Calculation logic
- `_display_load_factor_results()`: Results display

**Dependencies**:
- Streamlit (UI)
- Pandas (data handling)
- Plotly (visualizations)

## Notes

- The tool is available regardless of whether a load profile is loaded
- Energy percentages must sum to exactly 100%
- At least one demand value must be specified to calculate results
- The tool uses the currently selected tariff's rate structures
- **All displayed rates are total rates** (base rate + adjustments) for transparency and consistency
- Hover tooltips show the breakdown of base rate and adjustments for each charge
- All calculations use the total rates (base + adjustment)
- **Month-varying rates**: Some tariffs have different flat demand rates for different months (e.g., summer vs winter) - the tool automatically uses the correct rate based on selected month
- **Auto-correction**: When both TOU and flat demand charges exist, if flat monthly demand is entered as less than the highest TOU demand, the calculation will automatically use the higher TOU value (with a real-time blue info notification appearing immediately)
- **Intelligent Period Filtering**: The tool automatically parses the tariff's TOU schedule and only displays energy periods that are actually scheduled in the selected month. For example, if a tariff has separate summer and winter periods, only the relevant periods will be shown based on the selected month. An info message will indicate which periods (if any) are excluded.
- **Hour Percentage Labels**: Each energy period displays what percentage of the month's hours it occupies. This helps users understand the actual time distribution. For example, if "On-Peak" shows "📊 12.4% of month's hours", users know that this period only occurs for about 3 hours per day on average. The percentages account for both weekday and weekend schedules and the actual number of weekdays/weekends in the selected month.
- **Dynamic Load Factor Range**: The tool intelligently calculates load factors based on your energy distribution. If you only allocate energy to periods representing 50% of the month's hours, calculations are performed from 1-50% LF (using your distribution), then 100% LF (using hour percentages). This prevents physically impossible scenarios where the facility would need to operate during periods where you allocated 0% energy. The maximum valid load factor equals the sum of hour percentages for periods where you allocated energy.

