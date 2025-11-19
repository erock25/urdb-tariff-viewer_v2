# Load Factor Analysis Tool

## Overview

The Load Factor Analysis Tool has been added to the **Utility Cost Calculator** section of the URDB JSON Viewer application. This tool allows users to calculate the effective utility rate ($/kWh) at different load factors for any tariff.

## Location

The tool is accessible in the **💰 Utility Cost Calculator** tab as an expandable section titled **"🔍 Load Factor Rate Analysis Tool"**.

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
   - Specify percentage breakdown of energy consumption across all energy rate periods
   - Must sum to 100%
   - Total rates displayed include base rate + adjustments
   - Hover over (?) icon to see base rate and adjustment breakdown

### Calculated Load Factors

The tool calculates effective rates for the following load factors:
- 1%
- 5%
- 10%
- 20%
- 30%
- 50%
- 100%

### How It Works

For each load factor:

1. **Average Load** = Peak Demand × Load Factor
2. **Total Energy** = Average Load × Hours in Month
3. **Demand Charges** = Sum of (Demand × Rate) for all specified demand periods
4. **Energy Charges** = Sum of (Energy in Period × Rate) for all energy periods
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

