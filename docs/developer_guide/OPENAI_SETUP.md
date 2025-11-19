# OpenAI API Setup - Developer Guide

## 🎯 Overview

This guide explains how to configure OpenAI API access for the AI Schedule Assistant feature in the URDB Tariff Viewer application. This setup is required for the AI-powered schedule generation to work.

---

## 📋 Prerequisites

- OpenAI account with API access
- Streamlit Cloud account (for production deployment) OR
- Local development environment

---

## 🔑 Getting an OpenAI API Key

### Step 1: Create OpenAI Account

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)
6. ⚠️ **Important**: Save the key securely - you won't be able to see it again

### Step 2: Add Payment Method (Required)

OpenAI requires a payment method for API access:
1. Go to **Billing** section
2. Add a payment method (credit card)
3. Consider setting a usage limit to control costs
4. Recommended: Set a monthly budget alert

### Recommended Budget Settings

For the URDB Tariff Viewer with moderate usage:
- **Soft limit**: $5/month (warning email)
- **Hard limit**: $10/month (stops API access)

Typical monthly costs:
- Light usage (10 users, 5 schedules each): ~$0.25
- Moderate usage (50 users, 5 schedules each): ~$1.25
- Heavy usage (100 users, 10 schedules each): ~$5.00

---

## ⚙️ Configuration

### For Streamlit Cloud (Production)

#### Step 1: Access Streamlit Cloud Dashboard

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Log in with your account
3. Navigate to your deployed app
4. Click on **Settings** (⚙️ icon)

#### Step 2: Configure Secrets

1. Click on **Secrets** in the left sidebar
2. Add the following configuration:

```toml
[openai]
api_key = "sk-your-actual-api-key-here"
model = "gpt-4o-mini"  # Recommended for cost-efficiency
max_tokens = 2000
temperature = 0.1
```

**Configuration Options:**

| Parameter | Description | Recommended | Alternative |
|-----------|-------------|-------------|-------------|
| `api_key` | Your OpenAI API key | Required | N/A |
| `model` | OpenAI model to use | `gpt-4o-mini` | `gpt-4o` |
| `max_tokens` | Maximum response length | `2000` | `1000-4000` |
| `temperature` | Creativity vs consistency | `0.1` | `0.0-0.3` |

**Model Selection:**

| Model | Cost per 1K input tokens | Cost per 1K output tokens | Recommended for |
|-------|-------------------------|--------------------------|-----------------|
| `gpt-4o-mini` | $0.00015 | $0.0006 | **Production (default)** |
| `gpt-4o` | $0.0025 | $0.01 | High accuracy needs |
| `gpt-4` | $0.03 | $0.06 | Legacy/special cases |

💡 **Recommendation**: Start with `gpt-4o-mini`. It's 10-15x cheaper than GPT-4 and provides excellent results for schedule parsing.

#### Step 3: Save and Restart

1. Click **Save**
2. App will automatically restart
3. Verify configuration by checking the AI Assistant section

---

### For Local Development

You have three options for local configuration:

#### Option 1: Streamlit Secrets File (Recommended)

Create `.streamlit/secrets.toml` in your project root:

```toml
[openai]
api_key = "sk-your-actual-api-key-here"
model = "gpt-4o-mini"
max_tokens = 2000
temperature = 0.1
```

⚠️ **Important**: This file is already in `.gitignore`. Never commit API keys to git!

#### Option 2: Environment Variable

Set the `OPENAI_API_KEY` environment variable:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-your-actual-api-key-here"
streamlit run src/main.py
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
streamlit run src/main.py
```

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
streamlit run src/main.py
```

#### Option 3: `.env` File

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Then load it before running:

```python
# In your code or startup script
from dotenv import load_dotenv
load_dotenv()
```

⚠️ **Important**: Add `.env` to `.gitignore`!

---

## ✅ Verifying Configuration

### Check 1: Prerequisites Display

