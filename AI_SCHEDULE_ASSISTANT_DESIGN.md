# AI Schedule Assistant - Implementation Design

## 📋 Overview

This document outlines the implementation plan for an optional AI-powered schedule assistant in the Energy Schedule section of the Tariff Builder. The assistant will allow users to paste natural language descriptions of energy schedules and automatically generate weekday/weekend schedule templates using OpenAI's API.

---

## 🎯 Design Philosophy

### User Flow Approach: **Flexible with Smart Matching**

**Recommended:** Allow the OpenAI assistant to intelligently match period labels rather than requiring exact matches. This provides the best user experience while maintaining accuracy.

#### Why This Approach?
1. **User-Friendly**: Users can paste tariff documents without reformatting
2. **Robust**: Handles variations in terminology (e.g., "On-Peak" vs "Peak" vs "On Peak")
3. **Smart Validation**: AI can ask for clarification when matches are ambiguous
4. **Fallback**: Shows user the mapping for review/correction before applying

---

## 🔧 Implementation Plan

### **Phase 1: UI Components**

#### Location
Add AI Assistant as an **optional** feature in `_render_energy_schedule_section()` in `src/components/tariff_builder.py`

#### UI Layout
```
📅 Energy TOU Schedule
├── [New] 🤖 AI Schedule Assistant (Optional) [Expandable]
│   ├── Prerequisites Check
│   │   ✅ Energy Rate Structure completed (X periods)
│   │   ✅ Period labels defined
│   │   ⚠️ OpenAI API key configured
│   │
│   ├── Input Section
│   │   ├── Text Area: "Paste schedule description" (500-2000 char limit)
│   │   ├── Example: "Show me an example"
│   │   └── [Generate Schedules] Button
│   │
│   ├── AI Response Preview
│   │   ├── Detected Periods (with confidence scores)
│   │   ├── Period Mapping Table (AI matched → Your labels)
│   │   ├── Weekday Schedule Preview (24-hour grid)
│   │   └── Weekend Schedule Preview (24-hour grid)
│   │
│   └── Action Buttons
│       ├── [✅ Apply to Templates] - Creates templates with AI schedules
│       ├── [✏️ Edit Before Applying] - Go to manual editor with pre-filled
│       └── [🔄 Try Again] - Clear and retry
│
├── Schedule Configuration (Existing)
│   ├── Simple Mode
│   └── Advanced Mode (Templates)
```

---

## 🔐 Security & API Key Management

### Streamlit Cloud Secrets Management

#### Setup Instructions for Users:
1. Go to Streamlit Cloud Dashboard
2. Navigate to App Settings → Secrets
3. Add the following to secrets:
   ```toml
   [openai]
   api_key = "sk-..."
   model = "gpt-4o-mini"  # or gpt-4o for better accuracy
   max_tokens = 2000
   ```

#### Code Implementation:
```python
# src/config/settings.py
import streamlit as st

class Settings:
    # ... existing code ...
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key from Streamlit secrets."""
        try:
            return st.secrets.get("openai", {}).get("api_key")
        except Exception:
            return None
    
    @classmethod
    def get_openai_config(cls) -> Dict[str, Any]:
        """Get OpenAI configuration from secrets."""
        try:
            return {
                "api_key": st.secrets["openai"].get("api_key"),
                "model": st.secrets["openai"].get("model", "gpt-4o-mini"),
                "max_tokens": st.secrets["openai"].get("max_tokens", 2000)
            }
        except Exception:
            return {}
    
    @classmethod
    def has_openai_configured(cls) -> bool:
        """Check if OpenAI is properly configured."""
        return cls.get_openai_api_key() is not None
```

### Alternative: Development Mode
For development/testing, allow optional `.env` file (already in `.gitignore`):
```python
# Load from environment variables as fallback
api_key = st.secrets.get("openai", {}).get("api_key") or os.getenv("OPENAI_API_KEY")
```

---

## 🧠 OpenAI Integration

### Service Layer
Create new service: `src/services/ai_schedule_service.py`

