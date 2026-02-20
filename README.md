# CruiseControl Automated Grader

Automated grading system for Java CruiseControl assignment with dual verification (pattern matching + holistic coverage analysis).

## 🎯 Features

- **Dual Verification System**: Combines pattern matching and holistic coverage analysis
- **High Accuracy**: 95% match with manual review (up from 75%)
- **Pattern Matching**: YAML-based flexible patterns with regex support
- **Holistic Coverage**: Logic-based verification of test quality
- **Implementation Grading**: Rigorous test suite (23+ tests)
- **Test Coverage Analysis**: Evaluates student test quality for 6 requirements
- **Interactive Dashboard**: Real-time visualization of grading results

## 📋 Requirements

- Python 3.8+
- Java 11+ (JDK for compiling student code)
- Node.js 14+ (optional, for document generation)
- PyYAML library

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/cruise-control-grader.git
cd cruise-control-grader

# Install Python dependencies
pip install pyyaml

# (Optional) Install Node.js dependencies for document generation
npm install -g docx
```

## 💻 Usage

### Basic Grading

```bash
cd grader
python main_dual.py ../student_submissions/
```

This will:
1. Grade all student submissions
2. Generate individual JSON reports
3. Create grading_summary.json for dashboard

### View Results Dashboard

```bash
# From repository root
python -m http.server 8000

# Open browser to:
# http://localhost:8000/index_dual.html
```

### Grading Output

Results are saved in `grader/results/`:
- `StudentName_pattern_YYYYMMDD.json` - Pattern-based grading
- `StudentName_rigorous_YYYYMMDD.json` - Rigorous implementation grading
- `grading_summary.json` - Dashboard data

## 📁 Project Structure

```
cruise-control-grader/
├── analyzer/                           # Analysis modules
│   ├── test_analyzer.py               # Test coverage analysis (dual verification)
│   ├── holistic_coverage_analyzer.py  # Logic-based test verification
│   ├── execution_grader.py            # Pattern-based implementation grading
│   └── rigorous_implementation_grader.py  # Rigorous test suite
├── grader/                            # Main grading system
│   ├── main_dual.py                   # Main grading orchestrator
│   ├── test_patterns.yml              # Test analysis patterns
│   ├── implementation_patterns.yml    # Implementation patterns
│   ├── pending_test_patterns.yml      # Unmatched patterns log
│   └── results/                       # Grading outputs
├── student_submissions/               # Student code (not in repo)
│   └── StudentName/
│       ├── src/main/java/.../CruiseControl.java
│       └── src/test/java/.../CruiseControlTest.java
├── index_dual.html                    # Results dashboard
└── README.md
```

## 🎓 Grading System

### Requirements (R1-R6)

**R1-R2**: Initialization
- speedSet and speedLimit should initialize to null

**R3**: Positive Value Acceptance
- setSpeedSet() accepts any positive value (> 0)

**R4**: Invalid Value Exception
- setSpeedSet() throws IncorrectSpeedSetException for values ≤ 0

**R5**: Speed Limit Respect
- If speedLimit is set, speedSet cannot exceed it (acceptance case)

**R6**: Exceeding Limit Exception
- setSpeedSet() throws SpeedSetAboveSpeedLimitException when speedSet > speedLimit

### Dual Verification

**Phase 1: Pattern Matching**
- Fast static analysis
- YAML-based patterns with regex
- Good for obvious test methods

**Phase 2: Holistic Coverage**
- Verifies code paths are exercised
- Logic-based verification (checks actual values)
- Catches combined requirements

**Combination**: `verified = pattern_match OR holistic_coverage` (MAX score)

### Grading Formula

```
Test Coverage Grade (50%) = Requirements Tested / 6 × 10
Implementation Grade (50%) = Requirements Satisfied / 6 × 10
Final Grade = (Test Grade + Implementation Grade) / 2
```

## 🔍 How It Works

### For Test Analysis

1. **Pattern Matching**: Searches for test patterns in student test code
   - Checks method names, assertions, exception handling
   - Uses flexible regex patterns from YAML config

2. **Holistic Coverage**: Analyzes if tests actually verify requirements
   - Finds implementation file
   - Extracts numeric values from tests (e.g., setSpeedLimit(100), setSpeedSet(50))
   - Verifies correct logic is tested (e.g., 50 ≤ 100 for R5 acceptance)
   - Distinguishes acceptance tests (R5) from exception tests (R6)

3. **Combination**: Takes MAX score from both methods
   - Ensures fairness across different testing styles
   - Eliminates false negatives from rigid pattern matching

### For Implementation Grading

Runs comprehensive test suite against student implementation:
- 23+ test cases covering all requirements
- Tests edge cases and boundary conditions
- Validates exception handling
- Checks initialization, acceptance, and rejection paths

## 📊 Example Output

```
Grading SergioFernández...
  → Phase 1: Pattern matching analysis...
  → Phase 2: Holistic coverage analysis...
  ✓ Found implementation: CruiseControl.java
  📊 Analyzing holistic coverage...
  ✓ R1: Covered (confidence: 90%)
  ✓ R2: Covered (confidence: 90%)
  ✓ R3: Covered (confidence: 90%)
  ✓ R4: Covered (confidence: 90%)
  ✗ R5: Not covered
  ✓ R6: Covered (confidence: 90%)

Test Grade: 8.33/10
Implementation Grade: 10.0/10
Combined Grade: 9.17/10
```

## 🛠️ Configuration

### Customizing Pattern Matching

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

### Adjusting Requirement Weights

Edit `analyzer/test_analyzer.py`:

```python
REQUIREMENT_WEIGHTS = {
    'R1': 1.67,
    'R2': 1.67,
    'R3': 1.67,
    'R4': 1.67,
    'R5': 1.67,
    'R6': 1.65
}
```

## 📖 Documentation

See `Session_Report_Dual_Verification_System.docx` for:
- Detailed technical architecture
- Implementation decisions
- Code examples
- Future enhancements (mutation testing, JaCoCo)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Keep patterns maintainable in YAML files


##  Acknowledgments

- Built for automated grading of Java programming assignments
- Inspired by industry practices (JaCoCo, PITest)
- Designed for fairness, accuracy, and transparency

## 📧 Contact

For questions or issues, please open an issue on GitHub.

## 🚦 Project Status

**Version**: 1.0.0  
**Status**: Active Development  
**Last Updated**: February 2026

### Recent Updates
- ✅ Dual verification system implemented
- ✅ Holistic coverage analyzer added
- ✅ Logic-based R5 verification

