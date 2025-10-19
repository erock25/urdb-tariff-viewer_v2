# Tariff Builder - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

1. Launch app → Navigate to **🏗️ Tariff Builder** tab
2. Fill **Basic Info** (utility, name, description)
3. Set **Energy Rates** (number of periods, rates)
4. Configure **Schedule** (when rates apply)
5. Add **Fixed Charges** (monthly fee)
6. **Preview & Save** → Done!

---

## 📋 Required Fields Checklist

- ☑️ Utility Company Name
- ☑️ Rate Schedule Name  
- ☑️ Description
- ☑️ At least 1 Energy Rate > $0
- ☑️ Energy Schedule configured

---

## 🔧 7 Sections Overview

| Section | What It Does | Required? |
|---------|--------------|-----------|
| 📋 **Basic Info** | Utility name, rate name, sector | ✅ Yes |
| ⚡ **Energy Rates** | TOU period rates ($/kWh) | ✅ Yes |
| 📅 **Energy Schedule** | When each rate applies | ✅ Yes |
| 🔌 **Demand Charges** | TOU demand rates ($/kW) | ⬜ Optional |
| 📊 **Flat Demand** | Monthly demand charges | ⬜ Optional |
| 💰 **Fixed Charges** | Customer/service charges | ⬜ Optional |
| 🔍 **Preview & Save** | Validate and save | ✅ Yes |

---

## ⚡ Energy Rate Structure

### Number of Periods
Choose 1-12 TOU periods (most common: 2-4)

**Common Configurations:**
- **1 period**: Flat rate (no TOU)
- **2 periods**: Peak / Off-Peak
- **3 periods**: Peak / Mid-Peak / Off-Peak
- **4 periods**: Peak / Shoulder / Off-Peak / Super Off-Peak
- **6 periods**: Seasonal (Winter × 3) + (Summer × 3)

### For Each Period
- **Label**: Descriptive name (e.g., "Summer Peak")
- **Base Rate**: Energy charge in $/kWh
- **Adjustment**: Additional fees/credits
- **Total**: Auto-calculated (Base + Adjustment)

---

## 📅 Schedule Configuration

### Simple Mode (Recommended)
✅ Best for: Same pattern year-round  
✅ Set: 24-hour weekday pattern  
✅ Option: Use same for weekends or customize

### Advanced Mode
✅ Best for: Seasonal variations  
✅ Set: Different schedule per month  
✅ Feature: Copy between months

### Schedule Values
Enter period numbers (0, 1, 2...) matching your energy rates

**Example:**
- Hour 0-8: `0` (Off-Peak)
- Hour 9-16: `1` (Mid-Peak)
- Hour 17-21: `2` (Peak)
- Hour 22-23: `0` (Off-Peak)

---

## 💾 Saving Your Tariff

### Before Saving
1. ✅ All validation checks pass
2. ✅ Preview JSON looks correct
3. ✅ Filename is descriptive

### After Saving
1. 🔄 Refresh page (F5)
2. 📂 Find in sidebar: "👤 User Tariffs"
3. 🎯 Select and use in other tabs

### File Location
📁 `data/user_data/YourFileName.json`

---

## 🎯 Common Rate Structures

### Flat Rate (Simplest)
```
Energy: 1 period @ $0.12/kWh
Schedule: All hours → Period 0
Fixed: $10/month
```

### Basic TOU (2 periods)
```
Energy:
  Period 0: Off-Peak @ $0.10/kWh
  Period 1: Peak @ $0.25/kWh

Schedule (Weekday):
  Hours 0-15, 22-23: Period 0
  Hours 16-21: Period 1

Weekend: All Period 0
Fixed: $15/month
```

### Commercial TOU (3 periods)
```
Energy:
  Period 0: Off-Peak @ $0.12/kWh
  Period 1: Mid-Peak @ $0.18/kWh
  Period 2: Peak @ $0.28/kWh

Schedule (Weekday):
  Hours 0-8: Period 0
  Hours 9-11, 17-21: Period 1
  Hours 12-16: Period 2
  Hours 22-23: Period 0

Flat Demand: $5/kW
Fixed: $25/month
```