1. Open the app
2. Go to **Tariff Builder** → **Energy Schedule**
3. Expand **AI Schedule Assistant**
4. Check the Prerequisites section:
   - Should show: ✅ **OpenAI API Key**
   - If ⚠️ shows instead, configuration failed

### Check 2: Test Generation

1. Complete Energy Rate Structure (2 simple periods)
2. Paste a test description:
   ```
   Peak rates from 4 PM to 9 PM on weekdays.
   Off-Peak all other times.
   ```
3. Click **Generate Schedules**
4. Should receive results within 10-30 seconds

### Check 3: Logs (for troubleshooting)

For Streamlit Cloud:
- Go to App Settings → Logs
- Look for OpenAI-related errors

For Local:
- Check terminal output
- Look for import errors or API errors

---

## 🔒 Security Best Practices

### 1. Never Commit Secrets

**Files that should NEVER be committed:**
- `.streamlit/secrets.toml`
- `.env`
- Any file containing API keys

**Verify `.gitignore` includes:**
```gitignore
# Streamlit
.streamlit/secrets.toml

# Environment
.env
.env.local
```

### 2. Rotate Keys Regularly

- Change your API key every 3-6 months
- Immediately rotate if key is exposed
- Use different keys for dev/staging/production

### 3. Restrict Key Permissions

In OpenAI dashboard:
- Use separate keys for different environments
- Set usage limits per key
- Monitor key usage regularly

### 4. Environment-Specific Keys

**Recommended setup:**
- Development: Separate key with low limit ($1/month)
- Production: Production key with reasonable limit ($10/month)
- Testing: Optional separate key or reuse dev key

### 5. Monitor Usage

Set up monitoring:
1. OpenAI email alerts for usage thresholds
2. Weekly review of usage logs
3. Budget alerts in billing settings

---

## 💰 Cost Management

### Understanding Costs

**Per Request Costs (using gpt-4o-mini):**
- Input: ~600 tokens × $0.00015 per 1K = $0.00009
- Output: ~500 tokens × $0.0006 per 1K = $0.0003
- **Total: ~$0.0004 per generation**

**Monthly Projections:**

| Users | Schedules per User | Generations | Monthly Cost |
|-------|-------------------|-------------|--------------|
| 10 | 5 | 50 | $0.02 |
| 50 | 5 | 250 | $0.10 |
| 100 | 5 | 500 | $0.20 |
| 100 | 10 | 1,000 | $0.40 |
| 500 | 5 | 2,500 | $1.00 |

### Setting Budget Limits

#### In OpenAI Dashboard:

1. Go to **Organization Settings** → **Billing** → **Limits**
2. Set monthly budget limit
3. Enable email notifications

**Recommended Limits:**
- Small team (< 20 users): $5/month
- Medium org (20-100 users): $10/month
- Large org (100+ users): $25/month

#### In Application:

The app includes built-in rate limiting:
- Maximum 10 generations per user session
- User must refresh page to reset
- Prevents accidental over-usage

---

## 📊 Monitoring and Analytics

### Track Usage

#### OpenAI Dashboard:
1. Go to **Usage** section
2. View requests by:
   - Date/time
   - Model used
   - Tokens consumed
   - Cost

#### Application-Level Monitoring:

Add custom logging to `ai_schedule_service.py`:

```python
import logging

logger = logging.getLogger(__name__)

def parse_schedule_description(self, ...):
    logger.info(f"AI schedule generation requested")
    # ... existing code ...
    if result["success"]:
        logger.info(f"AI schedule generation successful. Confidence: {result['confidence']}")
    else:
        logger.error(f"AI schedule generation failed: {result.get('error')}")
```

### Key Metrics to Track

1. **Usage Metrics:**
   - Total requests per day/week/month
   - Requests per user
   - Success rate

2. **Quality Metrics:**
   - Average confidence score
   - Percentage of schedules applied
   - Retry rate

