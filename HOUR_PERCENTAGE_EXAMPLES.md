# Hour Percentage Labels - Visual Examples

## Example 1: Commercial TOU Rate (Typical)

### Tariff Structure
- **Off-Peak**: Midnight-7am, 11pm-midnight (weekdays), all day (weekends)
- **Mid-Peak**: 7am-1pm, 6pm-11pm (weekdays only)
- **On-Peak**: 1pm-6pm (weekdays only, 5 hours)

### January 2024 (31 days: 23 weekdays, 8 weekends)

#### Before Enhancement ❌
```
💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ Off-Peak                │ Mid-Peak                │ On-Peak                 │
│ ($0.0800/kWh)          │ ($0.1200/kWh)          │ ($0.1800/kWh)          │
│                         │                         │                         │
│ [  100.0  ] %          │ [   0.0   ] %          │ [   0.0   ] %          │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘

Total: 100.0%
```

**User's Problem:**
- 🤔 "How much of the month is each period?"
- 🤔 "Is On-Peak 5 hours/day or just on some days?"
- 🤔 "Does Off-Peak include weekends?"
- Must refer to TOU heatmap to understand distribution

#### After Enhancement ✅
```
💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ Off-Peak                │ Mid-Peak                │ On-Peak                 │
│ 📊 50.5% of month's     │ 📊 34.0% of month's     │ 📊 15.5% of month's     │
│    hours                │    hours                │    hours                │
│ ($0.0800/kWh)          │ ($0.1200/kWh)          │ ($0.1800/kWh)          │
│                         │                         │                         │
│ [  100.0  ] %          │ [   0.0   ] %          │ [   0.0   ] %          │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘

Total: 100.0%
```

**User's Insight:**
- ✅ "Off-Peak is 50.5% of hours - about half the month"
- ✅ "On-Peak is only 15.5% - roughly 3.7 hours/day"
- ✅ "Mid-Peak is 34% - substantial portion"
- No need to check heatmap - info is right there!

---

## Example 2: Seasonal Tariff

### Summer vs Winter Comparison

#### July 2024 (Summer)
```
ℹ️ Only showing periods present in July. The following periods are not 
   scheduled this month: Winter Peak, Winter Off-Peak

💡 Energy Distribution

┌─────────────────────────┬─────────────────────────┐
│ Summer Peak             │ Summer Off-Peak         │
│ 📊 25.0% of month's     │ 📊 75.0% of month's     │
│    hours                │    hours                │
│ ($0.2500/kWh)          │ ($0.1500/kWh)          │
│                         │                         │
│ [  100.0  ] %          │ [   0.0   ] %          │
└─────────────────────────┴─────────────────────────┘
```

**Insight:** Peak pricing applies 6 hours/day (25% of 24 hours)

#### January 2024 (Winter)
```
ℹ️ Only showing periods present in January. The following periods are not 
   scheduled this month: Summer Peak, Summer Off-Peak

💡 Energy Distribution

┌─────────────────────────┬─────────────────────────┐
│ Winter Peak             │ Winter Off-Peak         │
│ 📊 40.3% of month's     │ 📊 59.7% of month's     │
│    hours                │    hours                │
│ ($0.2000/kWh)          │ ($0.1000/kWh)          │
│                         │                         │
│ [  100.0  ] %          │ [   0.0   ] %          │
└─────────────────────────┴─────────────────────────┘
```

**Insight:** Winter peak is longer (40.3% vs 25% in summer)

---

## Example 3: Industrial Rate (5 TOU Periods)

### Tariff Structure
Complex schedule with 5 periods:
- Super Off-Peak: Midnight-6am (all days)
- Off-Peak: 6am-10am, 9pm-midnight (weekdays), 6am-midnight (weekends)
- Mid-Peak: 10am-1pm, 6pm-9pm (weekdays only)
- On-Peak: 1pm-6pm (weekdays only)
- Critical Peak: 3pm-4pm (weekdays only, summer months)

### August 2024 Display

