# Streamlit Configuration Directory

This directory contains Streamlit-specific configuration files.

## secrets.toml (Required for OpenEI Import)

To use the OpenEI tariff import feature, create a `secrets.toml` file in this directory with your API key:

```toml
# .streamlit/secrets.toml
OPENEI_API_KEY = "your_api_key_here"
```

### Getting an API Key

1. Visit: https://openei.org/services/api/signup/
2. Fill out the registration form
3. Copy your API key
4. Add it to `secrets.toml`

### Example File

Copy `secrets.toml.example` to `secrets.toml` and replace `your_api_key_here` with your actual API key:

```bash
# Windows PowerShell
Copy-Item secrets.toml.example secrets.toml

# Mac/Linux
cp secrets.toml.example secrets.toml
```

Then edit `secrets.toml` with your API key.

## Security

- ✅ `secrets.toml` is already in `.gitignore` and will NOT be committed to version control
- ✅ Keep your API key private - never share it publicly
- ✅ If you accidentally commit it, regenerate your API key at OpenEI.org

## Other Configuration Files

You can also add other Streamlit configuration files to this directory:
- `config.toml` - Streamlit app configuration
- `credentials.toml` - Authentication credentials (if using auth features)

See the [Streamlit documentation](https://docs.streamlit.io/library/advanced-features/configuration) for more details.

