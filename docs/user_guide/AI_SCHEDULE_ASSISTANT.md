# AI Schedule Assistant - User Guide

## 🎯 Overview

The **AI Schedule Assistant** is an optional feature in the Tariff Builder that helps you quickly generate energy rate schedules from natural language descriptions. Instead of manually assigning periods to each hour, simply paste a description of your rate schedule and let AI create the schedules for you.

---

## ✨ Key Features

- **Natural Language Input**: Paste schedule descriptions directly from tariff documents
- **Smart Period Matching**: AI intelligently matches period names (e.g., "Peak" → "Summer On-Peak")
- **Confidence Scoring**: Shows how confident the AI is about the generated schedule
- **Multiple Output Options**: Apply directly, create templates, or edit manually
- **Preview Before Applying**: Review schedules before integrating into your tariff
- **Cost Transparency**: See estimated API cost before generating

---

## 🚀 Getting Started

### Prerequisites

Before using the AI Schedule Assistant, you must:

1. ✅ Complete the **Energy Rate Structure** section
   - Define all TOU periods (e.g., Peak, Off-Peak)
   - Set rates for each period
   - Label each period with a descriptive name

2. ✅ Have an OpenAI API key configured
   - See admin documentation for setup instructions
   - Contact your system administrator if unavailable

### Accessing the Feature

1. Navigate to the **🏗️ Tariff Builder** tab
2. Go to the **📅 Energy Schedule** section
3. Click to expand **🤖 AI Schedule Assistant (Optional)**

---

## 📝 How to Use

### Step 1: Check Prerequisites

The assistant will show your current status:
- ✅ Energy Rate Structure: X periods defined
- ✅ Period Labels Defined
- ✅ OpenAI API Key configured

If any are missing, complete those sections first.

### Step 2: Describe Your Schedule

**Example Descriptions:**

**Simple TOU Schedule:**
```
Peak rates apply from 4 PM to 9 PM on weekdays.
All other hours are Off-Peak.
Weekends are all Off-Peak.
```

**Seasonal Schedule:**
```
Summer (June-September):
- On-Peak: 4 PM - 9 PM weekdays
- Mid-Peak: 3 PM - 4 PM and 9 PM - 10 PM weekdays
- Off-Peak: All other hours
- Weekends: All Off-Peak

Winter (October-May):
- Mid-Peak: 4 PM - 9 PM weekdays
- Off-Peak: All other hours
- Weekends: All Off-Peak
```

**Complex Commercial Schedule:**
```
The rate schedule has three periods:
1. On-Peak: Weekdays from 12 PM to 6 PM (noon to 6pm)
2. Mid-Peak: Weekdays from 8 AM to 12 PM and 6 PM to 10 PM
3. Off-Peak: Weekdays from 10 PM to 8 AM, and all weekend hours

These rates apply year-round.
```

### Step 3: Tips for Best Results

**✅ DO:**
- Specify time ranges clearly (e.g., "4 PM to 9 PM", "16:00-21:00")
- Mention weekday vs. weekend differences
- Include seasonal information if applicable
- Use period names similar to your defined labels
- Provide context about which months have different schedules

**❌ DON'T:**
- Use ambiguous terms like "late afternoon" without specific times
- Forget to mention weekend schedules
- Exceed 2000 characters
- Use overly technical jargon

### Step 4: Generate Schedules

1. Paste your description (20-2000 characters)
2. Review the estimated cost (typically $0.0001-$0.0005)
3. Click **🤖 Generate Schedules**
4. Wait 10-30 seconds for AI processing

### Step 5: Review Results

The AI will show:

**Confidence Score:**
- **High (80%+)**: Very confident in the schedule
- **Medium (60-79%)**: Mostly confident, review carefully
- **Low (<60%)**: Uncertain, verify carefully or try again

**AI Explanation:**
- How it interpreted your description
- Which periods were detected
- Any assumptions made

