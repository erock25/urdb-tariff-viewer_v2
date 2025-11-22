# Critical Fix: Correct Physics-Based Maximum Load Factor Calculation

## Overview

Fixed a fundamental error in how the Load Factor Rate Analysis Tool calculated the maximum physically possible load factor. The previous implementation violated physical constraints and could produce impossible scenarios.

## The Problem

### Previous (Incorrect) Implementation

The tool previously calculated maximum load factor by **summing** the hour percentages for all periods where energy was allocated:

```python
# WRONG!
max_valid_lf = 0.0
for period_idx, energy_pct in energy_percentages.items():
    if energy_pct > 0 and period_idx in period_hour_pcts:
        max_valid_lf += period_hour_pcts[period_idx] / 100.0
```

**Why this was wrong:**
- Ignored the constraint that power during any period cannot exceed peak demand
- Could allow physically impossible scenarios
- Did not account for the relationship between energy and time for each individual period

### Physical Reality

At any load factor, for each period `i`:

- **Energy in period i** = `E_i%` × Total Energy
- **Hours in period i** = `H_i%` × Total Hours
- **Required power during period i** = Energy / Hours = `(E_i / H_i)` × Average Load

Since the facility cannot operate above peak demand:
- Required Power ≤ Peak Demand
- `(E_i / H_i)` × Average Load ≤ Peak Demand
- `(E_i / H_i)` × (LF × Peak Demand) ≤ Peak Demand
- **LF ≤ H_i / E_i** for every period where `E_i > 0`

**Therefore: Maximum physically possible LF = min(H_i / E_i) across all periods with energy**

## The Solution

### New (Correct) Implementation

```python
# Calculate the maximum physically possible load factor
max_valid_lf = 1.0  # Start at 100%
for period_idx, energy_pct in energy_percentages.items():
    if energy_pct > 0 and period_idx in period_hour_pcts:
        hour_pct = period_hour_pcts[period_idx]
        if hour_pct > 0:
            # This period constrains max LF to hour_pct / energy_pct
            period_max_lf = hour_pct / energy_pct
            max_valid_lf = min(max_valid_lf, period_max_lf)
        else:
            # Period has energy but 0 hours - physically impossible
            max_valid_lf = 0.0

# Cap at 100%
max_valid_lf = min(max_valid_lf, 1.0)
```

## Examples

### Example 1: Single Period Constraint

**Scenario:**
- Period A: 20% of month's hours, user allocates 40% of energy
- Period B: 80% of month's hours, user allocates 60% of energy

**Analysis:**
- Period A: Max LF = 20% / 40% = **0.50 (50%)**
- Period B: Max LF = 80% / 60% = 1.33 (not limiting)
- **Overall Max LF = min(50%, 133%) = 50%**

**Why:** At 50% LF, Period A requires full peak power. Beyond 50%, Period A would require MORE than peak power, which is physically impossible.

### Example 2: Multiple Period Constraints

**Scenario:**
- Peak Period: 10% of hours, 30% of energy → Max LF = 10/30 = 33.3%
- Mid-Peak Period: 30% of hours, 50% of energy → Max LF = 30/50 = 60%
- Off-Peak Period: 60% of hours, 20% of energy → Max LF = 60/20 = 300%

**Overall Max LF = min(33.3%, 60%, 300%) = 33.3%**

The Peak Period is the limiting constraint.

### Example 3: Balanced Distribution (100% LF Possible)

**Scenario:**
- Period A: 30% of hours, 30% of energy → Max LF = 30/30 = 100%
- Period B: 70% of hours, 70% of energy → Max LF = 70/70 = 100%

**Overall Max LF = min(100%, 100%) = 100%**

At 100% LF, the facility operates at constant peak power 24/7, and energy distribution perfectly matches hour distribution.

## Physical Interpretation

### What the Constraint Means

For a period representing `H%` of hours with `E%` of energy:

- **If E = H**: Period operates at average load (proportional to overall LF)
- **If E > H**: Period operates at HIGHER than average load (requires lower max LF)
- **If E < H**: Period operates at LOWER than average load (not limiting)

The constraint `LF ≤ H/E` ensures that during period `i`, the required power equals:
- Power = (E/H) × (LF × Peak) ≤ Peak
- This is satisfied when LF ≤ H/E

### At Maximum LF

When operating at the maximum physically possible LF, the most constraining period operates at exactly peak demand for its entire duration.

### Beyond Maximum LF

