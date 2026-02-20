# Rigorous Property-Based Implementation Grader
## Formal Verification Approach for Academic Grading

---

## Overview

This grader uses **formal software testing methodologies** to rigorously verify student implementations:

1. **Equivalence Partitioning** - Systematic input space division
2. **Boundary Value Analysis** - Edge case testing
3. **Property-Based Testing** - Invariant verification
4. **State Machine Verification** - State transition correctness

---

## Why This Approach?

### Problems with Simple Test-Based Grading
- Students can pass with partial implementations
- Edge cases often missed
- No formal verification of properties
- Limited test coverage

### Advantages of Rigorous Grading
✅ **Systematic Coverage** - All input partitions tested
✅ **Formal Properties** - Mathematical invariants verified
✅ **Boundary Testing** - Edge cases explicitly covered
✅ **State Verification** - Object state consistency checked
✅ **Multiple Test Categories** - Comprehensive validation

---

## Testing Methodology

### 1. Equivalence Partitioning

**Concept:** Divide input space into equivalence classes where all inputs should behave similarly.

**For R4 (speedSet <= 0 throws exception):**
- **Invalid Partition:** speedSet ∈ (-∞, 0] → must throw exception
- **Valid Partition:** speedSet ∈ (0, ∞) → must succeed

**Test Cases Generated:**
```
R4_INVALID_0100: speedSet = -100  (representative)
R4_INVALID_0010: speedSet = -10   (representative)
R4_INVALID_0001: speedSet = -1    (boundary)
R4_INVALID_0000: speedSet = 0     (boundary)
```

---

### 2. Boundary Value Analysis

**Concept:** Test at the edges of equivalence partitions where errors often occur.

**For R5/R6 (speedSet vs speedLimit):**

Boundaries:
- `speedSet = speedLimit - 1` (valid, below limit)
- `speedSet = speedLimit` (valid, at boundary)
- `speedSet = speedLimit + 1` (invalid, exceeds)

**Test Cases:**
```python
speedLimit = 100:
  speedSet = 99  → PASS (R5)
  speedSet = 100 → PASS (R5) [boundary]
  speedSet = 101 → EXCEPTION (R6) [boundary]
```

---

### 3. Property-Based Testing

**Concept:** Define mathematical properties that must always hold.

**Properties Defined:**

**Property 1 (R4):**
```
∀ speedSet ∈ ℤ: speedSet ≤ 0 ⟹ throws IncorrectSpeedSetException
```

**Property 2 (R6):**
```
∀ speedSet ∈ ℤ: (speedLimit ≠ null ∧ speedSet > speedLimit) 
                 ⟹ throws SpeedSetAboveSpeedLimitException
```

**Property 3 (R3+R5):**
```
∀ speedSet ∈ ℤ⁺: (speedLimit = null ∨ speedSet ≤ speedLimit) 
                 ⟹ this.speedSet = speedSet
```

**Property 4 (State Consistency):**
```
∀ operations: exception thrown ⟹ state_before = state_after
```

---

### 4. State Machine Verification

**Concept:** Verify state transitions are correct.

**States:**
- `UNINITIALIZED`: Constructor called, speedSet/speedLimit = null
- `SPEED_SET`: speedSet has been set
- `LIMITED`: Both speedSet and speedLimit are set

**Transitions Tested:**
```
UNINITIALIZED --[setSpeedSet(valid)]--> SPEED_SET
SPEED_SET --[setSpeedSet(invalid)]--> SPEED_SET (no change)
SPEED_SET --[setSpeedLimit]--> LIMITED
LIMITED --[setSpeedSet(exceeds)]--> LIMITED (exception, no change)
```

---

## Test Case Structure

Each test case is formally specified:

```python
TestCase(
    id="R4_INVALID_0000",                    # Unique identifier
    category=TestCategory.BOUNDARY_VALUE,     # Test methodology
    requirement="R4",                         # Which requirement
    description="setSpeedSet(0) throws...",   # Human description
    
    # Design by Contract
    preconditions={'speedLimit': None},       # Must be true before
    input_params={'speedSet': 0},             # Inputs to test
    expected_behavior=ExpectedBehavior.EXCEPTION,  # Expected outcome
    expected_exception="IncorrectSpeedSetException",  # Specific exception
    postconditions={'speedSet': None}         # Must be true after
)
```

---

## Grading Criteria

### Satisfaction Threshold
A requirement is considered **satisfied** if:
- ≥80% of test cases pass
- All test categories have been covered
- No critical failures (wrong exception type)

### Test Categories Per Requirement

**R1, R2 (Initialization):**
- Equivalence Partition: 1 test each

**R3 (Valid Positive Values):**
- Equivalence Partition: 4 tests (representative values: 1, 50, 100, 1000)

**R4 (Invalid Values):**
- Boundary Value: 4 tests (-100, -10, -1, 0)
- Property-Based: 1 test (invariant verification)

**R5 (Respects Limit):**
- Equivalence Partition: 3 tests (below limit)
- Boundary Value: 1 test (equals limit)
- Property-Based: 1 test (sequential calls)

**R6 (Exceeds Limit):**
- Boundary Value: 3 tests (various exceedances)
- State Transition: 1 test (state preservation)

**Total:** 20+ comprehensive test cases

---

## Usage

### Basic Usage
```bash
python rigorous_implementation_grader.py path/to/CruiseControl.java
```

