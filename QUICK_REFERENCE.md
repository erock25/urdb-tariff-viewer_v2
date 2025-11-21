# Quick Reference: Load Factor Analysis Enhancements

## What Changed?

The **Energy Distribution** section of the Load Factor Rate Analysis tool now:

1. ✅ **Only shows periods present in the selected month**
2. ✅ **Displays hour percentages** for each period

---

## Visual Example

### January 2024 - Seasonal Tariff

```
ℹ️ Only showing periods present in January. The following periods are not 
   scheduled this month: Summer Peak, Summer Off-Peak

💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────────────┬─────────────────────────────┐
│ Winter Peak                 │ Winter Off-Peak             │
│ 📊 40.3% of month's hours   │ 📊 59.7% of month's hours   │
│ ($0.2000/kWh)              │ ($0.1000/kWh)              │
│ [  100.0  ] %              │ [   0.0   ] %              │
└─────────────────────────────┴─────────────────────────────┘

Total: 100.0%
```

---

## What the Hour Percentage Means

**"📊 40.3% of month's hours"** means:
- This period occupies 40.3% of all hours in the selected month
- Accounts for both weekday and weekend schedules
- Considers actual calendar (weekday/weekend count)
- Always sums to 100% across all periods

---

## How to Use It

### 1. Select Your Month
Choose the month you want to analyze.

### 2. Review Active Periods
Only periods scheduled for that month will appear.

### 3. Check Hour Percentages
Use the percentages to understand time distribution:
- 📊 85% = dominant period (~20 hours/day)
- 📊 50% = half the month (~12 hours/day)
- 📊 15% = limited period (~3.6 hours/day)
- 📊 5% = minimal period (~1.2 hours/day)

### 4. Set Energy Distribution
Allocate energy percentages (must sum to 100%).

**Tip:** Calculate intensity factor to check realism:
```
Intensity Factor = Energy % ÷ Hour %

Examples:
- 50% energy ÷ 50% hours = 1.0x (average)
- 30% energy ÷ 15% hours = 2.0x (high, but realistic)
- 70% energy ÷ 15% hours = 4.7x (unrealistic!)
```

---

## Benefits at a Glance

| Feature | Benefit |
|---------|---------|
| **Period Filtering** | Can't enter data for periods that don't exist |
| **Hour Percentages** | See time distribution at a glance |
| **Info Messages** | Know which periods are excluded and why |
| **Enhanced Tooltips** | Full context including hour percentage |
| **Auto-Updates** | Changes when you select different month |
| **Calendar-Accurate** | Accounts for actual weekday/weekend counts |

---

## Common Scenarios

### Scenario 1: High Intensity Usage
```
Period:   On-Peak
Hours:    📊 12% of month
Energy:   30%
Intensity: 30% ÷ 12% = 2.5x
✅ Realistic: Equipment runs at 2.5x during peak hours
```

### Scenario 2: Unrealistic Usage
```
Period:   On-Peak  
Hours:    📊 5% of month
Energy:   50%
Intensity: 50% ÷ 5% = 10x
❌ Unrealistic: Would need 10x load during peak - verify!
```

### Scenario 3: Baseline Usage
```
Period:   Off-Peak
Hours:    📊 75% of month
Energy:   75%
Intensity: 75% ÷ 75% = 1.0x
✅ Perfect: Constant load throughout
```

---

## Tooltip Information

Hover over the (?) icon to see:
- Base rate ($/kWh)
- Adjustment (if any)
- Hour percentage for the month

Example tooltip:
```
Base rate: $0.1500/kWh + Adjustment: $0.0050/kWh

This period is present for 40.3% of January's hours
```

---

## New Functions (For Developers)

### `_get_active_energy_periods_for_month(tariff_data, month)`
Returns set of period indices present in the month.

### `_calculate_period_hour_percentages(tariff_data, month, year=2024)`
Returns dict mapping period index to percentage of month's hours.

---

## Files Modified

- `src/components/cost_calculator.py` - Core implementation
- `LOAD_FACTOR_ANALYSIS_FEATURE.md` - Updated documentation

---

## Testing

Both features extensively tested:
- ✅ Seasonal tariffs
- ✅ Year-round tariffs
- ✅ Flat rates
- ✅ Complex TOU schedules
- ✅ All 12 months
- ✅ Different calendar compositions

---

## Questions?

**Q: Why don't I see all the periods listed in the tariff?**  
A: Only periods scheduled in the selected month are shown. Change the month to see different periods.

**Q: What does the hour percentage represent?**  
A: The percentage of the month's total hours that period is scheduled for (weekdays + weekends combined).

**Q: Why do the percentages change when I change months?**  
A: Different months have different numbers of weekdays/weekends, affecting the distribution.

**Q: Can the percentages be used to suggest energy distribution?**  
A: They provide a starting point! If a period is 25% of hours and you use constant load, allocate ~25% energy.

**Q: What if percentages don't sum to 100%?**  
A: They always will! It's mathematically guaranteed by the calculation.

---

## Status

✅ **COMPLETE AND READY TO USE**

No configuration needed - features work automatically with any tariff!

---

*For detailed documentation, see:*
- *COMPLETE_ENHANCEMENT_SUMMARY.md - Comprehensive technical overview*
- *HOUR_PERCENTAGE_EXAMPLES.md - Real-world usage examples*
- *ENHANCEMENT_PERIOD_FILTERING.md - Period filtering details*
- *ENHANCEMENT_HOUR_PERCENTAGES.md - Hour percentage details*