Beyond the maximum LF calculated from user's energy distribution, the tool shows 100% LF using hour percentages (constant 24/7 operation). This represents the theoretical upper bound where the facility runs at full power continuously.

## Changes Made

### 1. Core Calculation Function
**File:** `src/components/cost_calculator.py`  
**Function:** `_calculate_load_factor_rates()`

- Changed from summing hour percentages to calculating minimum ratio
- Added proper physical constraint checking
- Added handling for impossible scenarios (energy in 0-hour periods)

### 2. User Message Calculation
**File:** `src/components/cost_calculator.py`  
**Function:** `_render_load_factor_analysis_tool()`

- Updated pre-calculation max LF message to use correct formula
- Enhanced info messages to explain the physical constraint

### 3. Comprehensive Breakdown
**File:** `src/components/cost_calculator.py`  
**Function:** `_calculate_comprehensive_load_factor_breakdown()`

- Applied same correction to ensure consistency

### 4. User-Facing Documentation

Updated three places where users see explanations:

**Tool Description:**
```markdown
The maximum physically possible load factor is determined by your energy distribution. 
For each period: LF ≤ (hour %) / (energy %). The tool uses the most restrictive constraint.
Example: if a period is 20% of hours but you allocate 40% of energy there, max LF = 50%.
```

**Input Caption:**
```markdown
Your energy distribution determines the maximum physically possible load factor. 
For each period, the constraint is: LF ≤ (hour %) / (energy %). 
Example: if a period represents 20% of hours but you allocate 40% of energy there, 
max LF = 50% (otherwise power would exceed peak demand).
```

**Results Message:**
```markdown
Maximum physically possible load factor: X% (based on your energy distribution). 
Calculations from 1% to X% LF use your specified energy distribution. 
Additionally, 100% LF is calculated using hour percentages (constant 24/7 operation).
```

## Impact

### Before Fix (Problems)
❌ Could show load factors that were physically impossible  
❌ Allowed scenarios where power would exceed peak demand  
❌ Misled users about feasible operating conditions  
❌ Violated fundamental physics: power = energy / time  

### After Fix (Benefits)
✅ Respects physical constraint: power ≤ peak demand  
✅ Correctly identifies maximum feasible load factor  
✅ Provides accurate, actionable results  
✅ Educates users about the physics of load factor  
✅ Prevents impossible operational scenarios  

## Testing Recommendations

### Test Case 1: Single Limiting Period
- Set one period with high energy % but low hour %
- Verify max LF = hour% / energy%
- Confirm power during that period at max LF equals peak

### Test Case 2: Multiple Periods
- Set various energy distributions across multiple periods
- Verify max LF is minimum of all (hour% / energy%) ratios
- Confirm the most restrictive period limits overall LF

### Test Case 3: Balanced Distribution
- Set energy % = hour % for all periods
- Verify max LF = 100%
- Confirm 100% LF results in constant power

### Test Case 4: Edge Cases
- All energy in one period
- Energy in period with 0 hours (should be caught)
- Very small hour percentages

## Related Files

- `src/components/cost_calculator.py` - Main implementation
- `LOAD_FACTOR_ANALYSIS_FEATURE.md` - Feature documentation
- `ENHANCEMENT_PERIOD_FILTERING.md` - Related enhancement
- `COMPLETE_ENHANCEMENT_SUMMARY.md` - Enhancement history

## Technical Notes

### Mathematical Proof

Given:
- Peak demand: `P_peak` (kW)
- Load factor: `LF` (dimensionless, 0-1)
- Average load: `P_avg = LF × P_peak` (kW)
- Total hours in month: `H_total` (hours)
- Total energy: `E_total = P_avg × H_total` (kWh)

For period `i`:
- Hour percentage: `h_i` (0-100)
- Energy percentage: `e_i` (0-100)
- Hours in period: `H_i = (h_i/100) × H_total`
- Energy in period: `E_i = (e_i/100) × E_total`
- Power during period: `P_i = E_i / H_i`

Substituting:
```
P_i = [(e_i/100) × P_avg × H_total] / [(h_i/100) × H_total]
P_i = (e_i/h_i) × P_avg
P_i = (e_i/h_i) × LF × P_peak
```

Physical constraint:
```
P_i ≤ P_peak
(e_i/h_i) × LF × P_peak ≤ P_peak
LF ≤ h_i/e_i
```

Therefore: `LF_max = min(h_i/e_i)` for all `i` where `e_i > 0`

### Implementation Complexity
- Time complexity: O(n) where n is number of periods
- Space complexity: O(n) for storing period data
- No performance impact from the fix

