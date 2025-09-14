# Migration Guide: URDB Tariff Viewer v1 → v2

This guide explains the changes in version 2.0 and how to migrate from the old monolithic structure to the new modular architecture.

## 🎯 Overview of Changes

Version 2.0 represents a complete architectural overhaul of the URDB Tariff Viewer, transforming it from a single 3,333-line file into a well-organized, modular application.

## 📁 Directory Structure Changes

### Before (v1.x)
```
URDB_JSON_Viewer_v2/
├── app.py (3,333 lines - everything!)
├── calculate_utility_bill.py
├── tariffs/ (sample files)
├── load_profiles/
├── user_tariffs/
├── Archive/ (old versions)
└── requirements.txt
```

### After (v2.0)
```
URDB_JSON_Viewer_v2/
├── src/
│   ├── main.py (new entry point)
│   ├── models/ (data models)
│   ├── services/ (business logic)
│   ├── components/ (UI components)
│   ├── utils/ (utilities)
│   └── config/ (settings)
├── data/ (consolidated data files)
├── tests/ (comprehensive testing)
├── requirements/ (organized dependencies)
├── docs/ (documentation)
└── pyproject.toml (modern config)
```

## 🔄 How to Use the New Structure

### Running the Application

**Old way:**
```bash
streamlit run app.py
```

**New way:**
```bash
# Option 1: Direct
streamlit run src/main.py

# Option 2: Using launcher script
python run_app.py

# Option 3: Development mode
pip install -e .
urdb-viewer
```

### Development Workflow

**Old way:**
- Edit the massive `app.py` file
- All changes in one place
- Difficult to work in teams

**New way:**
```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Run tests
pytest

# Check code quality
black src/ tests/
mypy src/

# Work on specific components
# - Edit models: src/models/
# - Edit UI: src/components/
# - Edit business logic: src/services/
```

## 🧩 Component Mapping

Here's where the old code moved in the new structure:

### TariffViewer Class
- **Old**: Lines 13-581 in `app.py`
- **New**: `src/models/tariff.py`
- **Changes**: Better organized methods, improved documentation

### Load Profile Generation
- **Old**: Lines 613-748 in `app.py` 
- **New**: `src/models/load_profile.py`
- **Changes**: Class-based approach, better validation

### CSS Styling
- **Old**: Lines 759-1143 in `app.py`
- **New**: `src/utils/styling.py`
- **Changes**: Organized functions, theme management

### Main UI Logic
- **Old**: Lines 750-3489 in `app.py`
- **New**: Split across:
  - `src/main.py` (main entry point)
  - `src/components/sidebar.py`
  - `src/components/energy_rates.py`
  - `src/components/demand_rates.py`
  - `src/components/cost_calculator.py`
  - `src/components/load_generator.py`

### File Operations
- **Old**: Scattered throughout `app.py`
- **New**: `src/services/file_service.py`
- **Changes**: Centralized, better error handling

## 🔧 Configuration Changes

### Dependencies
- **Old**: Single `requirements.txt`
- **New**: Organized in `requirements/`:
  - `base.txt` - Core dependencies
  - `dev.txt` - Development tools
  - `prod.txt` - Production-specific

### Settings
- **Old**: Hardcoded values throughout code
- **New**: Centralized in `src/config/`:
  - `settings.py` - Application settings
  - `constants.py` - Constants and defaults

### Streamlit Configuration
- **Old**: No configuration file
- **New**: `.streamlit/config.toml` with optimized settings

## 🧪 Testing

### Old Structure
- **Testing**: Basic `test_app.py` (12 lines)
- **Coverage**: Minimal

### New Structure
- **Testing**: Comprehensive test suite in `tests/`
- **Coverage**: >80% target with pytest-cov
- **Structure**:
  - `tests/conftest.py` - Shared fixtures
  - `tests/test_models/` - Model tests
  - `tests/test_services/` - Service tests
  - `tests/test_components/` - UI component tests

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📊 Benefits of Migration

### For Individual Developers
1. **Faster Development**: Smaller files load and edit faster
2. **Better IDE Support**: Improved autocomplete and navigation
3. **Easier Debugging**: Issues isolated to specific modules
4. **Code Reuse**: Services and utilities can be reused

### For Teams
1. **Parallel Development**: Multiple developers can work simultaneously
2. **Cleaner Merges**: Smaller files reduce merge conflicts
3. **Focused Reviews**: PRs target specific functionality
4. **Onboarding**: New team members understand structure faster

### For Maintenance
1. **Easier Updates**: Changes isolated to relevant modules
2. **Better Testing**: Comprehensive test coverage
3. **Documentation**: Better organized and maintained
4. **Deployment**: More flexible deployment options

## 🚀 Migration Checklist

If you're migrating custom changes from v1 to v2:

- [ ] **Data Files**: Move your custom tariffs to `data/user_data/`
- [ ] **Load Profiles**: Move CSV files to `data/load_profiles/`
- [ ] **Custom Code**: Identify which module your changes belong in
- [ ] **Dependencies**: Update to use new requirements structure
- [ ] **Scripts**: Update any automation scripts to use new entry point
- [ ] **Documentation**: Update any internal documentation

## 🆘 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Make sure you're running from the project root directory

**Issue**: Import errors in new structure
**Solution**: Check that `__init__.py` files exist in all packages

**Issue**: Missing dependencies
**Solution**: Install using `pip install -r requirements/base.txt`

**Issue**: Tests not running
**Solution**: Install dev dependencies: `pip install -r requirements/dev.txt`

### Getting Help

1. **Check the logs**: Streamlit provides detailed error messages
2. **Run tests**: `pytest -v` to see what's working
3. **Validate setup**: Use the launcher script `python run_app.py`
4. **Compare structure**: Ensure your setup matches the new directory structure

## 📈 Future Roadmap

The new modular structure enables future enhancements:

- **Plugin System**: Easy to add new tariff formats
- **API Integration**: RESTful API for programmatic access
- **Advanced Analytics**: Machine learning for load forecasting
- **Multi-user Support**: User authentication and data isolation
- **Cloud Deployment**: Better suited for containerized deployment

---

**Need Help?** The new structure is designed to be more maintainable and easier to understand. Each module has clear documentation and focused responsibility.
