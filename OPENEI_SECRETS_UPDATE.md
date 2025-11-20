# OpenEI Import - Secrets.toml Integration Update

## Summary of Changes

Updated the OpenEI import feature to use Streamlit's `secrets.toml` as the primary method for storing the API key, with the ability for users to override it by entering their own key.

## What Changed

### 1. API Key Priority Order

The app now checks for API keys in this order:

1. **User-entered key in the app** (highest priority - overrides everything)
2. **Streamlit secrets** (`.streamlit/secrets.toml`)
3. **Environment variable** (`OPENEI_API_KEY`)
4. **Manual entry required** (if none of the above are found)

### 2. Updated Behavior

#### When API Key is Configured (secrets.toml or environment)
- ✅ Shows success message: "API Key configured (using secrets.toml or environment)"
- 💡 Displays hint: "Enter a key below to override the configured key"
- 📝 Shows input field labeled "Override API Key (optional):"
- 🔄 Uses user-entered key if provided, otherwise uses configured key

#### When No API Key is Configured
- ℹ️ Shows info message with setup instructions
- 📝 Shows input field labeled "OpenEI API Key:"
- ⚠️ Requires user to enter key to proceed

## Files Modified

### 1. `src/config/settings.py`
- Updated `get_openei_api_key()` method to check Streamlit secrets first
- Falls back to environment variable if secrets not found
- Handles exceptions gracefully

### 2. `src/components/sidebar.py`
- Modified `_render_openei_import_section()` to handle both scenarios:
  - When API key is configured (shows override option)
  - When API key is not configured (requires entry)
- Updated UI messages and field labels

### 3. Documentation Files
- Updated `OPENEI_IMPORT_FEATURE.md` - Added secrets.toml as Option 1
- Updated `OPENEI_IMPORT_QUICK_START.md` - Made secrets.toml the recommended method
- Updated `OPENEI_IMPORT_IMPLEMENTATION_SUMMARY.md` - Documented new priority order
- Updated `OPENEI_IMPORT_VISUAL_GUIDE.md` - Updated UI states and flow diagrams

## New Files Created

### 1. `.streamlit/secrets.toml.example`
Example configuration file showing users how to set up their API key:

```toml
# Streamlit Secrets Configuration
OPENEI_API_KEY = "your_api_key_here"
```

### 2. `.streamlit/README.md`
Comprehensive guide for the `.streamlit` directory explaining:
- How to create `secrets.toml`
- How to get an API key
- Security considerations
- Quick setup instructions

## Setup Instructions for Users

### Quick Setup

1. **Create secrets file:**
   ```bash
   # In project root
   cd .streamlit
   cp secrets.toml.example secrets.toml
   ```

2. **Add your API key:**
   Edit `secrets.toml`:
   ```toml
   OPENEI_API_KEY = "paste_your_actual_api_key_here"
   ```

3. **Run the app:**
   ```bash
   streamlit run src/main.py
   ```

4. **The app will automatically use your configured key!** ✅

### Override Option

Even with a configured key, users can:
- Enter a different API key in the "Override API Key (optional)" field
- Test with different keys without changing `secrets.toml`
- Use temporary keys for specific imports

## Security Notes

- ✅ `.streamlit/secrets.toml` is already in `.gitignore` (line 48)
- ✅ API keys stored in secrets.toml will NOT be committed to version control
- ✅ Input field uses `type="password"` to hide the key
- ✅ Keys are only used for API requests and never logged or displayed

## Benefits of This Approach

### For Users
- 🎯 **Persistent**: Set once, works forever
- 🔒 **Secure**: Not committed to git
- ✨ **Standard**: Uses Streamlit's built-in secrets management
- 🔄 **Flexible**: Can override when needed
- 💻 **Simple**: Just one file to edit

### For Development
- 📁 **Organized**: Secrets in dedicated directory
- 🧪 **Testable**: Easy to use different keys for testing
- 🔧 **Maintainable**: Standard Streamlit pattern
- 📚 **Well-documented**: Extensive guides provided

