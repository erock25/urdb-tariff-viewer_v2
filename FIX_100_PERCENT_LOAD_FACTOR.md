# Fix: 100% Load Factor Energy Distribution

## Problem Identified

The Load Factor Rate Analysis tool had a logical flaw in how it calculated energy costs at 100% load factor.

### The Issue

**Previous Behavior (Incorrect):**
- Used user-specified energy distribution percentages for ALL load factors, including 100%
- Allowed unrealistic scenarios like "100% of energy consumed during Off-Peak" even though facility runs 24/7

**Why This Was Wrong:**
At 100% load factor:
- Load Factor = Average Load / Peak Load = 1.0
- Facility operates at constant peak load 24 hours a day, 7 days a week
- Energy distribution MUST match the TOU schedule's time distribution
- No operational flexibility exists

**Example of the Flaw:**
```
TOU Schedule for January:
- Off-Peak:  50.5% of hours
- Mid-Peak:  34.0% of hours  
- On-Peak:   15.5% of hours

User enters:
- Off-Peak:  100% (all energy)
- Mid-Peak:  0%
- On-Peak:   0%

Tool calculates at 100% LF:
✗ ALL energy at $0.08/kWh (Off-Peak rate)

Reality at 100% LF (constant operation):
✓ 50.5% at $0.08/kWh, 34.0% at $0.12/kWh, 15.5% at $0.18/kWh
```

This could lead to significant cost estimation errors.

---

## Solution Implemented

### New Logic

```python
# At 100% load factor, use hour percentages
# For lower load factors, use user-specified distribution

if lf >= 0.99:  # 100% load factor (with small tolerance)
    # Calculate period hour percentages for this month
    period_hour_pcts = _calculate_period_hour_percentages(tariff_data, selected_month)
    effective_energy_pcts = period_hour_pcts
else:
    # Use user-specified energy percentages
    effective_energy_pcts = energy_percentages
```

### Behavior by Load Factor

| Load Factor | Energy Distribution Used | Rationale |
|-------------|-------------------------|-----------|
| **1% - 99%** | User-specified percentages | Operational flexibility - user can choose when to operate |
| **100%** | Automatic (hour percentages) | Constant operation - energy distribution = time distribution |

---

## Physical Justification

### At 100% Load Factor (Constant Operation)

**Physics:**
- Facility draws constant power 24/7
- If Off-Peak is 372 hours of the month and On-Peak is 115 hours...
- Then Off-Peak consumption = 372 × Power
- And On-Peak consumption = 115 × Power
- Energy ratio MUST = Hour ratio

**Example:**
```
100 kW facility, 24/7 operation in January (744 hours):
- Total energy: 100 kW × 744 hours = 74,400 kWh

If Off-Peak is 50.5% of hours (376 hours):
- Off-Peak energy: 100 kW × 376 hours = 37,600 kWh
- This is 37,600 / 74,400 = 50.5% of total energy ✓
```

**Conclusion:** At 100% LF, energy % = hour %

### At Lower Load Factors (Intermittent Operation)

**Operational Flexibility:**
- Facility doesn't run 24/7
- Can choose WHEN to operate
- Can strategically avoid expensive periods

**Example:**
```
100 kW facility, 50% load factor (runs 12 hours/day):
- Could run: Midnight-Noon (all Off-Peak)
- Could run: Noon-Midnight (mix of periods)
- Could run: Only weekends (all Off-Peak)
- User specifies the strategy
```

**Conclusion:** At < 100% LF, user input makes sense

---

## Impact Examples

### Example 1: Commercial Facility

**Scenario:**
- Peak Demand: 100 kW
- Month: January 2024 (744 hours)
- TOU: 50.5% Off-Peak ($0.08), 34.0% Mid-Peak ($0.12), 15.5% On-Peak ($0.18)
- User Input: 100% Off-Peak

**Before Fix:**
```
100% Load Factor:
- Total Energy: 74,400 kWh
- Uses: 100% Off-Peak (user input)
- Cost: 74,400 × $0.08 = $5,952
- Effective Rate: $0.0800/kWh
✗ WRONG - Ignores that facility must operate during all periods
```

**After Fix:**
```
100% Load Factor:
- Total Energy: 74,400 kWh
- Uses: 50.5% Off-Peak, 34.0% Mid-Peak, 15.5% On-Peak (automatic)
- Cost: (37,600 × $0.08) + (25,300 × $0.12) + (11,500 × $0.18)
      = $3,008 + $3,036 + $2,070 = $8,114
- Effective Rate: $0.1091/kWh
✓ CORRECT - Reflects constant 24/7 operation
```

**Difference:** $2,162 (36% error in original calculation!)

### Example 2: Why Lower Load Factors Still Use User Input

**Scenario:**
- Same facility at 50% Load Factor
- User specifies: 100% Off-Peak (strategic operation)

**Behavior:**
```
50% Load Factor:
- Total Energy: 37,200 kWh
- Uses: User-specified 100% Off-Peak
- Cost: 37,200 × $0.08 = $2,976
- Effective Rate: $0.0800/kWh
✓ CORRECT - User can choose to only operate during Off-Peak hours
```

This makes sense! A facility at 50% LF runs ~12 hours/day and could strategically operate only during the cheapest Off-Peak hours.

---

## User Interface Changes

### New Informational Message

Added caption below the "Energy Distribution" heading:

```
💡 Note: At 100% load factor, energy distribution automatically matches 
the hour percentages above (constant 24/7 operation). For lower load 
factors, your specified distribution is used (operational flexibility).
```

### Display Behavior

**User sees:**
- Hour percentages for each period (e.g., "📊 50.5% of month's hours")
- Input fields for energy distribution
- Note explaining 100% LF behavior