### Programmatic Usage
```python
from rigorous_implementation_grader import RigorousImplementationGrader

grader = RigorousImplementationGrader(student_dir)
result = grader.grade_implementation(cruise_control_file)

print(f"Grade: {result['grade']}/10.0")
print(f"Verified Properties: {result['properties_verified']}")
print(f"Test Cases Run: {result['total_test_cases']}")

# Detailed analysis per requirement
for req, analysis in result['requirement_analysis'].items():
    print(f"{req}: {analysis['satisfaction_rate']}% pass rate")
    if not analysis['satisfied']:
        print(f"  Failures: {analysis['failure_details']}")
```

---

## Output Format

### Success Output
```json
{
  "success": true,
  "verification_method": "Rigorous Property-Based Testing",
  "total_test_cases": 23,
  "requirements_satisfied": ["R1", "R2", "R3", "R5", "R6"],
  "requirements_missing": ["R4"],
  "grade": 8.33,
  
  "requirement_analysis": {
    "R4": {
      "satisfied": false,
      "total_tests": 5,
      "passed_tests": 3,
      "failed_tests": 2,
      "satisfaction_rate": 60.0,
      "categories_tested": ["boundary_value", "property_based"],
      "failure_details": [
        {
          "test_id": "R4_INVALID_0000",
          "reason": "NO_EXCEPTION"
        }
      ],
      "verification_method": "Property-Based + Equivalence Partitioning + Boundary Analysis"
    }
  },
  
  "properties_verified": [
    "PROP_R4_01",
    "PROP_R6_01",
    "PROP_R3_01",
    "PROP_STATE_01"
  ],
  
  "test_categories_used": [
    "equivalence_partition",
    "boundary_value",
    "property_based",
    "state_transition"
  ]
}
```

---

## Comparison with Simple Grader

| Aspect | Simple Grader | Rigorous Grader |
|--------|---------------|-----------------|
| Test Cases | ~6 (one per requirement) | ~23 (systematic coverage) |
| Methodology | Ad-hoc | Formal (EP, BVA, PBT) |
| Edge Cases | Minimal | Comprehensive |
| Properties | Not verified | Formally verified |
| Pass Criteria | Binary (pass/fail) | Threshold-based (80%) |
| State Verification | No | Yes |
| Failure Details | Basic | Detailed with category |

---

## Integration with Existing System

### Option 1: Replace execution_grader.py
```bash
cp rigorous_implementation_grader.py analyzer/execution_grader.py
```

### Option 2: Add as Alternative Grader
```python
# In main.py
from analyzer.rigorous_implementation_grader import RigorousImplementationGrader

# Use rigorous grader instead of simple grader
rigorous_grader = RigorousImplementationGrader(student_dir)
impl_analysis = rigorous_grader.grade_implementation(impl_file)
```

### Option 3: Dual Grading (Recommended for Validation)
```python
# Run both graders
simple_result = simple_grader.grade_implementation(impl_file)
rigorous_result = rigorous_grader.grade_implementation(impl_file)

# Compare results
if abs(simple_result['grade'] - rigorous_result['grade']) > 1.0:
    print("WARNING: Significant grade difference - review manually")
```

---

## Extending the Grader

### Adding New Test Cases
```python
# In _generate_test_cases()
test_cases.append(TestCase(
    id="R3_LARGE_VALUE",
    category=TestCategory.EQUIVALENCE_PARTITION,
    requirement="R3",
    description="Test with very large value",
    preconditions={'speedLimit': None},
    input_params={'speedSet': 999999},
    expected_behavior=ExpectedBehavior.SUCCESS,
    expected_value=999999
))
```

### Adding New Properties
```python
# In _define_properties()
PropertySpecification(
    id="PROP_CUSTOM_01",
    requirement="R3",
    property_name="Non-Negative After Success",
    property_description="∀ successful setSpeedSet → speedSet > 0",
    invariant="Success ⟹ speedSet > 0"
)
```

---

## Academic Benefits

### For Instructors
- **Rigorous grading** with formal justification
- **Detailed failure analysis** for feedback
- **Consistent evaluation** across all students
- **Multiple verification methods** ensure accuracy

### For Students
- **Clear expectations** through formal specifications
- **Detailed feedback** on what failed and why
- **Fair evaluation** using systematic testing
- **Learning opportunity** seeing formal methods in action

---

## Requirements for Running

### Dependencies
```bash
# Java compiler
javac --version  # Should be Java 8+

# Python
python --version  # Should be Python 3.7+
```

### File Structure
```
student_submission/
├── CruiseControl.java
├── IncorrectSpeedSetException.java
├── SpeedSetAboveSpeedLimitException.java
└── Speedometer.java (provided by grader)
```

---

## Troubleshooting

### Issue: All tests fail
**Cause:** Compilation errors
**Solution:** Check that all exception classes are present

### Issue: Low satisfaction rate on R4/R6
**Cause:** Missing or incomplete exception handling
**Solution:** Student needs to add proper exception throws

### Issue: State transition tests fail
**Cause:** State not preserved after exceptions
**Solution:** Student should not modify state before throwing

---

## Future Enhancements

1. **Mutation Testing** - Inject faults to verify test quality
2. **Coverage Analysis** - Measure code coverage of tests
3. **Automated Property Discovery** - Infer properties from spec
4. **Fuzzing** - Generate random inputs for stress testing
5. **Formal Verification** - Use SMT solvers for proof

---

## References

- **Equivalence Partitioning**: Myers, G. J. (2011). The Art of Software Testing
- **Boundary Value Analysis**: Beizer, B. (1990). Software Testing Techniques
- **Property-Based Testing**: Claessen & Hughes (2000). QuickCheck
- **Design by Contract**: Meyer, B. (1992). Applying "Design by Contract"

---

**Author:** Automated Grading System
**Version:** 1.0
**Date:** January 9, 2026
**Purpose:** Rigorous academic grading using formal methods
