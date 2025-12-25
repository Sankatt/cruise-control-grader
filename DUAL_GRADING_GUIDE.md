# Dual Grading System

## 🎯 Two-Part Grading

Your grading system now evaluates students on **TWO** dimensions:

### 1. Test Coverage (What they tested)
- **Analyzes:** `CruiseControlTest.java`
- **Checks:** Which requirements did the student write tests for?
- **Grade:** Based on how many of the 19 requirements have test coverage

### 2. Implementation Quality (What they implemented)
- **Analyzes:** `CruiseControl.java`
- **Checks:** Which requirements did the student actually implement correctly?
- **Grade:** Based on how many of the 19 requirements are satisfied in the code

### 3. Combined Grade
- **Formula:** `(Test Coverage Grade + Implementation Grade) / 2`
- **Purpose:** Overall assessment of the student's work

---

## 🚀 How to Use

### Run the Dual Grading System

```powershell
# Grade all students (now analyzes both test and implementation files)
python grader/main.py ./student_submissions
```

### View Results

**Option 1: New Dual Dashboard**
```powershell
python -m http.server 8000
# Then open: http://localhost:8000/dashboard/index_dual.html
```

**Option 2: Original Dashboard (Test Coverage Only)**
```powershell
# Open: http://localhost:8000/dashboard/index.html
```

---

## 📊 What Gets Graded

### Test Coverage Example:

Student writes this test:
```java
@Test
void defaultValuesAreNull() {
    assertNull(cc.getSpeedSet());     // Tests R1 ✓
    assertNull(cc.getSpeedLimit());   // Tests R2 ✓
}
```
**Result:** R1 and R2 are marked as "tested"

### Implementation Quality Example:

Student implements this:
```java
public CruiseControl(Speedometer speedometer) {
    this.speedometer = speedometer;
    this.speedSet = null;      // Implements R1 ✓
    this.speedLimit = null;    // Implements R2 ✓
}
```
**Result:** R1 and R2 are marked as "implemented"

---

## 🔍 Understanding the Results

### Scenario 1: Good Tests, Bad Implementation
```
Test Coverage Grade: 8.0/10 (wrote tests for 15/19 requirements)
Implementation Grade: 3.0/10 (only implemented 6/19 correctly)
Combined Grade: 5.5/10
```
**Interpretation:** Student knows WHAT to test but couldn't implement it

### Scenario 2: Bad Tests, Good Implementation
```
Test Coverage Grade: 2.0/10 (only tested 4/19 requirements)
Implementation Grade: 7.0/10 (implemented 13/19 correctly)
Combined Grade: 4.5/10
```
**Interpretation:** Student can code but didn't write comprehensive tests

### Scenario 3: Good Overall
```
Test Coverage Grade: 8.0/10 (tested 15/19)
Implementation Grade: 8.5/10 (implemented 16/19)
Combined Grade: 8.25/10
```
**Interpretation:** Strong performance on both fronts

---

## 📋 Dashboard Features

### Table 1: Test Coverage
Shows which requirements each student wrote tests for

### Table 2: Implementation Quality
Shows which requirements each student correctly implemented

### Table 3: Combined View
Side-by-side comparison with combined grade

---

## ⚙️ How Implementation Analysis Works

The analyzer checks the actual code patterns:

**R1 & R2 - Initialization:**
```java
// Looks for:
this.speedSet = null;
this.speedLimit = null;
```

**R3 & R4 - setSpeedSet validation:**
```java
// Looks for:
if (speedSet <= 0) {
    throw new IncorrectSpeedSetException(...);
}
this.speedSet = speedSet;
```

**R5 & R6 - SpeedLimit checking:**
```java
// Looks for:
if (speedSet > this.speedLimit) {
    throw new SpeedSetAboveSpeedLimitException(...);
}
```

And so on for all 19 requirements...

---

## 🎓 Grading Philosophy

### Why Two Tables?

1. **Accountability:** Students can't get high grades by only writing tests OR only implementing
2. **Learning Assessment:** Shows if students understand requirements conceptually vs practically
3. **Fairness:** Partial credit for incomplete work in either dimension

### Weighting Options

You can adjust how much each dimension counts:

**Option A: Equal Weight (Current)**
```
Combined = (Test + Implementation) / 2
```

**Option B: Favor Implementation**
```
Combined = (Test * 0.3) + (Implementation * 0.7)
```

**Option C: Favor Testing**
```
Combined = (Test * 0.7) + (Implementation * 0.3)
```

To change this, edit `grader/main.py` in the `grade_student()` method.

---

## ⚠️ Important Notes

### What the Implementation Analyzer Does:
✅ Checks if code STRUCTURE matches requirements (has the right if-statements, exceptions, etc.)
✅ Uses pattern matching on the source code
✅ Verifies method signatures and logic flow

### What the Implementation Analyzer Does NOT Do:
❌ Actually RUN the code to see if it works
❌ Compile or execute the Java files
❌ Test edge cases or correctness beyond structure

### Limitations:
- **False Positives:** Code might LOOK right but not work
- **False Negatives:** Code might work but use different patterns
- **Style Variations:** Students might implement correctly in unexpected ways

**Recommendation:** Use as a first-pass automated grading, then manually review borderline cases.

---

## 📈 Next Steps

1. **Run on all students** and compare the two tables
2. **Validate results** - manually check a few students to see if detection is accurate
3. **Adjust patterns** in `analyzer/implementation_analyzer.py` if needed
4. **Set final weights** for combined grade based on your course objectives

---

## 🔧 Customization

### To adjust requirement weights:
Edit `config.yaml`:
```yaml
requirement_weights:
  R1: 3.0  # Increase importance
  R2: 3.0
  R3: 4.0  # Higher weight
```

### To modify implementation detection:
Edit `analyzer/implementation_analyzer.py` and adjust the regex patterns in each `check_*` method.

---

## 💡 Example Use Case

Professor wants to know:
1. "Which students understand the requirements but can't code?" → Look for high Test / low Implementation
2. "Which students can code but don't test properly?" → Look for low Test / high Implementation
3. "Which students are overall strong?" → Look at Combined Grade

The dual table system makes all these analyses possible!