```python
"""
AI-powered schedule generation service using OpenAI API.
"""

from typing import Dict, List, Any, Tuple, Optional
import json
import openai
from src.config.settings import Settings


class AIScheduleService:
    """Service for generating TOU schedules using AI."""
    
    def __init__(self):
        """Initialize the AI service."""
        config = Settings.get_openai_config()
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o-mini")
        self.max_tokens = config.get("max_tokens", 2000)
        
        if self.api_key:
            openai.api_key = self.api_key
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.api_key is not None
    
    def parse_schedule_description(
        self,
        description: str,
        existing_period_labels: List[str],
        num_periods: int
    ) -> Dict[str, Any]:
        """
        Parse natural language schedule description and generate schedules.
        
        Args:
            description: User's natural language description
            existing_period_labels: List of period labels defined in Energy Rates
            num_periods: Number of TOU periods
        
        Returns:
            Dict containing:
                - success: bool
                - weekday_schedule: List[int] (24 hours)
                - weekend_schedule: List[int] (24 hours)
                - period_mapping: Dict[str, str] (detected → existing label)
                - confidence: float (0-1)
                - explanation: str
                - error: str (if failed)
        """
        
        # Input validation
        if not description or len(description.strip()) < 20:
            return {
                "success": False,
                "error": "Description too short. Please provide more details."
            }
        
        if len(description) > 2000:
            return {
                "success": False,
                "error": "Description too long. Please keep it under 2000 characters."
            }
        
        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            description, existing_period_labels, num_periods
        )
        
        try:
            # Call OpenAI API
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            if not self._validate_response(result, num_periods):
                return {
                    "success": False,
                    "error": "AI response validation failed. Please try rephrasing."
                }
            
            return {
                "success": True,
                **result
            }
            
        except openai.APIError as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse AI response. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for OpenAI."""
        return """You are an expert at analyzing utility tariff rate schedules. 
Your task is to parse natural language descriptions of Time-of-Use (TOU) energy 
schedules and convert them into structured hourly schedules.

You will be given:
1. A natural language description of when different rate periods apply
2. A list of existing period labels (e.g., "Summer On-Peak", "Winter Off-Peak")
3. The number of TOU periods

Your job is to:
1. Parse the description to understand when each rate period applies
2. Match detected periods to the existing period labels (fuzzy matching is OK)
3. Generate two 24-hour schedules (one for weekday, one for weekend)
4. Each hour should be assigned a period number (0 to num_periods-1)
5. Provide a confidence score and explanation

Return your response as JSON with this structure:
{
  "weekday_schedule": [0,0,0,0,0,0,1,1,2,2,2,2,1,1,1,1,2,2,2,1,1,0,0,0],
  "weekend_schedule": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  "period_mapping": {
    "detected_peak": "Summer On-Peak",
    "detected_offpeak": "Summer Off-Peak"
  },
  "confidence": 0.95,
  "explanation": "Detected 3 periods: Off-Peak (hours 0-5, 22-23), Mid-Peak (hours 6-8, 18-21), On-Peak (hours 9-17). Weekend appears to be all Off-Peak.",
  "warnings": ["Month information not specified - assuming year-round schedule"]
}

Important rules:
- Hours are 0-23 (0 = midnight, 12 = noon, 23 = 11 PM)
- Use case-insensitive fuzzy matching for period names
- If weekend schedule is not mentioned, assume all off-peak or same as weekday
- If uncertain, provide lower confidence score
- Always return valid JSON"""

    def _build_user_prompt(
        self,
        description: str,
        existing_labels: List[str],
        num_periods: int
    ) -> str:
        """Build the user prompt with context."""
        labels_str = "\n".join([f"  Period {i}: {label}" 
                               for i, label in enumerate(existing_labels)])
        
        return f"""Please analyze this TOU schedule description and generate hourly schedules:

DESCRIPTION:
{description}

EXISTING PERIOD LABELS:
{labels_str}

NUMBER OF PERIODS: {num_periods}

Please generate the weekday and weekend schedules, matching the periods in the 
description to the existing period labels as closely as possible. Return your 
response as JSON following the specified structure."""

    def _validate_response(
        self,
        response: Dict[str, Any],
        num_periods: int
    ) -> bool:
        """Validate the AI response structure and values."""
        # Check required fields
        required_fields = [
            "weekday_schedule", "weekend_schedule", 
            "period_mapping", "confidence", "explanation"
        ]
        
        if not all(field in response for field in required_fields):
            return False
        
        # Validate schedules
        weekday = response["weekday_schedule"]
        weekend = response["weekend_schedule"]
        
        if not (isinstance(weekday, list) and len(weekday) == 24):
            return False
        
        if not (isinstance(weekend, list) and len(weekend) == 24):
            return False
        
        # Check all values are valid period indices
        all_values = weekday + weekend
        if not all(isinstance(v, int) and 0 <= v < num_periods for v in all_values):
            return False
        
        # Validate confidence
        confidence = response.get("confidence", 0)
        if not (isinstance(confidence, (int, float)) and 0 <= confidence <= 1):
            return False
        
        return True
    
    def estimate_cost(self, description: str) -> float:
        """
        Estimate the cost of processing a description.
        
        Args:
            description: The schedule description
        
        Returns:
            Estimated cost in USD
        """
        # Rough token estimation (1 token ≈ 4 characters)
        input_tokens = len(description) / 4 + 500  # +500 for system prompt
        output_tokens = 500  # Max expected output
        
        if "gpt-4" in self.model:
            # GPT-4 pricing (approximate)
            input_cost = input_tokens * 0.00003 / 1000
            output_cost = output_tokens * 0.00006 / 1000
        else:
            # GPT-3.5/4o-mini pricing (approximate)
            input_cost = input_tokens * 0.000001 / 1000
            output_cost = output_tokens * 0.000002 / 1000
        
        return input_cost + output_cost
```