3. **Cost Metrics:**
   - Cost per request
   - Cost per user
   - Monthly total cost

---

## 🔧 Troubleshooting

### Issue: "AI service is not available"

**Possible Causes:**
1. API key not configured
2. API key is invalid
3. `openai` package not installed

**Solutions:**
```bash
# Check if package is installed
pip list | grep openai

# Install if missing
pip install openai>=1.0.0

# Verify secrets file exists
ls .streamlit/secrets.toml  # Local
# OR check Streamlit Cloud secrets dashboard

# Test API key validity
python -c "from openai import OpenAI; client = OpenAI(api_key='sk-...'); print(client.models.list())"
```

### Issue: "Rate limit exceeded"

**Possible Causes:**
1. Hit OpenAI rate limits
2. Hit app's 10-request limit

**Solutions:**
- Wait 1 minute and retry
- Check OpenAI dashboard for rate limit status
- Upgrade OpenAI plan if hitting API limits
- For app limit: refresh page

### Issue: "OpenAI API error"

**Possible Causes:**
1. Invalid API key
2. Insufficient credits
3. Network issues

**Solutions:**
```python
# Test API connectivity
import openai
from openai import OpenAI

client = OpenAI(api_key="sk-...")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("API working:", response.choices[0].message.content)
except Exception as e:
    print("API error:", str(e))
```

### Issue: High Costs

**Solutions:**
1. Switch from `gpt-4o` to `gpt-4o-mini`
2. Reduce `max_tokens` setting (try 1500)
3. Implement stricter rate limiting
4. Set lower budget limits in OpenAI dashboard

### Issue: Low Quality Results

**Solutions:**
1. Switch from `gpt-4o-mini` to `gpt-4o`
2. Adjust `temperature` (try 0.0 for more consistency)
3. Increase `max_tokens` (try 2500)
4. Review system prompt in `ai_schedule_service.py`

---

## 🔄 Updating Configuration

### Changing the Model

**To switch to GPT-4o (higher quality, higher cost):**

```toml
[openai]
api_key = "sk-..."
model = "gpt-4o"  # Changed from gpt-4o-mini
max_tokens = 2000
temperature = 0.1
```

Expected cost increase: ~10-15x

**To optimize for cost:**

```toml
[openai]
api_key = "sk-..."
model = "gpt-4o-mini"
max_tokens = 1500  # Reduced from 2000
temperature = 0.1
```

### Updating API Key

**Streamlit Cloud:**
1. Go to App Settings → Secrets
2. Update the `api_key` value
3. Save (app auto-restarts)

**Local:**
1. Edit `.streamlit/secrets.toml`
2. Update the `api_key` value
3. Restart the app

---

## 📚 Additional Resources

### OpenAI Documentation
- [API Reference](https://platform.openai.com/docs/api-reference)
- [Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [Pricing](https://openai.com/pricing)

### Streamlit Documentation
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Environment Variables](https://docs.streamlit.io/library/advanced-features/configuration)

### Security Resources
- [API Key Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [Git Security](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)

---

## 🆘 Support

For issues with:
- **OpenAI API**: Contact OpenAI support at platform.openai.com/support
- **Streamlit Cloud**: Contact Streamlit support
- **Application**: Check GitHub issues or contact your development team

---

## 📝 Configuration Checklist

Before going live:

- [ ] OpenAI account created
- [ ] Payment method added to OpenAI
- [ ] Budget limits set in OpenAI
- [ ] API key generated
- [ ] API key added to secrets (Streamlit Cloud or local)
- [ ] Model selected (`gpt-4o-mini` recommended)
- [ ] Configuration tested with sample generation
- [ ] `.gitignore` verified to exclude secrets
- [ ] Monitoring/logging configured
- [ ] Team members trained on usage limits
- [ ] Documentation shared with users

---

*Last Updated: November 2024*

