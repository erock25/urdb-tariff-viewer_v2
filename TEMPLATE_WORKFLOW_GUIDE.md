# Template-Based Schedule: Visual Workflow Guide

## 🎯 Quick Start Guide

### Before: Old Month-by-Month Approach
```
Edit January → Copy to other winter months
Edit June → Copy to other summer months  
Edit April → Copy to other shoulder months
(Lots of clicking and copying!)
```

### After: New Template-Based Approach
```
1. Create 3 templates: Summer, Winter, Shoulder
2. Edit each template once (24 hours each)
3. Assign months: Jan=Winter, Jun=Summer, etc.
(Done in 3 steps!)
```

---

## 📋 Step-by-Step Walkthrough

### Step 1: Manage Templates

**What you'll see:**
```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Manage Templates                                    │
├──────────────────────────────┬──────────────────────────────┤
│ Current Weekday Templates:   │ Add New Template:            │
│ • Template 1 (0 months)      │ [Summer Peak          ]      │
│                              │ [➕ Add Template]            │
├──────────────────────────────┴──────────────────────────────┤
│ Delete Template:                                            │
│ [Template 1 ▼]  [🗑️ Delete]                                │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
- ✏️ Enter a descriptive name (e.g., "Summer Peak", "Winter Off-Peak")
- ➕ Click "Add Template"
- 🔁 Repeat for each unique schedule (typically 2-3 templates)
- 🗑️ Delete the default "Template 1" if not needed

---

### Step 2: Edit Templates

**What you'll see:**
```
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Edit Templates                                      │
├─────────────────────────────────────────────────────────────┤
│ Select template to edit: [Summer Peak ▼]                   │
│                                                             │
│ Editing: Summer Peak                                        │
│ Set the TOU period for each hour:                          │
│                                                             │
│ 0:00  1:00  2:00  3:00  4:00  5:00                        │
│ [P0▼] [P0▼] [P0▼] [P0▼] [P0▼] [P0▼]                      │
│                                                             │
│ 6:00  7:00  8:00  9:00  10:00 11:00                       │
│ [P0▼] [P1▼] [P1▼] [P1▼] [P1▼] [P1▼]                      │
│                                                             │
│ 12:00 13:00 14:00 15:00 16:00 17:00                       │
│ [P1▼] [P1▼] [P2▼] [P2▼] [P2▼] [P2▼]                      │
│                                                             │
│ 18:00 19:00 20:00 21:00 22:00 23:00                       │
│ [P2▼] [P2▼] [P1▼] [P1▼] [P0▼] [P0▼]                      │
│                                                             │
│ [✅ Save Template]                                          │
│                                                             │
│ Template Preview:                                           │
│ Hour    Period                                              │
│ 0:00    0                                                   │
│ 1:00    0                                                   │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
- 🎯 Select template from dropdown
- ⏰ Set each hour to the appropriate TOU period
- 💾 Click "Save Template"
- 🔁 Repeat for each template
- 👁️ Review the preview table to confirm

**Tip:** Focus on defining the pattern correctly - you'll apply it to multiple months next!

---

### Step 3: Assign Templates to Months