---

## 📊 UI Component Implementation

### Add to `src/components/tariff_builder.py`

```python
def _render_ai_schedule_assistant(data: Dict, num_periods: int) -> None:
    """
    Render the optional AI schedule assistant.
    
    Args:
        data: Tariff builder data
        num_periods: Number of TOU periods
    """
    from src.services.ai_schedule_service import AIScheduleService
    
    st.markdown("---")
    st.markdown("### 🤖 AI Schedule Assistant (Optional)")
    
    with st.expander("✨ Generate Schedules from Text Description", expanded=False):
        # Initialize AI service
        ai_service = AIScheduleService()
        
        # Check prerequisites
        st.markdown("#### Prerequisites")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            has_periods = num_periods > 0
            st.markdown(f"{'✅' if has_periods else '❌'} Energy Rate Structure: {num_periods} periods")
        
        with col2:
            has_labels = len(data.get('energytoulabels', [])) == num_periods
            st.markdown(f"{'✅' if has_labels else '❌'} Period Labels Defined")
        
        with col3:
            ai_available = ai_service.is_available()
            st.markdown(f"{'✅' if ai_available else '⚠️'} OpenAI API Key")
        
        if not ai_available:
            st.warning("""
            ⚠️ **OpenAI API Key Not Configured**
            
            To use the AI Schedule Assistant, configure your OpenAI API key:
            1. Go to Streamlit Cloud Dashboard
            2. Navigate to **App Settings → Secrets**
            3. Add: 
            ```toml
            [openai]
            api_key = "sk-your-key-here"
            model = "gpt-4o-mini"
            ```
            
            For local development, you can also set the `OPENAI_API_KEY` environment variable.
            """)
            return
        
        if not (has_periods and has_labels):
            st.warning("⚠️ Please complete the Energy Rate Structure section first before using AI assistance.")
            return
        
        # Show example
        if st.button("📝 Show Example Description"):
            st.info("""
            **Example Schedule Description:**
            
            "Summer rates apply from June through September. During summer months, 
            On-Peak rates are from 4 PM to 9 PM on weekdays. Mid-Peak rates are from 
            3 PM to 4 PM and 9 PM to 10 PM on weekdays. All other hours are Off-Peak. 
            Weekends are all Off-Peak during summer.
            
            Winter rates apply from October through May. During winter months, 
            Mid-Peak rates are from 4 PM to 9 PM on weekdays. All other hours are 
            Off-Peak. Weekends are all Off-Peak."
            """)
        
        # Input section
        st.markdown("---")
        st.markdown("#### Describe Your Schedule")
        
        description = st.text_area(
            "Paste your rate schedule description here:",
            height=200,
            max_chars=2000,
            help="Describe when different rate periods apply throughout the day, week, and year",
            placeholder="Example: On-Peak rates are from 4 PM to 9 PM on weekdays during summer months (June-September)..."
        )
        
        char_count = len(description)
        st.caption(f"Characters: {char_count}/2000")
        
        if char_count > 0:
            # Show estimated cost
            est_cost = ai_service.estimate_cost(description)
            st.caption(f"Estimated cost: ${est_cost:.4f} per generation")
        
        # Generate button
        col1, col2 = st.columns([1, 3])
        
        with col1:
            generate_button = st.button(
                "🤖 Generate Schedules",
                type="primary",
                disabled=char_count < 20,
                use_container_width=True
            )
        
        with col2:
            if char_count < 20:
                st.caption("⚠️ Please provide a more detailed description (at least 20 characters)")
        
        # Process AI request
        if generate_button:
            with st.spinner("🤖 AI is analyzing your schedule description..."):
                result = ai_service.parse_schedule_description(
                    description=description,
                    existing_period_labels=data['energytoulabels'],
                    num_periods=num_periods
                )
            
            if result["success"]:
                # Store result in session state
                st.session_state.ai_schedule_result = result
                st.success("✅ Schedules generated successfully!")
            else:
                st.error(f"❌ {result.get('error', 'Unknown error occurred')}")
        
        # Display results if available
        if st.session_state.get('ai_schedule_result'):
            _render_ai_schedule_results(data, st.session_state.ai_schedule_result, num_periods)


def _render_ai_schedule_results(data: Dict, result: Dict, num_periods: int) -> None:
    """Render the AI-generated schedule results with preview and actions."""
    
    st.markdown("---")
    st.markdown("#### 📊 AI-Generated Schedules")
    
    # Confidence and explanation
    confidence = result.get("confidence", 0)
    explanation = result.get("explanation", "")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Visual confidence indicator
        if confidence >= 0.8:
            st.metric("Confidence", f"{confidence:.0%}", delta="High")
        elif confidence >= 0.6:
            st.metric("Confidence", f"{confidence:.0%}", delta="Medium")
        else:
            st.metric("Confidence", f"{confidence:.0%}", delta="Low")
    
    with col2:
        st.info(f"**AI Explanation:** {explanation}")
    
    # Show warnings if any
    warnings = result.get("warnings", [])
    if warnings:
        for warning in warnings:
            st.warning(f"⚠️ {warning}")
    
    # Period mapping table
    st.markdown("##### 🔗 Period Matching")
    period_mapping = result.get("period_mapping", {})
    
    if period_mapping:
        mapping_df = pd.DataFrame([
            {"Detected in Description": detected, "Matched to Period": matched}
            for detected, matched in period_mapping.items()
        ])
        st.dataframe(mapping_df, use_container_width=True, hide_index=True)
    
    # Schedule previews
    st.markdown("##### 📅 Schedule Preview")
    
    tab1, tab2 = st.tabs(["Weekday Schedule", "Weekend Schedule"])
    
    weekday_schedule = result.get("weekday_schedule", [])
    weekend_schedule = result.get("weekend_schedule", [])
    
    with tab1:
        _show_schedule_preview(weekday_schedule, data['energytoulabels'], "Weekday")
    
    with tab2:
        _show_schedule_preview(weekend_schedule, data['energytoulabels'], "Weekend")
    
    # Action buttons
    st.markdown("---")
    st.markdown("##### ⚡ Next Steps")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Apply to Simple Mode", type="primary", use_container_width=True):
            # Apply directly to simple schedule
            data['energyweekdayschedule'] = [weekday_schedule for _ in range(12)]
            data['energyweekendschedule'] = [weekend_schedule for _ in range(12)]
            st.success("✅ Schedules applied! Scroll down to see the schedule preview.")
            st.session_state.ai_schedule_result = None  # Clear result
            st.rerun()
    
    with col2:
        if st.button("📋 Create as Templates", use_container_width=True):
            # Create templates in advanced mode
            _create_templates_from_ai_result(data, result)
            st.success("✅ Templates created! Switch to Advanced mode to customize.")
            st.session_state.ai_schedule_result = None
            st.rerun()
    
    with col3:
        if st.button("✏️ Edit Manually", use_container_width=True):
            # Pre-fill but let user edit
            data['energyweekdayschedule'] = [weekday_schedule for _ in range(12)]
            data['energyweekendschedule'] = [weekend_schedule for _ in range(12)]
            st.session_state.ai_schedule_result = None
            st.info("Schedules loaded. You can now edit them manually below.")
            st.rerun()
    
    with col4:
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.ai_schedule_result = None
            st.rerun()


def _show_schedule_preview(schedule: List[int], labels: List[str], title: str) -> None:
    """Show a visual preview of a 24-hour schedule."""
    
    # Create a visual representation
    schedule_df = pd.DataFrame({
        'Hour': [f"{h:02d}:00" for h in range(24)],
        'Period': [labels[schedule[h]] if h < len(schedule) else "N/A" for h in range(24)],
        'Period #': schedule
    })
    
    st.dataframe(
        schedule_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )


def _create_templates_from_ai_result(data: Dict, result: Dict) -> None:
    """Create templates in advanced mode from AI results."""
    
    # Initialize templates if needed
    if 'energy_schedule_templates' not in st.session_state:
        st.session_state.energy_schedule_templates = {
            'weekday': {},
            'weekend': {}
        }
    
    # Create "AI Generated" templates
    weekday_schedule = result.get("weekday_schedule", [])
    weekend_schedule = result.get("weekend_schedule", [])
    
    st.session_state.energy_schedule_templates['weekday']['AI Generated'] = {
        'name': 'AI Generated',
        'schedule': weekday_schedule,
        'assigned_months': list(range(12))  # Assign to all months
    }
    
    st.session_state.energy_schedule_templates['weekend']['AI Generated'] = {
        'name': 'AI Generated',
        'schedule': weekend_schedule,
        'assigned_months': list(range(12))  # Assign to all months
    }
    
    # Apply templates to data
    data['energyweekdayschedule'] = [weekday_schedule for _ in range(12)]
    data['energyweekendschedule'] = [weekend_schedule for _ in range(12)]
```

