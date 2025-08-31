# URDB Tariff Viewer & Editor

A comprehensive Streamlit application for viewing and editing utility rate structures from the U.S. Utility Rate Database (URDB). This application provides interactive visualizations and editing capabilities for both energy and demand charge rate structures.

## Features

### ⚡ Energy Rate Management
- **Time-of-Use Energy Rates**: Interactive heatmaps showing energy rates ($/kWh) by hour and month
- **Weekday vs Weekend**: Separate visualizations for weekday and weekend energy rates
- **Real-time Editing**: Modify energy rates directly through the interface
- **Rate Statistics**: Summary metrics including highest, lowest, and average rates

### 🔌 Demand Charge Management
- **Time-of-Use Demand Rates**: Interactive heatmaps showing demand charges ($/kW) by hour and month
- **Seasonal Flat Demand Rates**: Bar charts displaying monthly flat demand rates
- **Demand Rate Editing**: Modify both time-of-use and flat demand rates
- **Demand Charge Details**: Comprehensive information about demand charge structures

### 📊 Advanced Visualizations
- **Combined Analysis**: Side-by-side comparison of energy vs demand rates
- **Rate Distribution**: Histograms showing the distribution of rates
- **Monthly Comparisons**: Line charts comparing average monthly rates
- **Dark Mode Support**: Toggle between light and dark themes

### 🎛️ Interactive Controls
- **Rate Type Selection**: Choose between energy and demand rate editing
- **Time Selection**: Select specific months and hours for rate modifications
- **Day Type Selection**: Edit rates for weekdays or weekends
- **Real-time Updates**: See changes immediately in the visualizations

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd URDB_JSON_Viewer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

### Loading Tariff Files
- Place your URDB JSON files in the `tariffs/` subdirectory
- The application will automatically detect and list available tariff files
- Select a tariff file from the sidebar to begin analysis

### Editing Rates
1. **Select Rate Type**: Choose between "Energy" or "Demand" rates
2. **Choose Time Period**: Select month, hour, and day type (weekday/weekend)
3. **Modify Rate**: Enter the new rate value
4. **Apply Changes**: Click "Update Rate" to apply modifications
5. **Save Changes**: Use "Save Changes" to export modified tariffs

### Understanding the Visualizations
- **Energy Rates**: Displayed in $/kWh with blue color gradients
- **Demand Rates**: Displayed in $/kW with similar color schemes
- **Flat Demand Rates**: Monthly bar charts showing seasonal demand charges
- **Combined View**: Comparative analysis and rate distribution charts

## Data Structure Support

The application supports the following URDB JSON fields:

### Energy Rates
- `energyratestructure`: Rate structure with tiers and rates
- `energyweekdayschedule`: Weekday hourly schedule mapping
- `energyweekendschedule`: Weekend hourly schedule mapping

### Demand Charges
- `demandratestructure`: Demand rate structure with tiers and rates
- `demandweekdayschedule`: Weekday demand schedule mapping
- `demandweekendschedule`: Weekend demand schedule mapping
- `flatdemandstructure`: Seasonal/monthly flat demand rates
- `flatdemandmonths`: Month-to-period mapping for flat demand

### Additional Fields
- `demandrateunit`: Unit for demand charges (kW, kVA, etc.)
- `demandwindow`: Demand measurement window in minutes
- `demandratchetpercentage`: Demand ratchet percentages
- `demandreactivepowercharge`: Reactive power charges

## File Format

The application expects URDB JSON files in the standard format:
```json
{
  "items": [
    {
      "utility": "Utility Company Name",
      "name": "Rate Name",
      "sector": "Residential/Commercial/Industrial",
      "energyratestructure": [...],
      "demandratestructure": [...],
      "energyweekdayschedule": [...],
      "demandweekdayschedule": [...],
      ...
    }
  ]
}
```

## Output

Modified tariffs are saved to the `modified_tariffs/` directory with the prefix "modified_" added to the original filename.

## Requirements

- Python 3.8+
- Streamlit 1.26.0+
- Pandas 1.5.0+
- NumPy 1.23.0+
- Plotly 6.3.0+

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests to improve the application.

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Data visualization powered by [Plotly](https://plotly.com/)
- Based on the [U.S. Utility Rate Database](https://openei.org/wiki/Utility_Rate_Database) from OpenEI