```
💡 Energy Distribution

┌──────────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Super Off-Peak   │ Off-Peak         │ Mid-Peak         │ On-Peak          │ Critical Peak    │
│ 📊 25.0% of      │ 📊 42.9% of      │ 📊 19.4% of      │ 📊 11.3% of      │ 📊 1.3% of       │
│    month's hours │    month's hours │    month's hours │    month's hours │    month's hours │
│ ($0.0500/kWh)   │ ($0.0900/kWh)   │ ($0.1300/kWh)   │ ($0.2000/kWh)   │ ($0.5000/kWh)   │
│                  │                  │                  │                  │                  │
│ [   20.0  ] %   │ [   40.0  ] %   │ [   20.0  ] %   │ [   15.0  ] %   │ [    5.0  ] %   │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┴──────────────────┘

Total: 100.0%
```

**Key Insights:**
- ✅ Critical Peak is only 1.3% of hours (~18 minutes/day)
- ✅ Off-Peak dominates at 42.9% (10.3 hours/day)
- ✅ Allocating 5% energy to Critical Peak (which is 1.3% of time) = high intensity

**Energy Intensity Calculation:**
```
Critical Peak: 5.0% energy / 1.3% hours = 3.85x intensity factor
Off-Peak:     40.0% energy / 42.9% hours = 0.93x intensity factor
```

This helps users understand if their energy allocation is realistic!

---

## Example 4: Flat Rate

### Simple Flat Rate Tariff

```
💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────────┐
│ Flat Rate               │
│ 📊 100.0% of month's    │
│    hours                │
│ ($0.1200/kWh)          │
│                         │
│ [  100.0  ] %          │
└─────────────────────────┘

Total: 100.0%
```

**Insight:** Clearly shows this is a 24/7, year-round flat rate

---

## Example 5: Weekend-Only Period

### Tariff with Weekend Rate

```
💡 Energy Distribution

┌─────────────────────────┬─────────────────────────┐
│ Weekday Rate            │ Weekend/Holiday Rate    │
│ 📊 74.2% of month's     │ 📊 25.8% of month's     │
│    hours                │    hours                │
│ ($0.1500/kWh)          │ ($0.0800/kWh)          │
│                         │                         │
│ [   75.0  ] %          │ [   25.0  ] %          │
└─────────────────────────┴─────────────────────────┘
```

**January 2024:** 23 weekdays, 8 weekends
- Weekday Rate: 23/31 = 74.2% ✓
- Weekend Rate: 8/31 = 25.8% ✓

**User sees:** Energy allocation (75%/25%) closely matches time allocation (74.2%/25.8%)

---

## Example 6: Helping Identify Unrealistic Scenarios

### Scenario A: Realistic ✅

```
┌─────────────────────────┬─────────────────────────┐
│ Off-Peak                │ On-Peak                 │
│ 📊 85.0% of month's     │ 📊 15.0% of month's     │
│    hours                │    hours                │
│                         │                         │
│ [   80.0  ] %          │ [   20.0  ] %          │
└─────────────────────────┴─────────────────────────┘

Intensity factors:
- Off-Peak: 80% / 85% = 0.94x (slightly lower usage)
- On-Peak:  20% / 15% = 1.33x (33% higher usage)
✅ Reasonable - slightly higher usage during on-peak
```

### Scenario B: Questionable ⚠️

```
┌─────────────────────────┬─────────────────────────┐
│ Off-Peak                │ On-Peak                 │
│ 📊 85.0% of month's     │ 📊 15.0% of month's     │
│    hours                │    hours                │
│                         │                         │
│ [   30.0  ] %          │ [   70.0  ] %          │
└─────────────────────────┴─────────────────────────┘

Intensity factors:
- Off-Peak: 30% / 85% = 0.35x (very low usage)
- On-Peak:  70% / 15% = 4.67x (almost 5x higher!)
⚠️ Unrealistic - would require massive load increase during on-peak hours
```

**The hour percentages help users spot and correct unrealistic energy allocations!**

---

## Summary of Benefits

| Without Hour % | With Hour % |
|----------------|-------------|
| Must check TOU schedule separately | Info integrated in UI |
| Unclear which periods dominate | Immediately see time distribution |
| Can't judge if energy allocation is realistic | Can calculate intensity factors |
| No context for period prevalence | Full context at a glance |
| Difficult to understand seasonal differences | Easy comparison across months |

**Result:** Users make better-informed, more realistic assumptions about their energy distribution, leading to more accurate cost estimates.

