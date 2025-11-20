# OpenEI Tariff Import Feature

## Overview

The URDB Tariff Viewer now supports importing tariffs directly from the OpenEI (Open Energy Information) API. This feature allows users to quickly fetch and save tariff data from OpenEI's extensive Utility Rate Database.

## Features

- 🌐 **Direct API Integration**: Fetch tariffs directly from OpenEI's API
- 🔐 **Flexible API Key Configuration**: Use environment variable or input directly in the app
- 💾 **Automatic Saving**: Imported tariffs are automatically saved to the user_data directory
- ✨ **Smart Naming**: Files are automatically named using utility and rate name
- 🔄 **Duplicate Handling**: Automatic numbering if a tariff with the same name already exists

## Setup

### Option 1: Streamlit Secrets (Recommended)

Store your API key in Streamlit's secrets file:

1. Create a `.streamlit` directory in your project root (if it doesn't exist)
2. Create a file named `secrets.toml` inside the `.streamlit` directory
3. Add your API key:

```toml
# .streamlit/secrets.toml
OPENEI_API_KEY = "your_api_key_here"
```

**Benefits:**
- ✅ Secure and persistent
- ✅ Not tracked by git (automatically ignored)
- ✅ Works across all sessions
- ✅ Standard Streamlit practice

### Option 2: Environment Variable

Set the `OPENEI_API_KEY` environment variable:

**Windows (PowerShell):**
```powershell
$env:OPENEI_API_KEY = "your_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set OPENEI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export OPENEI_API_KEY="your_api_key_here"
```

### Option 3: Direct Input in App

If no API key is configured via secrets or environment variable, the app will display an input field where you can paste your API key.

### Option 4: Override Configured Key

Even if you have a key configured via secrets or environment variable, you can enter a different key directly in the app to temporarily override it.

### Getting an API Key

1. Visit [OpenEI API Signup](https://openei.org/services/api/signup/)
2. Register for a free API key
3. Copy your API key and configure it using one of the methods above

## Usage

### Finding Tariff IDs

1. Browse tariffs at [OpenEI Utility Rate Database](https://openei.org/wiki/Utility_Rate_Database)
2. When you find a tariff you want to import, copy its ID from the URL or tariff page
   - Example ID: `674e0b87201c6bd096007a5a`

### Importing a Tariff

1. Open the URDB Tariff Viewer application
2. In the sidebar, navigate to the **"🌐 Import from OpenEI"** section
3. Enter or verify your API key (if not set via environment variable)
4. Paste the tariff ID in the **"Tariff ID"** field
5. Click **"📥 Import Tariff"**
6. Wait for the import to complete
7. The tariff will be saved to `data/user_data/` with a descriptive filename
8. Refresh the page or reselect to see the new tariff in the dropdown

### Example

**Tariff ID:** `674e0b87201c6bd096007a5a`

After import, the file will be saved as:
```
data/user_data/Utility_Name_Rate_Name.json
```

## Technical Details

### API Endpoint

- **URL**: `https://api.openei.org/utility_rates`
- **Version**: 7
- **Detail Level**: full

### Request Parameters

- `version`: API version (7)
- `format`: json
- `api_key`: Your OpenEI API key
- `getpage`: Tariff ID to fetch
- `detail`: Level of detail (full)

### File Naming

Files are automatically named using:
```
{utility_name}_{rate_name}.json
```

Special characters are replaced with underscores for filesystem compatibility.

### Duplicate Handling

If a file with the same name already exists, a number suffix is automatically added:
```
Utility_Name_Rate_Name_1.json
Utility_Name_Rate_Name_2.json
```

## Error Handling

The feature includes comprehensive error handling for:

- ❌ **Invalid API Key**: Displays clear message to check your API key
- ❌ **Tariff Not Found**: Indicates the tariff ID doesn't exist
- ❌ **Network Errors**: Handles connection issues and timeouts
- ❌ **API Errors**: Displays specific error codes and messages

## Troubleshooting

### "Invalid API key" Error

- Verify your API key is correct
- Check that there are no extra spaces or characters
- Try registering for a new API key at OpenEI

### "Tariff not found" Error

- Verify the tariff ID is correct
- Check that the tariff still exists on OpenEI
- Try browsing OpenEI to find the correct ID

### Connection Errors

- Check your internet connection
- Verify you can access https://api.openei.org in your browser
- Check if a firewall is blocking the request

### Import Button Disabled

The import button is only enabled when:
- ✅ API key is provided (via environment or input)
- ✅ Tariff ID is entered

## Dependencies

The feature requires the `requests` library:

```
requests>=2.31.0
```

This is automatically included in `requirements.txt`.

## Files Modified

- `src/components/sidebar.py`: Added import section and functions
- `src/config/settings.py`: Added OpenEI API configuration
- `requirements.txt`: Added requests dependency

## Future Enhancements

Potential improvements for future versions:

- 🔍 Search functionality within the app
- 📋 Batch import of multiple tariffs
- 🔄 Update existing tariffs from OpenEI
- 📊 Preview tariff details before importing
- 💾 Import history tracking

## Related Resources

- [OpenEI Website](https://openei.org/)
- [OpenEI Utility Rate Database](https://openei.org/wiki/Utility_Rate_Database)
- [OpenEI API Documentation](https://openei.org/services/doc/rest/util_rates/)
- [API Key Signup](https://openei.org/services/api/signup/)

