# 📊 Paper Analysis: Overtime in He et al. (2019)

## Question: Does the paper even use overtime?

**SHORT ANSWER: Yes, but it's UNDERSPECIFIED.**

## Paper's Treatment of Overtime

### 1. Variables Defined (Table 1)

```
srijk: Binary = 1 if nurse i on day j takes shift k with REGULAR pay
soijk: Binary = 1 if nurse i on day j takes shift k with OVERTIME pay
```

### 2. Parameters Defined

```
n3: Minimum number of REGULAR shifts a nurse need to take in the period
c1: Regular wage rate per shift
c2: Overtime wage rate per shift (paper says 1.5 × c1)
```

### 3. Constraints in Paper

**Constraint (1):** One shift per day maximum
```
Σk(srijk + soijk) ≤ 1  ∀i∈I, j∈J
```

**Constraint (4):** Overtime requires regular work
```
SOi ≤ SRi
```
Meaning: If nurse works overtime (SO=1), they must also work regular shifts (SR=1)

**Constraint (6):** Maximum total shifts
```
Σjk(srijk + soijk) ≤ n1  ∀i∈I
```

**Constraint (8):** **Minimum REGULAR shifts** (if working)
```
Σjk srijk ≥ n3 · SRi  ∀i∈I
```

### 4. What's MISSING in the Paper

**NO CONSTRAINT that caps regular shifts at n3!**

The paper does NOT include:
```
Σjk srijk ≤ n3 · SRi  ∀i∈I  ← THIS IS NOT IN THE PAPER!
```

## The Problem This Creates

### Mathematical Interpretation

Given the constraints:
- `Σjk srijk ≥ n3 · SRi` (minimum regular)
- `Σjk(srijk + soijk) ≤ n1` (maximum total)
- `c1 < c2` (regular cheaper than overtime)

The model can legally set:
- `srijk = any value from n3 to n1` (if SR=1)
- `soijk = 0` (no overtime)

Since `c1 < c2`, the optimizer will **always prefer** `sr` over `so`.

**Result:** Overtime variable exists but is **NEVER USED** in practice!

## Paper's Case Study (Section 5)

Looking at Table 3 and Section 5.1:
- **n1 = 24** (max total shifts)
- **n3 = 16** (min regular shifts)
- **Overtime capacity = 24 - 16 = 8 shifts**

The paper states:
> "Fulltime nurses work 36 h regular time per week"
> "a nurse may work at most one extra 9-hour overtime shift per week"

This implies **4 weeks × 1 overtime/week = 4 overtime shifts maximum**.

But Table 4 (results) shows:
- "No. of regular shift (srijk): 231"
- "No. of overtime shift (soijk): 25"

**They DO get overtime in their results!** But they don't explain HOW.

## Possible Explanations

### Theory 1: Different Cost Structure in Their Implementation
They might have used:
- Higher `q_plus` (emergency cost) to make overtime attractive
- Lower `c2` (overtime cost) relative to emergency

### Theory 2: Additional Unstated Constraint
They might have implemented (but not documented):
```
Σjk srijk ≤ n3 · SRi  (cap regular at minimum)
```

This would force the model to use overtime for shifts beyond n3.

### Theory 3: Different Demand Structure
Their scenarios might have created conditions where:
- Stage 1 needs to schedule MORE than n3 × nurses shifts
- Emergency (q_plus) is expensive enough that overtime becomes attractive

## What We Implemented

We added **Constraint 8b** (optional):
```python
if enforce_max_regular:
    Σjk srijk ≤ n3 · SRi  ∀i∈I
```

This **forces** the distinction between regular and overtime:
- First n3 shifts = regular (sr)
- Shifts beyond n3 = overtime (so)

## Comparison: Paper vs Our Model

| Aspect | Paper (He et al. 2019) | Our Model (Default) | Our Model (enforce_max_regular=True) |
|--------|----------------------|---------------------|-------------------------------------|
| Constraint 8 (min) | ✅ `sr ≥ n3·SR` | ✅ `sr ≥ n3·SR` | ✅ `sr ≥ n3·SR` |
| Constraint 8b (max) | ❌ Not mentioned | ❌ Not enforced | ✅ `sr ≤ n3·SR` |
| Overtime usage | Claimed in results (25 shifts) | Never used (economically inferior) | ✅ Used (forced by constraint) |
| Paper-compliant | ✅ Yes (as written) | ✅ Yes (as written) | ⚠️ Extended (adds constraint) |
| Practical | ❓ Unclear how they got overtime | ❌ No overtime separation | ✅ Clear separation |

## Conclusion

### The Root Problem

**The paper's formulation is INCOMPLETE for overtime.**

They define overtime variables and costs but don't provide sufficient constraints to force their use. The model will naturally prefer all regular shifts (cheaper) unless:
1. Additional constraints force overtime (our Constraint 8b), OR
2. Cost structure makes overtime attractive (very expensive emergency), OR  
3. There's an unstated implementation detail in their actual code

### Our Solution is BETTER

By adding the optional `enforce_max_regular` parameter:
- **Default mode**: Matches paper exactly (no overtime, but mathematically correct)
- **Practical mode**: Forces clear separation (overtime for shifts > n3)

This gives users CONTROL over whether they want:
- Pure cost optimization (paper mode)
- Clear shift categorization (practical mode)

### Recommendation for University Project

**Use `enforce_max_regular=True` and document it:**

```
"While He et al. (2019) define overtime variables (so_ijk), their 
formulation lacks a constraint to enforce overtime usage. We added
Constraint 8b to cap regular shifts at n3, ensuring shifts beyond
the minimum are classified as overtime. This provides clearer 
separation between shift types and matches the practical 
interpretation stated in the paper's parameters section."
```

---

**File:** PAPER_ANALYSIS.md  
**Date:** December 8, 2025  
**Status:** Complete Analysis