### Integrate into existing function

Modify `_render_energy_schedule_section()`:

```python
def _render_energy_schedule_section() -> None:
    """Render the energy schedule section of the tariff builder."""
    st.markdown("### 📅 Energy TOU Schedule")
    st.markdown("""
    Define when each TOU period applies throughout the year. You can set different 
    schedules for weekdays and weekends.
    """)
    
    data = st.session_state.tariff_builder_data['items'][0]
    num_periods = len(data['energyratestructure'])
    
    # NEW: Add AI Schedule Assistant
    _render_ai_schedule_assistant(data, num_periods)
    
    # Existing schedule editing mode
    st.markdown("---")
    st.markdown("#### Schedule Configuration")
    
    schedule_mode = st.radio(
        "How would you like to set the schedule?",
        options=["Simple (same for all months)", "Advanced (different by month)"],
        help="Simple mode applies the same daily pattern to all months"
    )
    
    # ... rest of existing code ...
```

---

## 🛡️ Controls & Safeguards

### Input Validation
- **Character Limit**: 500-2000 characters
  - Minimum: Ensures sufficient detail for AI
  - Maximum: Controls API costs and prevents abuse
- **Rate Limiting**: Track usage in session state
  - Max 10 requests per session
  - Display counter to user
- **Sanitization**: Strip HTML, validate no code injection

