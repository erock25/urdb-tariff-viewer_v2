# Load Factor Analysis - Before vs After Comparison

## Before Enhancement ❌

### Problem Scenario
Tariff with 4 energy periods:
- Period 0: Summer Peak ($0.25/kWh)
- Period 1: Summer Off-Peak ($0.15/kWh)
- Period 2: Winter Peak ($0.20/kWh)
- Period 3: Winter Off-Peak ($0.10/kWh)

User selects **January** (winter month) and the tool shows:

```
💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│ Summer Peak         │ Summer Off-Peak     │ Winter Peak         │ Winter Off-Peak     │
│ ($0.2500/kWh)       │ ($0.1500/kWh)       │ ($0.2000/kWh)       │ ($0.1000/kWh)       │
│ [    0.0   ] %      │ [    0.0   ] %      │ [   50.0   ] %      │ [   50.0   ] %      │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

Total: 100.0%
```

**Issues:**
1. ❌ Shows "Summer Peak" and "Summer Off-Peak" even though these periods don't exist in January
2. ❌ User could accidentally enter percentages for summer periods
3. ❌ No indication that summer periods are not valid for January
4. ❌ Confusing - user has to manually check the TOU schedule to know which periods are valid
5. ❌ Calculation would use summer rates if user entered values, creating unrealistic scenario

---

## After Enhancement ✅

### Same Scenario with Enhancement
User selects **January** (winter month) and the tool now shows:

```
💡 Energy Distribution

ℹ️ Only showing periods present in January. The following periods are not 
   scheduled this month: Summer Peak, Summer Off-Peak

Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────┬─────────────────────┐
│ Winter Peak         │ Winter Off-Peak     │
│ ($0.2000/kWh)       │ ($0.1000/kWh)       │
│ [  100.0   ] %      │ [    0.0   ] %      │
└─────────────────────┴─────────────────────┘

Total: 100.0%
```

**Benefits:**
1. ✅ Only shows periods that actually exist in January (Winter Peak, Winter Off-Peak)
2. ✅ Clear info message explains which periods are excluded
3. ✅ Impossible to enter percentages for non-existent periods
4. ✅ Cleaner, simpler UI with fewer options
5. ✅ First active period auto-defaults to 100%
6. ✅ Guarantees accurate calculations aligned with actual TOU schedule

---

## When User Switches to July

```
💡 Energy Distribution

ℹ️ Only showing periods present in July. The following periods are not 
   scheduled this month: Winter Peak, Winter Off-Peak

Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────┬─────────────────────┐
│ Summer Peak         │ Summer Off-Peak     │
│ ($0.2500/kWh)       │ ($0.1500/kWh)       │
│ [  100.0   ] %      │ [    0.0   ] %      │
└─────────────────────┴─────────────────────┘

Total: 100.0%
```

**Dynamic Behavior:**
- Tool automatically switches to show only Summer periods
- Info message updates to indicate Winter periods are excluded
- Inputs reset to defaults for the new active periods

---

## For Tariffs with All Periods Year-Round

If a tariff has periods that apply to all months (e.g., Off-Peak, Mid-Peak, On-Peak), the tool shows all periods with no info message:

```
💡 Energy Distribution
Specify the percentage of energy consumption in each rate period (must sum to 100%):

┌─────────────────────┬─────────────────────┬─────────────────────┐
│ Off-Peak            │ Mid-Peak            │ On-Peak             │
│ ($0.0800/kWh)       │ ($0.1200/kWh)       │ ($0.1800/kWh)       │
│ [  100.0   ] %      │ [    0.0   ] %      │ [    0.0   ] %      │
└─────────────────────┴─────────────────────┴─────────────────────┘

Total: 100.0%
```

**No filtering needed** - all periods are valid for all months.

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **User Experience** | Confusing - shows all periods | Clear - shows only valid periods |
| **Error Prevention** | Can enter invalid data | Prevents invalid entries |
| **Information** | No guidance | Clear info messages |
| **Accuracy** | Risk of unrealistic scenarios | Guaranteed accurate scenarios |
| **Efficiency** | Need to check TOU schedule separately | Automatic filtering |
| **UI Complexity** | Always shows all periods | Adaptive to selected month |