### Complex Commercial (6 periods)
```
Energy:
  Winter:
    Period 0: Off-Peak @ $0.11/kWh
    Period 1: Mid-Peak @ $0.19/kWh
    Period 2: Peak @ $0.35/kWh
  Summer:
    Period 3: Off-Peak @ $0.15/kWh
    Period 4: Mid-Peak @ $0.28/kWh
    Period 5: Peak @ $0.45/kWh

Schedule:
  Months 1-5, 10-12: Use Periods 0-2
  Months 6-9: Use Periods 3-5

Flat Demand:
  Season 0 (Winter): $8/kW
  Season 1 (Summer): $15/kW

Fixed: $50/month
```

---

## 🔍 Validation Guide

### ✅ Valid Tariff Checklist
- ✓ All required fields filled
- ✓ At least one non-zero energy rate
- ✓ Schedule periods match defined rates
- ✓ No missing or invalid data
- ✓ Green "✅ Valid" message shown

### ❌ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "Required fields missing" | Fill utility, name, description |
| "At least one rate should be non-zero" | Enter actual rate values |
| "Schedule references non-existent period" | Check period numbers match rate count |
| "Tariff doesn't appear in sidebar" | Refresh page (F5) |

---

## 🎨 Pro Tips

### Efficiency Tips
1. **Start Simple**: Create basic version first, enhance later
2. **Use Simple Mode**: Unless you need seasonal variations
3. **Copy Existing**: Download similar tariff as reference
4. **Test Immediately**: Use Cost Calculator to verify

### Accuracy Tips
1. **Reference Official Docs**: Always use utility's official tariff
2. **Include All Adjustments**: Add fuel adjustments to "adj" field
3. **Verify Peak Hours**: Double-check utility's definition
4. **Document Assumptions**: Use description/comments fields

### Best Practices
1. **Descriptive Labels**: "Summer Peak" not "Period 5"
2. **Consistent Units**: Verify $/kWh vs $/kW
3. **Test with Load Profile**: Validate realistic costs
4. **Save Frequently**: Download backup copies

---

## 📊 Field Units Reference

| Field | Units | Typical Range |
|-------|-------|---------------|
| Energy Rate | $/kWh | $0.05 - $0.50 |
| Energy Adjustment | $/kWh | -$0.10 - $0.10 |
| Demand Rate | $/kW | $0 - $50 |
| Flat Demand | $/kW | $0 - $30 |
| Fixed Charge | $/month | $0 - $500 |

---

## 🆘 Quick Troubleshooting

### Issue → Solution

**Can't save tariff**
→ Check validation messages, fix errors

**Schedule doesn't look right**
→ Review heatmap preview, adjust periods

**Wrong rates displaying**
→ Verify Base + Adjustment = Total

**Missing from sidebar**
→ Refresh page, check user_data folder

**Want to start over**
→ Click "🔄 Reset Form" button

---

## 🔗 Related Features

After creating tariff, use with:

- **⚡ Energy Rates Tab** → View rate heatmaps
- **🔌 Demand Rates Tab** → View demand charges
- **💰 Cost Calculator** → Calculate utility bills
- **📥 Download** → Backup your tariff JSON
- **✏️ Edit Mode** → Fine-tune existing tariffs

---

## 📱 Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh page | `F5` |
| Next field | `Tab` |
| Previous field | `Shift + Tab` |
| Expand section | `Enter` (on expander) |

---

## 📚 Learn More

- **Full Guide**: `TARIFF_BUILDER_GUIDE.md`
- **Technical Docs**: `TARIFF_BUILDER_IMPLEMENTATION.md`
- **URDB Format**: Check existing tariffs in `data/tariffs/`

---

## 🎯 Typical Workflow

```
Open App
   ↓
Tariff Builder Tab
   ↓
Basic Info (2 min)
   ↓
Energy Rates (2 min)
   ↓
Schedule (3 min)
   ↓
Optional: Demand/Fixed (2 min)
   ↓
Preview & Validate
   ↓
Save
   ↓
Refresh Page
   ↓
Use in Cost Calculator!
```

**Total Time: 5-10 minutes for simple tariff**

---

## 💡 Remember

- Start with **required fields** first
- Use **Simple Mode** for faster setup
- **Preview** before saving
- **Test** with Cost Calculator
- **Save frequently** to avoid data loss
- **Download backup** of important tariffs

---

**Need Help?** Check the full guide or look at example tariffs in `data/tariffs/`

**Ready?** Navigate to 🏗️ Tariff Builder and start creating! 🚀