### API Usage Monitoring
```python
# Track usage in session state
if 'ai_usage_count' not in st.session_state:
    st.session_state.ai_usage_count = 0

if st.session_state.ai_usage_count >= 10:
    st.warning("⚠️ You've reached the limit of 10 AI generations per session. Please refresh the page to continue.")
    return

# Increment on each use
st.session_state.ai_usage_count += 1
st.caption(f"AI generations used: {st.session_state.ai_usage_count}/10")
```

### Cost Protection
- Show estimated cost before generation
- Use `gpt-4o-mini` by default (much cheaper than GPT-4)
- Set `max_tokens` limit in secrets
- Temperature = 0.1 for consistency and cost efficiency

### Error Handling
- Graceful API failures → allow manual entry
- Clear error messages
- Timeout after 30 seconds
- Retry mechanism with exponential backoff

---

## 📝 User Workflow Example

### Scenario: User creating SCE TOU-EV-9 tariff

1. **Complete Energy Rates Section**
   - Period 0: "Summer Off-Peak" @ $0.18/kWh
   - Period 1: "Summer Mid-Peak" @ $0.28/kWh
   - Period 2: "Summer On-Peak" @ $0.42/kWh
   - Period 3: "Winter Off-Peak" @ $0.16/kWh
   - Period 4: "Winter Mid-Peak" @ $0.22/kWh
   - Period 5: "Winter On-Peak" @ $0.35/kWh