**What you'll see:**
```
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Assign Templates to Months                          │
├─────────────────────────────────────────────────────────────┤
│ Assign each month to a template:                            │
│ ℹ️ Tip: Typically 2-3 unique schedules per year            │
│                                                             │
│ January        February       March          April         │
│ [Winter ▼]     [Winter ▼]     [Shoulder ▼]   [Shoulder ▼] │
│                                                             │
│ May            June           July           August        │
│ [Shoulder ▼]   [Summer ▼]     [Summer ▼]     [Summer ▼]   │
│                                                             │
│ September      October        November       December      │
│ [Shoulder ▼]   [Shoulder ▼]   [Winter ▼]     [Winter ▼]   │
│                                                             │
│ [✅ Apply Month Assignments]                                │
│                                                             │
│ ─────────────────────────────────────────────────────────  │
│ Assignment Summary:                                         │
│ Summer Peak: Jun, Jul, Aug                                  │
│ Winter Off-Peak: Jan, Feb, Nov, Dec                         │
│ Shoulder: Mar, Apr, May, Sep, Oct                           │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
- 📅 Select appropriate template for each month
- ✅ Click "Apply Month Assignments"
- 👁️ Review the assignment summary
- ✓ Done! Your schedules are now configured for the entire year

---

## 🎨 Example: Creating a Typical 3-Season Tariff

### Common Utility Rate Pattern

Most commercial/industrial tariffs follow a seasonal pattern:

```
┌────────────────────────────────────────────────────────────┐
│                   YEAR-AT-A-GLANCE                         │
├────────────────────────────────────────────────────────────┤
│ Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec│
│  W    W    S    S    S    H    H    H    S    S    W    W │
│                                                            │
│ W = Winter (lower peak rates)                             │
│ S = Shoulder (moderate rates)                             │
│ H = Summer/Hot (highest peak rates)                       │
└────────────────────────────────────────────────────────────┘
```

### Template Definitions

**Template 1: "Summer Peak"** (June-August)
```
Hours      Period   Description
0-6        P0       Off-Peak (night)
7-13       P1       Mid-Peak (morning)
14-20      P2       On-Peak (afternoon heat)
21-23      P1       Mid-Peak (evening)
```

**Template 2: "Winter Standard"** (Jan-Feb, Nov-Dec)
```
Hours      Period   Description
0-8        P0       Off-Peak (night/morning)
9-17       P1       Mid-Peak (business hours)
18-23      P0       Off-Peak (evening)
```

**Template 3: "Shoulder"** (Mar-May, Sep-Oct)
```
Hours      Period   Description
0-8        P0       Off-Peak
9-21       P1       Mid-Peak (flat rate)
22-23      P0       Off-Peak
```

---

## 💡 Pro Tips

### Naming Conventions
✅ **Good names:** "Summer Peak", "Winter Off-Peak", "Shoulder Months"  
❌ **Avoid:** "Template 1", "Schedule A", "Test"

**Why?** Descriptive names help you remember what each template represents.

### Typical Template Counts
- **2 templates** - Simple summer/winter split
- **3 templates** - Summer, winter, shoulder seasons (most common)
- **4+ templates** - Complex regional variations

### Quick Edits
If you need to adjust one month:
1. Create a new template (e.g., "December Holiday")
2. Copy an existing template by setting hours similarly
3. Assign only that month to the new template

### Copy Functionality
Want to create a template similar to another?
1. Create new template (starts with all zeros)
2. Manually set hours to match your reference template
3. Make minor adjustments as needed

---

## ⚙️ Technical Notes

### What Happens Behind the Scenes

When you click "Apply Month Assignments":
```python
# Your templates...
templates = {
    'Summer Peak': { schedule: [0,0,0,0,0,0,1,1,2,2,2,2,2,2,2,1,1,1,0,0,0,0,0,0] },
    'Winter Standard': { schedule: [...] },
}

# ...are automatically converted to...
data['energyweekdayschedule'] = [
    winter_schedule,   # January
    winter_schedule,   # February
    shoulder_schedule, # March
    shoulder_schedule, # April
    shoulder_schedule, # May
    summer_schedule,   # June
    # ... etc for all 12 months
]
```

The calculation engine sees the same data structure as before - the template system is just a user-friendly wrapper!

---

## 🔄 Switching Between Modes

You can always switch between Simple and Advanced modes:

- **Simple → Advanced**: Your simple schedule becomes "Template 1" for all months
- **Advanced → Simple**: You'll start fresh with the simple editor (advanced templates stay in session but aren't used)

---

## 📊 Preview Your Work

After configuring templates:
1. Scroll down to **"Schedule Preview"**
2. View the **Weekday Schedule** heatmap
3. View the **Weekend Schedule** heatmap
4. Verify the patterns match your expectations

The heatmap shows all 12 months × 24 hours with color-coded periods.

---

## ❓ FAQ

**Q: Can I have different templates for weekday vs weekend?**  
A: Yes! You configure weekday and weekend templates separately.

**Q: What if I only need 1 template?**  
A: That's fine! Just use Simple mode instead - it's more efficient for that use case.

**Q: Can I rename a template?**  
A: Currently no, but you can delete and recreate with a new name (your assigned months will reset).

**Q: What happens if I don't assign all months?**  
A: Unassigned months will keep their previous schedule values.

**Q: Do templates work for Demand schedules too?**  
A: Yes! The exact same workflow applies to both Energy and Demand schedules.

---

## 🎉 You're Ready!

The template-based workflow makes creating complex TOU schedules fast and intuitive. Most tariffs can be configured in under 5 minutes!

**Happy tariff building! 🔧⚡**

