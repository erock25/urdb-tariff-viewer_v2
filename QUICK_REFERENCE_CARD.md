# Template-Based TOU Schedule - Quick Reference Card

## 🚀 Quick Start (30 seconds)

```
1. Tariff Builder → Energy Schedule → Advanced mode
2. Add templates (e.g., "Summer", "Winter", "Shoulder")
3. Edit each template's 24 hours
4. Assign months to templates
5. Done! ✓
```

---

## 📋 3-Step Workflow

### Step 1: Manage Templates
```
Current Templates:        Add New Template:
• Summer (0 months)      [Summer Peak    ]
• Winter (0 months)      [➕ Add Template]

Delete Template:
[Select template ▼] [🗑️ Delete]
```

**Actions:**
- ➕ Add: Name your template → Click "Add"
- 🗑️ Delete: Select → Click "Delete"
- 👀 View: See template list with month counts

---

### Step 2: Edit Templates
```
Select template: [Summer Peak ▼]

Editing: Summer Peak
Set the TOU period for each hour:

0:00  1:00  2:00  ... 23:00
[P0▼] [P0▼] [P0▼] ... [P0▼]

[✅ Save Template]

Template Preview:
Hour    Period
0:00    0
1:00    0
...
```

**Actions:**
- 🎯 Select template from dropdown
- ⏰ Set each hour to desired period
- 💾 Click "Save Template"
- 👁️ Review preview table

---

### Step 3: Assign to Months
```
Assign each month to a template:

Jan       Feb       Mar       Apr
[Winter▼] [Winter▼] [Shoulder▼] [Shoulder▼]

May       Jun       Jul       Aug
[Shoulder▼] [Summer▼] [Summer▼] [Summer▼]

Sep       Oct       Nov       Dec
[Shoulder▼] [Shoulder▼] [Winter▼] [Winter▼]

[✅ Apply Month Assignments]

Assignment Summary:
Summer Peak: Jun, Jul, Aug
Winter Off-Peak: Jan, Feb, Nov, Dec
Shoulder: Mar, Apr, May, Sep, Oct
```

**Actions:**
- 📅 Set each month's template
- ✅ Click "Apply Month Assignments"
- 👁️ Review assignment summary

---

## 🎯 Common Use Cases

### 2-Season Tariff (Summer/Winter)
```
Templates:
1. "Summer" → Jun, Jul, Aug, Sep
2. "Winter" → Oct, Nov, Dec, Jan, Feb, Mar, Apr, May
```

### 3-Season Tariff (Most Common)
```
Templates:
1. "Summer Peak" → Jun, Jul, Aug
2. "Winter Standard" → Jan, Feb, Nov, Dec
3. "Shoulder" → Mar, Apr, May, Sep, Oct
```

### 4-Season Tariff (Regional)
```
Templates:
1. "Summer Peak" → Jul, Aug
2. "Shoulder Summer" → Jun, Sep
3. "Shoulder Winter" → Mar, Apr, Oct
4. "Winter Off-Peak" → Nov, Dec, Jan, Feb, May
```

---

## 💡 Pro Tips

### Naming Templates
✅ **Good:** "Summer Peak", "Winter Off-Peak", "Shoulder"  
❌ **Avoid:** "Template 1", "Schedule A", "Test"

### Typical Patterns

**Commercial Peak Pattern:**
```
Hours 0-8:   Off-Peak (P0)
Hours 9-17:  Mid-Peak (P1)
Hours 18-21: On-Peak (P2)
Hours 22-23: Off-Peak (P0)
```

**Industrial Flat Pattern:**
```
All hours: Single Period (P0)
```

**Residential TOU Pattern:**
```
Hours 0-15:  Off-Peak (P0)
Hours 16-21: Peak (P1)
Hours 22-23: Off-Peak (P0)
```

---

## 🔄 Workflow Comparison

### Old Way (Month-by-Month)
```
1. Select January → Edit 24 hours
2. Copy to Feb, Nov, Dec (winter months)
3. Select June → Edit 24 hours
4. Copy to Jul, Aug (summer months)
5. Select March → Edit 24 hours
6. Copy to Apr, May, Sep, Oct (shoulder)

⏱️ Time: 5-10 minutes
❌ Error-prone: Lots of manual copying
```

### New Way (Template-Based)
```
1. Add 3 templates: Summer, Winter, Shoulder
2. Edit Summer template (24 hours)
3. Edit Winter template (24 hours)
4. Edit Shoulder template (24 hours)
5. Assign all months at once

⏱️ Time: 2-3 minutes
✅ Error-resistant: No manual copying
✅ Clear: Assignment summary shows everything
```