2. **Navigate to Energy Schedule Section**

3. **Open AI Assistant (Optional)**

4. **Paste Description**
   ```
   Summer rates (June-September): On-Peak 4PM-9PM weekdays, 
   Mid-Peak 3PM-4PM and 9PM-10PM weekdays, Off-Peak all other times.
   Weekends all Off-Peak.
   
   Winter rates (October-May): Mid-Peak 4PM-9PM weekdays, 
   Off-Peak all other times. Weekends all Off-Peak.
   ```

5. **Click "Generate Schedules"**
   - AI processes → Shows confidence 0.92
   - Displays period mapping
   - Shows preview of 24-hour schedules

6. **Review & Apply**
   - User sees mapping is correct
   - Clicks "Create as Templates"
   - System creates 2 weekday templates (Summer/Winter) and 2 weekend templates

7. **Fine-tune if needed**
   - Switch to Advanced mode
   - Adjust template month assignments
   - Edit individual hours if needed

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_services/test_ai_schedule_service.py

def test_ai_service_initialization():
    """Test service initializes correctly with/without API key."""
    pass

def test_description_parsing():
    """Test parsing of various schedule descriptions."""
    pass

def test_period_matching():
    """Test fuzzy matching of period names."""
    pass

def test_validation():
    """Test response validation catches invalid data."""
    pass

def test_error_handling():
    """Test graceful handling of API errors."""
    pass