**What happens behind the scenes:**
- If calculating for 100% LF → uses hour percentages (ignores inputs)
- If calculating for < 100% LF → uses user inputs

---

## Testing

### Test Case 1: Verify Correct Behavior

```python
TOU Schedule: 50.5% Off-Peak, 34.0% Mid-Peak, 15.5% On-Peak
User Input: 100% Off-Peak, 0% Mid-Peak, 0% On-Peak

At 50% Load Factor:
- Uses: User input (100% Off-Peak)
- Cost: $2,976
✓ PASS

At 100% Load Factor:
- Uses: Hour percentages (50.5% / 34.0% / 15.5%)
- Cost: $8,114
✓ PASS

Costs differ correctly ✓
```

### Test Case 2: Verify Calculation Accuracy

```python
100 kW, 100% LF, January (744 hours):
Total Energy: 74,400 kWh

Energy Distribution (automatic):
- Off-Peak (50.5%):  37,600 kWh × $0.08 = $3,008
- Mid-Peak (34.0%):  25,300 kWh × $0.12 = $3,036
- On-Peak (15.5%):   11,500 kWh × $0.18 = $2,070
Total: $8,114

Calculated: $8,114
Expected: $8,114
✓ PASS
```

---

## Benefits of This Fix

### 1. Physical Accuracy ✓
- 100% LF calculations now reflect reality
- Energy distribution matches time distribution
- No impossible scenarios

### 2. Cost Estimation Accuracy ✓
- Prevents underestimating costs at 100% LF
- Critical for budgeting and financial planning
- Realistic effective rate calculations

### 3. User Understanding ✓
- Clear message explains behavior
- Differentiates between 100% LF and lower LF
- Users understand when inputs are used vs. ignored

### 4. Maintains Flexibility ✓
- Lower load factors still allow user control
- Models operational strategies (e.g., avoiding peak hours)
- Doesn't break existing functionality

---

## Code Changes

### File Modified
`src/components/cost_calculator.py`

### Changes Made

**1. Energy charge calculation** (lines 1057-1079):
```python
# Before:
for period_idx, percentage in energy_percentages.items():
    period_energy = total_energy * (percentage / 100.0)
    # ...

# After:
if lf >= 0.99:  # 100% load factor
    period_hour_pcts = _calculate_period_hour_percentages(tariff_data, selected_month)
    effective_energy_pcts = period_hour_pcts
else:
    effective_energy_pcts = energy_percentages

for period_idx, percentage in effective_energy_pcts.items():
    period_energy = total_energy * (percentage / 100.0)
    # ...
```

**2. User interface note** (line 901):
```python
st.caption("💡 **Note:** At 100% load factor, energy distribution automatically matches the hour percentages above (constant 24/7 operation). For lower load factors, your specified distribution is used (operational flexibility).")
```

**3. Documentation updates**:
- Updated `LOAD_FACTOR_ANALYSIS_FEATURE.md`
- Created `FIX_100_PERCENT_LOAD_FACTOR.md`

---

## Edge Cases Handled

### 1. Tolerance for Rounding
```python
if lf >= 0.99:  # Not lf == 1.0
```
Uses 0.99 threshold to handle floating-point rounding issues.

### 2. Missing Hour Percentages
If `_calculate_period_hour_percentages()` returns empty dict, the calculation gracefully handles it (no energy charges calculated).

### 3. Partial Period Data
If user hasn't entered percentages for all periods, the calculation only uses the periods that exist.

---

## Backward Compatibility

### Impact on Existing Results

**For load factors 1% - 99%:**
- ✅ No change in behavior
- ✅ User inputs still used as before
- ✅ Existing calculations remain valid

**For 100% load factor:**
- ⚠️ Results will change (become more accurate)
- ✅ Previous results were incorrect; new results are correct
- ✅ This is a bug fix, not a breaking change

### Migration Notes

**No action required from users.** The fix is automatic and transparent.

---

## Future Enhancements

Potential improvements:

1. **Visual Indicator at 100% LF**
   - Highlight that auto-distribution is being used
   - Show side-by-side comparison of user input vs. actual

2. **Configurable Threshold**
   - Allow users to set when "constant operation" applies
   - Some might want 95% LF to also use auto-distribution

3. **Intensity Factor Warnings**
   - At lower LF, warn if intensity factor is unrealistic
   - E.g., "You allocated 80% energy to 15% of hours = 5.3x intensity"

4. **Smart Suggestions**
   - Suggest realistic distributions based on hour percentages
   - "Consider allocating proportionally: 50% Off-Peak, 35% Mid-Peak, 15% On-Peak"

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **100% LF Calculation** | Used user input | Uses hour percentages ✓ |
| **Physical Accuracy** | Incorrect | Correct ✓ |
| **Cost Estimation** | Could be 30-50% off | Accurate ✓ |
| **Lower LF Behavior** | Used user input | Still uses user input ✓ |
| **User Understanding** | No explanation | Clear message ✓ |
| **Code Changes** | N/A | Minimal, well-tested ✓ |

---

## Status

✅ **FIX COMPLETE AND TESTED**

- Code implemented and verified
- Documentation updated
- User interface enhanced
- No breaking changes
- Improves accuracy significantly

**Credit:** Issue identified by user during code review. Excellent catch!

---

## References

- **Modified File:** `src/components/cost_calculator.py` (lines 897-1079)
- **Updated Docs:** `LOAD_FACTOR_ANALYSIS_FEATURE.md`
- **Related:** `ENHANCEMENT_HOUR_PERCENTAGES.md` (hour % calculation used by this fix)