## Comparison: Before vs After

### Before (Environment Variable Only)
```
User Experience:
1. User sets environment variable (session-only)
2. Must re-set each time PowerShell/terminal is reopened
3. Different for each OS (PowerShell vs bash vs cmd)
4. No easy way to override without changing environment

Developer Experience:
- Simple implementation
- Less secure (could be visible in process list)
- Not persistent
```

### After (Secrets.toml Primary)
```
User Experience:
1. User creates secrets.toml once
2. Works automatically in all sessions
3. Same process for all operating systems
4. Can override by entering key in app

Developer Experience:
- Standard Streamlit practice
- More secure (file-based, gitignored)
- Persistent across sessions
- Fallback to environment still available
```

## Testing Scenarios

### Scenario 1: Fresh Install
1. User clones repo
2. User creates `.streamlit/secrets.toml`
3. User adds API key
4. User runs app
5. ✅ App shows "API Key configured"
6. User can import tariffs immediately

### Scenario 2: Override Key
1. User has key in `secrets.toml`
2. App shows "API Key configured"
3. User wants to test different key
4. User enters new key in "Override" field
5. ✅ App uses override key for that session
6. Next session: Back to secrets.toml key

### Scenario 3: No Configuration
1. User runs app without secrets or env var
2. App shows info message
3. User enters key directly
4. ✅ User can import tariffs
5. But key is not saved (session-only)

### Scenario 4: Environment Variable (Legacy)
1. User has `OPENEI_API_KEY` env var set
2. No secrets.toml file
3. App shows "API Key configured"
4. ✅ Environment variable is used
5. Backward compatible!

## Migration Guide

### For Existing Users

If you were using the environment variable approach:

**Option A: Switch to secrets.toml (Recommended)**
1. Copy your API key from environment variable
2. Create `.streamlit/secrets.toml`
3. Add your key to the file
4. Remove environment variable (optional)

**Option B: Keep Using Environment Variable**
- No changes needed!
- Your environment variable still works
- Secrets.toml is optional

## Code Examples

### How It Works in Code

```python
# In src/config/settings.py
@classmethod
def get_openei_api_key(cls) -> str:
    # Priority 1: Check Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'OPENEI_API_KEY' in st.secrets:
            return st.secrets['OPENEI_API_KEY']
    except Exception:
        pass
    
    # Priority 2: Check environment variable
    return os.getenv('OPENEI_API_KEY', '')

# In src/components/sidebar.py
def _render_openei_import_section():
    configured_api_key = Settings.get_openei_api_key()
    
    if configured_api_key:
        # User has a configured key - offer override
        api_key_input = st.sidebar.text_input(
            "Override API Key (optional):", 
            type="password"
        )
        # Priority 3: User override (highest priority)
        api_key = api_key_input if api_key_input else configured_api_key
    else:
        # No configured key - require entry
        api_key_input = st.sidebar.text_input(
            "OpenEI API Key:", 
            type="password"
        )
        api_key = api_key_input
```

## Support Resources

- **Setup Guide**: `.streamlit/README.md`
- **Example File**: `.streamlit/secrets.toml.example`
- **Full Documentation**: `OPENEI_IMPORT_FEATURE.md`
- **Quick Start**: `OPENEI_IMPORT_QUICK_START.md`
- **Visual Guide**: `OPENEI_IMPORT_VISUAL_GUIDE.md`

## Backward Compatibility

✅ **Fully backward compatible!**

- Users with environment variables will see no change
- Environment variables still work as fallback
- Existing workflows are not disrupted
- New users get better default experience

## Future Enhancements

Potential future improvements:
- 🔐 Support for multiple API keys (switch between accounts)
- 📊 Track which key was used for each import
- ⚙️ GUI button to validate API key
- 🔄 Auto-refresh secrets without restarting app

## Conclusion

This update provides a more robust, user-friendly, and secure method for managing OpenEI API keys while maintaining full backward compatibility with the environment variable approach. Users get a persistent, cross-session solution that follows Streamlit best practices.

