# Tariff Rates Excel Download Feature

## Overview
Added functionality to download both energy and demand rate data as an Excel file with multiple sheets from the Energy Rates tab.

## Changes Made

### 1. Dependencies Added
- **File**: `requirements/base.txt` and `requirements.txt`
- **Added**: `openpyxl>=3.0.0` for Excel file generation

### 2. Helper Functions Created
- **File**: `src/utils/helpers.py`
- **Functions**:
  - `generate_energy_rates_excel(tariff_viewer, year=2025)` - Main function to generate Excel file with 8 sheets (energy + demand)
  - `generate_energy_rate_timeseries(tariff_viewer, year=2025)` - Generates full year of 15-minute interval timeseries data

### 3. UI Component Updates
- **File**: `src/components/energy_rates.py`
- **Added**: 
  - Import statements for datetime and new helper functions
  - `_render_excel_download_section(tariff_viewer)` - Renders the download interface
  - Integration into main `render_energy_rates_tab()` function

## Excel File Structure

The generated Excel file contains **8 sheets** with both energy and demand rate data:

### ENERGY RATES (Sheets 1-4)

#### Sheet 1: Energy Rate Table
- Contains data from "📊 Current Rate Table" (Energy)
- Columns:
  - TOU Period
  - Base Rate ($/kWh)
  - Adjustment ($/kWh)
  - Total Rate ($/kWh)
  - Months Present

#### Sheet 2: Weekday Energy Rates
- 12x24 matrix (Months x Hours)
- Rows: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
- Columns: 00:00 through 23:00 (hourly)
- Values: Energy rates in $/kWh

#### Sheet 3: Weekend Energy Rates
- Same structure as Weekday Energy Rates
- Contains weekend-specific energy rates

#### Sheet 4: Energy Timeseries
- Full year of data at 15-minute intervals
- Columns:
  - `timestamp`: Date and time (YYYY-MM-DD HH:MM:SS)
  - `energy_rate_$/kWh`: Corresponding energy rate for that timestamp
- Automatically accounts for:
  - Month
  - Hour of day
  - Weekday vs weekend
- Approximately 35,040 rows (365 days × 24 hours × 4 intervals per hour)

### DEMAND RATES (Sheets 5-8)

#### Sheet 5: Demand Rate Table
- Contains data from "📊 Current Demand Rate Table"
- Columns:
  - Demand Period
  - Base Rate ($/kW)
  - Adjustment ($/kW)
  - Total Rate ($/kW)
  - Months Present

#### Sheet 6: Weekday Demand Rates
- 12x24 matrix (Months x Hours)
- Rows: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
- Columns: 00:00 through 23:00 (hourly)
- Values: Demand rates in $/kW

#### Sheet 7: Weekend Demand Rates
- Same structure as Weekday Demand Rates
- Contains weekend-specific demand rates

#### Sheet 8: Flat Demand Rates
- Contains data from "📊 Seasonal/Monthly Flat Demand Rates"
- Rows: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
- Column: Rate ($/kW)
- Values: Monthly flat demand charges

## Usage

1. Navigate to the **⚡ Energy Rates** tab
2. At the bottom of the page, you'll see **📥 Download Rate Data (Energy & Demand)** section
3. Select the year for timeseries generation (default: current year)
4. Click **📥 Download Excel File** button
5. Excel file will be downloaded with filename format: `Tariff_Rates_{Utility}_{Rate}_{Date}.xlsx`

## Features

- **Comprehensive Data Export**: Includes both energy and demand rate information
- **Dynamic Year Selection**: Choose any year from 2020-2050 for energy timeseries data
- **Smart Filename**: Automatically generates clean filename based on utility name, rate name, and current date
- **Error Handling**: Graceful error handling with user-friendly error messages
- **Info Panel**: Shows description of what each of the 8 sheets contains
- **Clean Data**: Properly formatted headers and data structure for easy analysis in Excel
- **Handles Missing Data**: Gracefully handles tariffs that may not have all rate types

## Technical Details

- Uses `openpyxl` engine for Excel generation
- Generates data in-memory using `io.BytesIO()` for efficient processing
- Timeseries generation uses datetime calculations for accurate timestamp mapping
- Rate lookup logic correctly handles weekday/weekend differentiation
- Supports both modified and original tariff data

## Example Use Cases

1. **Comprehensive Tariff Analysis**: Import both energy and demand rates into Excel for pivot tables and custom analysis
2. **Load Profile Matching**: Use energy timeseries data to match with actual load profiles
3. **Rate Comparisons**: Export multiple tariffs and compare energy and demand charges side-by-side
4. **Billing Calculations**: Use timeseries energy rates with consumption data and demand rates with peak demand data
5. **Demand Charge Planning**: Analyze flat and time-of-use demand charges to optimize facility operations
6. **Documentation**: Include comprehensive rate data in reports and presentations

## Installation

If you're setting up a new environment, install the updated requirements:

```bash
pip install -r requirements.txt
# or
pip install -r requirements/base.txt
```

If you already have the environment set up:

```bash
pip install openpyxl>=3.0.0
```

## Files Modified

1. `requirements/base.txt` - Added openpyxl dependency
2. `requirements.txt` - Added openpyxl dependency
3. `src/utils/helpers.py` - Added Excel generation functions
4. `src/components/energy_rates.py` - Added download UI section

## Testing

The feature includes:
- Error handling for missing data
- Validation of year input
- Clean filename generation
- Proper DataFrame handling
- Memory-efficient file generation

No new tests were added, but the functions can be tested manually by:
1. Running the app
2. Loading a tariff file
3. Navigating to Energy Rates tab
4. Clicking download and verifying Excel file structure