**Period Matching Table:**
- Shows how detected periods map to your labels
- Verify these mappings are correct

**Schedule Preview:**
- Visual 24-hour schedules for weekday and weekend
- Shows which period applies at each hour

### Step 6: Apply Schedules

Choose one of four options:

**✅ Apply to Simple Mode** (Recommended for most users)
- Applies the schedule to all 12 months
- Best for year-round schedules
- Can still switch to Advanced mode later

**📋 Create as Templates**
- Creates templates in Advanced mode
- Good for further customization
- Allows different schedules per month

**✏️ Edit Manually**
- Pre-fills schedules but doesn't apply
- Lets you make adjustments first
- Use if confidence is medium/low

**🔄 Try Again**
- Clears results and lets you retry
- Use if results don't look right
- Try rephrasing your description

---

## 💡 Common Use Cases

### Use Case 1: Basic Residential TOU

**Your Periods:**
- Period 0: "Off-Peak" @ $0.10/kWh
- Period 1: "Peak" @ $0.25/kWh

**Description:**
```
Peak rates from 4 PM to 9 PM on weekdays.
Off-Peak all other times including weekends.
```

**Expected Result:**
- Weekday: Off-Peak 0-15, Peak 16-20, Off-Peak 21-23
- Weekend: All Off-Peak

---

### Use Case 2: Commercial with Three Periods

**Your Periods:**
- Period 0: "Off-Peak" @ $0.12/kWh
- Period 1: "Mid-Peak" @ $0.18/kWh
- Period 2: "On-Peak" @ $0.28/kWh

**Description:**
```
On-Peak: Weekdays 12 PM to 6 PM
Mid-Peak: Weekdays 8 AM to 12 PM and 6 PM to 10 PM
Off-Peak: Weekdays 10 PM to 8 AM, all weekends
```

**Expected Result:**
- Weekday: Off-Peak 0-7, Mid-Peak 8-11, On-Peak 12-17, Mid-Peak 18-21, Off-Peak 22-23
- Weekend: All Off-Peak

---

### Use Case 3: Seasonal Schedule

**Your Periods:**
- Period 0: "Summer Off-Peak"
- Period 1: "Summer Mid-Peak"
- Period 2: "Summer On-Peak"
- Period 3: "Winter Off-Peak"
- Period 4: "Winter On-Peak"

**Description:**
```
Summer (June-September):
- On-Peak: 4 PM - 9 PM weekdays
- Mid-Peak: 3 PM - 4 PM and 9 PM - 10 PM weekdays
- Off-Peak: All other times

Winter (October-May):
- On-Peak: 4 PM - 9 PM weekdays
- Off-Peak: All other times

Weekends are always Off-Peak regardless of season.
```

**Note:** For seasonal schedules, you'll need to use the **Create as Templates** option and then assign templates to specific months in Advanced mode.

---

## ⚠️ Troubleshooting

### "AI service is not available"
- **Cause**: OpenAI API key not configured
- **Solution**: Contact your system administrator

### "Description too short"
- **Cause**: Less than 20 characters provided
- **Solution**: Add more details about when rates apply

### Low Confidence Score
- **Causes**: 
  - Ambiguous time descriptions
  - Missing information about weekends
  - Conflicting information
- **Solutions**:
  - Be more specific about time ranges
  - Explicitly mention weekend schedules
  - Review and clarify any contradictions
  - Try the "Show Example" button for reference

### Wrong Period Mapping
- **Cause**: Period names in description don't match your labels
- **Solution**: 
  - Review the mapping table
  - Use the "Edit Manually" option
  - Adjust your description to use closer names

### "Rate limit exceeded"
- **Cause**: Made 10+ generation requests in one session
- **Solution**: Refresh the page to reset counter

---

## 📊 Understanding Costs

The AI Schedule Assistant uses OpenAI's API, which incurs small costs per use:

**Typical Costs per Generation:**
- Using GPT-4o-mini: $0.0001 - $0.0005
- Using GPT-4o: $0.001 - $0.005

**Example Monthly Usage:**
- 10 tariffs created × 2 attempts each = 20 generations
- Cost with GPT-4o-mini: ~$0.01
- Cost with GPT-4o: ~$0.10

The app shows estimated cost before each generation.

---

## 🎓 Best Practices

### 1. Start with Energy Rates
Always complete your Energy Rate Structure before using AI assistance. The AI needs to know:
- How many periods you have
- What you call each period

### 2. Be Specific with Times
Use concrete times instead of vague descriptions:
- ✅ "4 PM to 9 PM" or "16:00-21:00"
- ❌ "late afternoon to evening"

### 3. Mention Weekend Schedules
Always explicitly state what happens on weekends:
- ✅ "Weekends are all Off-Peak"
- ❌ (No mention of weekends)

### 4. Review Before Applying
Always check:
- Confidence score is acceptable
- Period mapping looks correct
- Preview schedules match your intent

### 5. Use Appropriate Output Option
- **Simple schedule that won't change?** → Apply to Simple Mode
- **Need month-by-month customization?** → Create as Templates
- **Want to tweak the results?** → Edit Manually
- **Results don't look right?** → Try Again

### 6. Seasonal Schedules
For schedules that vary by season:
1. Use "Create as Templates" option
2. Switch to Advanced mode
3. Create additional templates for different seasons
4. Assign templates to appropriate months

---

## 🔄 Workflow Examples

### Quick Workflow (Simple Schedule)
1. Complete Energy Rate Structure → 2 minutes
2. Open AI Assistant → 5 seconds
3. Paste description → 10 seconds
4. Generate schedules → 20 seconds
5. Review results → 30 seconds
6. Apply to Simple Mode → 5 seconds
**Total Time: ~3 minutes**

### Detailed Workflow (Seasonal Schedule)
1. Complete Energy Rate Structure → 5 minutes
2. Open AI Assistant → 5 seconds
3. Paste description (with seasons) → 30 seconds
4. Generate schedules → 20 seconds
5. Review results → 1 minute
6. Create as Templates → 5 seconds
7. Switch to Advanced mode → 10 seconds
8. Adjust month assignments → 2 minutes
**Total Time: ~9 minutes**

vs. Manual Entry: 20-30 minutes

---

## ❓ FAQ

**Q: Do I need to use the AI Assistant?**
A: No, it's completely optional. You can still create schedules manually.

**Q: Can I edit AI-generated schedules?**
A: Yes! Use the "Edit Manually" option, or apply schedules and edit them afterwards.

**Q: What languages are supported?**
A: Currently English only. The AI may understand other languages but results may vary.

**Q: Can I save my description for later?**
A: The description is not saved automatically. Copy it elsewhere if you want to reuse it.

**Q: What if the AI gets it wrong?**
A: You can try again with a clearer description, or use manual entry. Always review results carefully.

**Q: Is my data sent to OpenAI?**
A: Yes, your description and period labels are sent to OpenAI's API to generate schedules. Don't include sensitive or proprietary information beyond standard tariff structures.

**Q: Can I use this for demand schedules?**
A: Not yet. The AI Assistant currently only works for energy schedules. Demand schedule support may be added in the future.

---

## 📞 Getting Help

If you encounter issues:

1. **Try the Example**: Click "Show Example Description" to see a working format
2. **Check Prerequisites**: Ensure Energy Rate Structure is complete
3. **Simplify**: Try a simpler, more straightforward description
4. **Manual Entry**: You can always fall back to manual schedule creation
5. **Contact Support**: Reach out to your system administrator

---

## 🔮 Future Enhancements

Planned features for future releases:
- Support for demand charge schedules
- Multi-season automatic detection
- PDF/document upload and parsing
- Holiday schedule handling
- Schedule validation and suggestions
- Multiple language support

---

*Last Updated: November 2024*

