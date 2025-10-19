# URDB Tariff Viewer & Editor v2.0

A comprehensive, modular Streamlit application for viewing and editing utility rate structures from the U.S. Utility Rate Database (URDB). This application provides interactive visualizations, editing capabilities, cost calculations, and load profile generation for utility rate analysis.

## ✨ New in Version 2.0

- **🏗️ Modular Architecture**: Complete restructure for better team collaboration and maintainability
- **🧪 Comprehensive Testing**: Full test suite with pytest integration
- **💰 Enhanced Cost Calculator**: Advanced utility bill calculations with load profile analysis
- **🔧 Load Profile Generator**: Create synthetic load profiles aligned with TOU periods
- **📊 Advanced Analytics**: Detailed load profile analysis and comparison tools
- **🎨 Modern UI**: Updated styling with improved user experience
- **⚙️ Better Configuration**: Centralized settings and environment management
- **🛠️ Tariff Builder**: NEW! Create custom tariff JSON files from scratch through an intuitive GUI

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

### 💰 Utility Cost Calculator
- **Bill Calculations**: Calculate annual utility costs using real load profiles
- **Cost Breakdowns**: Detailed analysis of energy, demand, and fixed charges
- **Multiple Tariff Comparison**: Compare costs across different rate schedules
- **Export Results**: Download calculation results in multiple formats

### 🔧 Load Profile Generator
- **Synthetic Profiles**: Generate realistic load profiles based on TOU periods
- **Customizable Parameters**: Adjust load factor, seasonal variation, and daily patterns
- **Validation Tools**: Ensure generated profiles meet specified criteria
- **Export Capabilities**: Save generated profiles for use in cost calculations

### 📊 Advanced Visualizations
- **Interactive Heatmaps**: Modern, responsive rate visualizations
- **Load Duration Curves**: Analyze load profile characteristics
- **Cost Comparison Charts**: Visual comparison of tariff options
- **Dark Mode Support**: Toggle between light and dark themes

### 🛠️ Tariff Builder (NEW!)
- **Create Custom Tariffs**: Build new tariff JSON files from scratch through an intuitive GUI
- **Wizard Interface**: 7-section guided workflow for easy tariff creation
- **Visual Schedule Editor**: Set time-of-use schedules with simple or advanced modes
- **Real-time Validation**: Ensure tariff data is complete and properly formatted
- **Schedule Preview**: Visual heatmap showing your complete TOU schedule
- **Save & Export**: Save to user_data directory or download directly
- **URDB Compatible**: Creates properly formatted URDB JSON files
- **No JSON Editing Required**: Build complex tariffs without manual file editing

📚 **Documentation**: See `TARIFF_BUILDER_GUIDE.md` for detailed instructions and `TARIFF_BUILDER_QUICK_REFERENCE.md` for quick tips

## Installation

### Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd URDB_JSON_Viewer_v2
```

2. Install dependencies:
```bash
pip install -r requirements/base.txt
```

3. Run the application:
```bash
streamlit run src/main.py
```

### Development Setup

For development with testing and code quality tools:

```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
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

### Creating New Tariffs (Tariff Builder)
1. **Access the Builder**: Navigate to the "🏗️ Tariff Builder" tab
2. **Basic Information**: Fill in utility name, rate name, sector, and description
3. **Energy Rates**: Define your TOU periods and rates ($/kWh)
4. **Schedule Configuration**: Set when each rate period applies (Simple or Advanced mode)
5. **Optional Charges**: Add demand charges, flat demand, and fixed charges as needed
6. **Validate & Save**: Review your configuration and save to user_data directory
7. **Use Your Tariff**: Refresh the page and select your new tariff from the sidebar

📖 **Detailed Guide**: See `TARIFF_BUILDER_GUIDE.md` for comprehensive instructions  
⚡ **Quick Start**: See `TARIFF_BUILDER_QUICK_REFERENCE.md` for a 5-minute tutorial

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