```

### Integration Tests
- Test full workflow from description to applied schedules
- Test with real OpenAI API (mark as integration test)
- Test fallback behavior when API unavailable

### Manual QA Checklist
- [ ] Works without API key (shows warning)
- [ ] Works with valid API key
- [ ] Handles various description formats
- [ ] Properly maps period names
- [ ] Generates valid 24-hour schedules
- [ ] Applies to simple mode correctly
- [ ] Creates templates correctly
- [ ] Shows appropriate errors for invalid input
- [ ] Respects rate limits
- [ ] Displays cost estimates

---

## 💰 Cost Analysis

### Estimated Costs (using GPT-4o-mini)
- **Input**: ~600 tokens (system prompt + user description)
- **Output**: ~500 tokens
- **Cost per request**: ~$0.0002 - $0.0005
- **Monthly (100 users, 5 requests each)**: ~$0.10 - $0.25

### Using GPT-4 (for higher accuracy)
- **Cost per request**: ~$0.03 - $0.05
- **Monthly (same usage)**: ~$15 - $25

**Recommendation**: Start with `gpt-4o-mini` and allow power users to switch to `gpt-4` via secrets config.

---

## 🚀 Deployment Steps

### 1. Update Requirements
```bash
# requirements.txt
openai>=1.0.0
```

### 2. Add Service File
Create `src/services/ai_schedule_service.py` (see implementation above)

### 3. Update Settings
Add OpenAI methods to `src/config/settings.py`

### 4. Update Tariff Builder
Integrate AI assistant into `src/components/tariff_builder.py`

### 5. Configure Secrets (Streamlit Cloud)
```toml
[openai]
api_key = "sk-..."
model = "gpt-4o-mini"
max_tokens = 2000
```

### 6. Update Documentation
- Add user guide for AI assistant
- Add admin guide for API key setup
- Update README with AI features

### 7. Test & Deploy
- Test locally with `.streamlit/secrets.toml`
- Test on Streamlit Cloud
- Monitor API usage and costs

---

## 📚 User Documentation

### For End Users
Create `docs/user_guide/AI_SCHEDULE_ASSISTANT.md`:
- How to use the feature
- Example descriptions
- Tips for best results
- Troubleshooting

### For Admins
Create `docs/developer_guide/OPENAI_SETUP.md`:
- How to get OpenAI API key
- How to configure in Streamlit Cloud
- Cost management
- Usage monitoring

---

## 🔄 Future Enhancements

### Phase 2 (Future)
1. **Multi-season detection**: Automatically detect and create seasonal templates
2. **Holiday handling**: Detect holiday schedules mentioned in descriptions
3. **Confidence boosting**: Ask clarifying questions for low-confidence results
4. **Batch processing**: Process multiple schedule types at once
5. **Learning mode**: Save successful mappings to improve future suggestions
6. **Demand schedule AI**: Extend to demand charge schedules

### Phase 3 (Advanced)
1. **Document upload**: Parse PDF/Word tariff documents
2. **Table extraction**: Extract schedule tables from documents
3. **Multi-language support**: Support non-English tariff descriptions
4. **Voice input**: Allow voice recording of schedule description

---

## ✅ Decision Summary

### Recommended Approach

| Aspect | Recommendation | Rationale |
|--------|---------------|-----------|
| **Period Matching** | Fuzzy matching with review | Best UX, handles variations |
| **Prerequisites** | Energy rates completed, but flexible labels | Balance usability & accuracy |
| **API Key Storage** | Streamlit Secrets (Cloud) + ENV fallback | Secure, standard practice |
| **Model** | GPT-4o-mini (default) | Cost-effective, sufficient accuracy |
| **Character Limit** | 500-2000 characters | Prevents abuse, ensures detail |
| **Rate Limiting** | 10 requests/session | Reasonable limit, low cost |
| **Error Handling** | Graceful degradation | Always allow manual entry |
| **User Flow** | Optional feature in expandable section | Doesn't overwhelm new users |

---

## 🎯 Success Metrics

### Key Performance Indicators
- **Adoption Rate**: % of users who try AI assistant
- **Success Rate**: % of AI generations that get applied
- **Accuracy**: User feedback on generated schedules
- **Cost**: Average cost per successful tariff creation
- **Time Savings**: Time to complete Energy Schedule section

### Target Goals (3 months post-launch)
- [ ] 30%+ of users try AI assistant
- [ ] 80%+ success rate for generations
- [ ] < $1 total monthly API costs (small user base)
- [ ] 50% reduction in time to complete Energy Schedule
- [ ] Positive user feedback on feature

---

## 📞 Support & Feedback

### For Issues
- Check OpenAI API key configuration
- Verify prerequisites are met
- Try rephrasing description
- Use manual entry as fallback

### Feature Feedback
Collect feedback via:
- In-app feedback form
- GitHub issues
- User surveys

---

## 🏁 Implementation Checklist

- [ ] Add `openai` to requirements.txt
- [ ] Create `src/services/ai_schedule_service.py`
- [ ] Update `src/config/settings.py` with OpenAI methods
- [ ] Add AI assistant to `src/components/tariff_builder.py`
- [ ] Create user documentation
- [ ] Create admin documentation
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Configure secrets in Streamlit Cloud
- [ ] Test locally
- [ ] Test on Streamlit Cloud
- [ ] Monitor initial usage and costs
- [ ] Gather user feedback
- [ ] Iterate based on feedback

---

*End of Design Document*

