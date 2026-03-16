# CruiseControl Automated Grader

Automated grading system for Java CruiseControl programming assignments. Evaluates both **test quality** (via execution-based mutation testing) and **implementation correctness** (via formal test suites).

---

## 🎯 What It Does

Students submit two files:
- `CruiseControl.java` — implement `setSpeedSet()` covering requirements R1–R6
- `CruiseControlTest.java` — unit tests proving their implementation is correct

The grader runs **5 analyzers** per student and produces two scores:

| Score | Method | Description |
|---|---|---|
| **Test Coverage** | Mutation testing (primary) | Compiles & runs student tests against 6 buggy mutants — one per requirement. If a test catches the bug, that requirement is covered. |
| **Implementation Quality** | Pattern + Rigorous graders | Compiles student's `CruiseControl.java` and runs 19+ formal test cases against it. |

---

## 📋 Requirements

- Python 3.8+
- Java 11+ (JDK — required for compiling and running student code)
- Node.js 14+ (optional, for document generation)

---

## 🚀 Installation

```bash
git clone https://github.com/Sankatt/cruise-control-grader.git
cd cruise-control-grader
pip install pyyaml
```

No other setup needed — JUnit/Mockito jars are downloaded automatically on first run into `analyzer/_jar_cache/`.

---

## 💻 Usage

```bash
cd grader
python main_dual.py ../student_submissions/
```

This grades all student submissions, prints a summary, and saves results to `grader/results/`.

### View Results Dashboard

After grading, regenerate the summary file so the dashboard shows the latest scores:

```bash
cd grader
python generate_summary.py
```

Then serve and open:

```bash
# From repository root
python -m http.server 8000
# Open: http://localhost:8000/index_dual.html
```

### Output Files

```
grader/results/
├── StudentName_pattern_YYYYMMDD.json    # Pattern + mutation grading
├── StudentName_rigorous_YYYYMMDD.json   # Rigorous implementation grading
└── grading_summary.json                 # Dashboard data
```

---

## 📁 Project Structure

```
cruise-control-grader/
├── analyzer/
│   ├── mutation_test_analyzer.py          # ★ Execution-based mutation testing
│   ├── test_analyzer.py                   # Static test coverage (original)
│   ├── improved_test_analyzer.py          # Static test coverage (stricter)
│   ├── execution_grader.py                # Pattern-based implementation grader
│   ├── rigorous_implementation_grader.py  # 19-test formal implementation grader
│   ├── holistic_coverage_analyzer.py      # Logic-based test verification
│   ├── _jar_cache/                        # JUnit/Mockito jars (auto-downloaded)
│   ├── test_patterns.yml
│   └── implementation_patterns.yml
├── grader/
│   ├── main_dual.py                       # Main orchestrator
│   ├── generate_summary.py                # Regenerates grading_summary.json for dashboard
│   └── results/                           # Grading outputs
├── student_submissions/                   # Student code (not in repo)
├── index_dual.html                        # Results dashboard
└── README.md
```

---

## 🎓 Requirements R1–R6

| Req | Description |
|---|---|
| R1 | `speedSet` initialises to `null` in the constructor |
| R2 | `speedLimit` initialises to `null` in the constructor |
| R3 | `setSpeedSet()` accepts any strictly positive value |
| R4 | `setSpeedSet()` throws `IncorrectSpeedSetException` when value ≤ 0 |
| R5 | `setSpeedSet()` accepts values ≤ `speedLimit` when limit is set |
| R6 | `setSpeedSet()` throws `SpeedSetAboveSpeedLimitException` when value > `speedLimit` |

Each requirement is worth **1.67 points** (6 × 1.67 ≈ 10).

---

## 🔬 How Mutation Testing Works

The `MutationTestAnalyzer` runs the following pipeline for each student:

1. **Strip Mockito** — pre-processes the student's test file to remove `@Mock`, `MockitoAnnotations`, `when().thenReturn()` etc., replacing `mock(Speedometer.class)` with a real anonymous stub returning `50`. This allows compilation without Mockito at runtime.

2. **Compile against reference** — compiles the cleaned test against a known-correct `CruiseControl` implementation. If this fails, the student's test has a genuine Java error.

3. **Run against reference** — all tests must pass on the correct implementation.

4. **Run against 6 mutants** — each mutant introduces exactly one bug:

| Mutant | Bug Introduced |
|---|---|
| M1 | Constructor sets `speedSet = 0` instead of `null` |
| M2 | Constructor sets `speedLimit = 0` instead of `null` |
| M3 | `setSpeedSet()` never assigns `this.speedSet` |
| M4 | Removes the `≤ 0` check — never throws `IncorrectSpeedSetException` |
| M5 | Throws exception whenever `speedLimit` is set, even within limit |
| M6 | Removes the `> speedLimit` check — never throws `SpeedSetAboveSpeedLimitException` |

5. **Score** — if a student's test fails on mutant Mx, requirement Rx is covered. Score = covered requirements / 6 × 10.

---

## 📊 Score Combination

```
Test Coverage  = mutation score (primary)
               → falls back to union of both static analyzers if mutation fails

Implementation = average of pattern grader + rigorous grader

Final Grade    = (Test Coverage + Implementation) / 2
```

Static analyzers (original + improved) are always run for comparison but do **not** override the mutation score.

---

## 📈 Example Output

```
Grading MarioAlonsoCuero...
  Mutation: ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']  grade=10.00
  Original:  ['R1', 'R2']  grade=3.34     ← static under-estimated
  Improved:  ['R1', 'R2']  grade=3.34
  COMBINED:  ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']  grade=10.00

  Pattern: 6/6  grade=10.00
  Rigorous: 6/6  grade=10.00  (19 test cases)
```

---

## 🛠️ Configuration

### Customising Pattern Matching

Edit `grader/test_patterns.yml`:

```yaml
R5:
  requirement: "Test that speedSet respects speedLimit"
  patterns:
    method_calls:
      - "setSpeedLimit"
    boundary_or_restriction:
      - "regex:setSpeedSet\\s*\\(\\s*120\\s*\\).*setSpeedLimit\\s*\\(\\s*120\\s*\\)"
```

### Requirement Weights

Edit `analyzer/test_analyzer.py`:

```python
REQUIREMENT_WEIGHTS = {
    'R1': 1.67, 'R2': 1.67, 'R3': 1.67,
    'R4': 1.67, 'R5': 1.67, 'R6': 1.65
}
```

---

## 📖 Documentation

See `CruiseControlGrader_SessionReport.docx` for full technical documentation including architecture, change log, per-student results, and known issues.

---

## 🚦 Project Status

- **Version:** 2.0.0
- **Status:** Active Development
- **Last Updated:** March 2026

### Recent Updates (March 2026)
- ✅ Execution-based mutation testing fully implemented (`mutation_test_analyzer.py`)
- ✅ Mockito stripping — student tests using `@Mock` / `Mockito.mock()` now compile and run correctly
- ✅ Static analysis retained for comparison and fallback
- ✅ 9/10 students grade correctly (1 failure is a genuine Java syntax error in the submission)

### Previous Updates (February 2026)
- ✅ Dual verification system implemented
- ✅ Holistic coverage analyzer added
- ✅ Logic-based R5 verification