---

## 🎨 Visual Guide

### Template Structure
```
Template = Name + 24-Hour Schedule + Assigned Months

Example:
{
  name: "Summer Peak"
  schedule: [0,0,0,0,0,0,1,1,1,1,1,1,2,2,2,2,2,2,1,1,1,0,0,0]
  assigned_months: [5, 6, 7]  # Jun, Jul, Aug
}
```

### How It Converts to Final Schedule
```
Your Templates:
  Summer = [0,0,0,1,1,2,2,2,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  Winter = [0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0]

Your Assignments:
  Jan → Winter
  Jun → Summer

↓ Converts to ↓

Final Schedule Array:
  energyweekdayschedule[0] = [0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0]  # Jan
  energyweekdayschedule[5] = [0,0,0,1,1,2,2,2,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]  # Jun
```

---

## 🔍 Troubleshooting

### Issue: Template not appearing in dropdown
**Solution:** Make sure you clicked "➕ Add Template" after typing the name

### Issue: Changes not showing in preview
**Solution:** Click "✅ Save Template" after editing hours

### Issue: Months not updating
**Solution:** Click "✅ Apply Month Assignments" after selecting templates

### Issue: Can't delete template
**Solution:** You can't delete the last template. Add another one first.

### Issue: Want to rename template
**Solution:** Currently, delete the old one and create a new one with the correct name

---

## 📊 Feature Checklist

Use this to verify the feature works:

- [ ] Can add new templates with custom names
- [ ] Can edit template hours (0-23)
- [ ] Can save templates
- [ ] Can see template preview table
- [ ] Can assign months to templates
- [ ] Can see assignment summary
- [ ] Can delete templates
- [ ] Works for weekday schedules
- [ ] Works for weekend schedules
- [ ] Preview heatmap shows correct patterns
- [ ] Saved JSON has correct schedule arrays

---

## 🎯 Decision Tree: Which Mode to Use?

```
Do you need different schedules for different months?
│
├─ NO → Use "Simple (same for all months)"
│       ✓ Faster setup
│       ✓ One 24-hour pattern applies year-round
│
└─ YES → Use "Advanced (different by month)"
    │
    ├─ 1 unique schedule → Use Simple mode instead
    │
    └─ 2-10 unique schedules → Use Template mode!
        ✓ Define each unique schedule once
        ✓ Assign to applicable months
        ✓ Much faster than month-by-month
```

---

## 📖 Documentation Index

- **Quick Reference** (this file) - Cheat sheet
- **`TEMPLATE_WORKFLOW_GUIDE.md`** - Visual walkthrough with examples
- **`TEMPLATE_BASED_SCHEDULE_FEATURE.md`** - Complete feature documentation
- **`IMPLEMENTATION_SUMMARY.md`** - Technical implementation details
- **`README_TEMPLATE_FEATURE.md`** - Getting started guide

---

## 🚀 Getting Started Now

1. **Launch app:**
   ```bash
   streamlit run app.py
   ```

2. **Navigate:**
   - Click "🔧 Tariff Builder"
   - Click "📅 Energy Schedule"
   - Select "Advanced (different by month)"

3. **Follow 3 steps:**
   - Step 1: Add templates
   - Step 2: Edit templates
   - Step 3: Assign to months

4. **Preview:**
   - Scroll down to see heatmap
   - Verify colors match your expectations

5. **Save:**
   - Go to "🔍 Preview & Save"
   - Download JSON

---

## ⌨️ Keyboard Workflow Tips

1. **Tab** to move between fields quickly
2. **Enter** to submit forms
3. Use **dropdown arrow keys** to select options fast
4. **Ctrl+S** (in browser) won't work - use "Save" buttons

---

## 📞 Quick Help

**Question:** How many templates do I need?  
**Answer:** Usually 2-3 (Summer, Winter, Shoulder)

**Question:** Can templates be reused?  
**Answer:** Yes! Assign the same template to multiple months

**Question:** Do templates save to JSON?  
**Answer:** No - only the final schedules save. Templates are a UI helper.

**Question:** Can I switch between Simple and Advanced?  
**Answer:** Yes, anytime. Your data won't be lost.

**Question:** Works for Demand schedules too?  
**Answer:** Yes! Same workflow in the Demand Charges tab.

---

## ✅ You're Ready!

Print this card or keep it handy for quick reference.

**The template-based workflow makes TOU schedule creation 2-3x faster!**

---

*Last updated: 2025-11-01*  
*Version: 1.0*

