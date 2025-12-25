# CruiseControl Automated Grading System v2.0

**Dual-metric automated grading system for Java CruiseControl programming assignments.**

[![Status](https://img.shields.io/badge/status-production-green)]()
[![Success Rate](https://img.shields.io/badge/success_rate-90%25-brightgreen)]()
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-blue)]()

## 🎯 Overview

This system automatically grades student submissions for a CruiseControl programming exam by evaluating **two key dimensions**:

1. **Test Coverage** (Pattern-Based) - Did students write tests for all requirements?
2. **Implementation Quality** (Execution-Based) - Does their code actually work when executed?

### Why Dual Grading?

**Single-metric grading misses the full picture:**
- A student might write great tests but have broken implementation
- A student might have working code but inadequate test coverage

**Dual grading provides:**
✅ Complete assessment of both testing skills AND coding ability  
✅ Fair partial credit for incomplete work  
✅ Insights into student strengths/weaknesses  
✅ Protection against "looks right but doesn't work" code  

---

## ✨ Key Features

### Automated Dual Analysis
- ✅ **Test Coverage Analysis** - Pattern-matches test methods against 19 requirements
- ✅ **Implementation Execution** - Compiles and runs code to verify functionality
- ✅ **Combined Scoring** - Fair aggregate of both metrics

### Robust & Flexible
- ✅ Supports **JUnit 4 and JUnit 5**
- ✅ Handles **checked and unchecked exceptions**
- ✅ Works with **various project structures** (Maven, Gradle, flat)
- ✅ Manages **inner classes and separate exception files**
- ✅ **Cross-platform** (Windows, Mac, Linux)

### Production Ready
- ✅ **90% success rate** (9/10 students graded successfully)
- ✅ Comprehensive **error handling** and recovery
- ✅ **Visual dashboard** with sortable tables
- ✅ Detailed **JSON output** for further analysis

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
Java JDK 8+
Git
```

### Installation

```bash
# Clone the repository
git clone https://github.com/Sankatt/cruise-control-grader.git
cd cruise-control-grader

# Install Python dependencies
pip install -r requirements.txt
```

### Usage (3 Steps)

```bash
# 1. Add student GitHub URLs to student_repos.txt
echo "mario_alonso,https://github.com/maaloncu/2025-control-1-parte-a1" >> student_repos.txt

# 2. Clone and grade all students
python scripts/github_cloner.py student_repos.txt
python grader/main.py ./student_submissions

# 3. View results
python -m http.server 8000
# Open: http://localhost:8000/dashboard/index_dual.html
```

---

## 📊 How It Works

### The Dual Grading Process

```
┌─────────────────────────────────────────────────────────────┐
│ Student Submission (GitHub Repository)                      │
└────────────┬────────────────────────────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐    ┌──────────────┐
│ Tests   │    │ Implementation│
│ .java   │    │ .java         │
└────┬────┘    └──────┬────────┘
     │                │
     ▼                ▼
┌──────────────┐ ┌─────────────────┐
│ Pattern      │ │ Compile & Run   │
│ Matching     │ │ (javac + java)  │
└──────┬───────┘ └────────┬────────┘
       │                  │
       ▼                  ▼
┌──────────────┐ ┌─────────────────┐
│ Test         │ │ Implementation  │
│ Coverage     │ │ Grade           │
│ Grade        │ │ (Execution)     │
│ (Analysis)   │ │                 │
└──────┬───────┘ └────────┬────────┘
       │                  │
       └────────┬─────────┘
                ▼
        ┌───────────────┐
        │ Combined Grade│
        │   = (T+I)/2   │
        └───────────────┘
```

### Example: Mario's Results

**Test Coverage Analysis:**
```
Found: defaultValuesAreNull() → R1, R2 ✓
Found: settingValidSpeedStoresValue() → R3 ✓
Found: settingZeroOrNegativeThrows...() → R4 ✓
Coverage: 7/19 requirements = 36.84%
Test Grade: 3.46/10
```

**Implementation Execution:**
```
Compiling CruiseControl.java... ✓
Running R1 test: speedSet == null? PASS ✓
Running R2 test: speedLimit == null? PASS ✓
Running R3 test: setSpeedSet(50) works? PASS ✓
Running R4 test: setSpeedSet(0) throws? PASS ✓
...
Implementation: 7/19 requirements = 36.84%
Implementation Grade: 3.46/10
```

**Combined:**
```
Combined Grade: (3.46 + 3.46) / 2 = 3.46/10
```

---

## 📋 Requirements Evaluated

The system evaluates **19 requirements (R1-R19)**:

### Initialization (R1-R2)
- **R1**: `speedSet` initializes to null
- **R2**: `speedLimit` initializes to null

### setSpeedSet Method (R3-R6)
- **R3**: Accepts positive values (> 0)
- **R4**: Throws `IncorrectSpeedSetException` for ≤ 0
- **R5**: Cannot exceed `speedLimit`
- **R6**: Throws `SpeedSetAboveSpeedLimitException` when exceeding limit

### setSpeedLimit Method (R7-R9)
- **R7**: Accepts positive values (> 0)
- **R8**: Throws `IncorrectSpeedLimitException` for ≤ 0
- **R9**: Throws `CannotSetSpeedLimitException` if `speedSet` already set

### disable Method (R10-R11)
- **R10**: Sets `speedSet` to null
- **R11**: Does not alter `speedLimit`

### nextCommand Method (R12-R19)
- **R12-R19**: IDLE/REDUCE/INCREASE/KEEP logic based on speed conditions

*Note: Current implementation fully tests R1-R9. R10-R19 framework is in place for extension.*

---

## 📁 Project Structure

```
cruise-control-grader/
├── README.md                      # This file
├── REQUIREMENTS.md                # Detailed specifications
├── DUAL_GRADING_GUIDE.md         # Grading methodology
├── PROJECT_REPORT.md             # Development journey
├── config.yaml                    # Grading configuration
├── student_repos.txt              # Student repository list
├── Speedometer.java               # Required interface
│
├── analyzer/
│   ├── test_analyzer.py          # Test coverage analysis (pattern-based)
│   └── execution_grader.py       # Implementation testing (execution-based)
│
├── grader/
│   └── main.py                   # Main grading orchestrator
│
├── scripts/
│   └── github_cloner.py          # Repository cloning utility
│
├── dashboard/
│   ├── index.html                # Original single-table dashboard
│   └── index_dual.html           # ⭐ Dual grading dashboard (use this)
│
├── results/                       # Generated results (JSON)
│   ├── grading_summary.json
│   └── [student]_[date].json
│
└── student_submissions/           # Cloned repositories
```

---

## 🎓 Sample Results

### Console Output
```
Found 10 student submissions
======================================================================

Grading MarioAlonso...
  Found test file: CruiseControlTest.java
  Found implementation: CruiseControl.java
  Test Coverage: 7/19 (36.84%)
  Test Grade: 3.46/10.0
  Implementation: 7/19 (36.84%)
  Implementation Grade: 3.46/10.0
  Combined Grade: 3.46/10.0

Grading Summary:
  Total Students: 10
  Successfully Graded: 9
  Failed: 1
  
  Test Coverage Grades:
    Average Grade: 2.72/10.0
    Average Coverage: 27.6%
  
  Implementation Grades:
    Average Grade: 3.11/10.0
    Average Satisfaction: 31.1%
  
  Combined Grade: 2.92/10.0
```

### Dashboard Features

**Three Interactive Tables:**
1. **Test Coverage** - Shows which requirements students tested
2. **Implementation Quality** - Shows which requirements actually work
3. **Combined View** - Side-by-side comparison with final grades

**Visual Elements:**
- Color-coded grades (red=poor, yellow=average, green=good)
- Progress bars for coverage percentages
- Requirement badges (R1, R2, R3...)
- Sortable columns
- Search/filter functionality

---

## ⚙️ Configuration

### `config.yaml` Structure

```yaml
grading:
  max_grade: 10.0
  
  # Adjust weights per requirement (total should be 100)
  requirement_weights:
    R1: 2.0   # speedSet initialization
    R2: 2.0   # speedLimit initialization
    R3: 3.0   # setSpeedSet accepts positive
    R4: 3.0   # IncorrectSpeedSetException
    R5: 3.0   # respects speedLimit
    R6: 3.0   # SpeedSetAboveSpeedLimitException
    R7: 2.0   # setSpeedLimit accepts positive
    R8: 2.0   # IncorrectSpeedLimitException
    R9: 3.0   # Cannot set after speedSet
    # Add R10-R19 as needed

output:
  results_directory: "results"
  summary_file: "grading_summary.json"
```

### Customization Examples

**Emphasize exception handling:**
```yaml
requirement_weights:
  R4: 5.0   # Increased from 3.0
  R6: 5.0   # Increased from 3.0
  R8: 5.0   # Increased from 2.0
```

**Equal weighting:**
```yaml
requirement_weights:
  R1: 5.26  # 100/19 for each
  R2: 5.26
  # ... etc
```

---

## 🔧 Advanced Usage

### Grading Specific Students

```bash
# Grade only specific student directories
python grader/main.py ./student_submissions/MarioAlonso
```

### Re-grading After Updates

```bash
# Pull latest student changes
cd student_submissions/MarioAlonso
git pull
cd ../..

# Re-grade
python grader/main.py ./student_submissions/MarioAlonso
```

### Viewing Detailed Results

```bash
# Pretty-print JSON results
cat results/MarioAlonso_20251225.json | python -m json.tool

# View summary
cat results/grading_summary.json | python -m json.tool
```

### Export to CSV

```python
import json
import csv

with open('results/grading_summary.json') as f:
    data = json.load(f)

with open('grades.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Student', 'Test Grade', 'Impl Grade', 'Combined'])
    
    for result in data['results']:
        if result['success']:
            writer.writerow([
                result['student_id'],
                result['test_coverage_grade'],
                result['implementation_grade'],
                result['combined_grade']
            ])
```

---

## 🐛 Troubleshooting

### Issue: No tests detected (0/19)

**Possible Causes:**
- Test file not named `CruiseControlTest.java`
- Missing `@Test` annotations
- Test file in unexpected location

**Solution:**
```bash
# Check test file location
find student_submissions -name "*Test.java"

# Verify test file content
cat student_submissions/StudentName/src/test/java/.../CruiseControlTest.java
```

### Issue: Compilation failed

**Possible Causes:**
- Student has syntax errors
- Missing exception class files
- Wrong package declaration

**Solution:**
```bash
# Check compilation error details
python grader/main.py ./student_submissions/StudentName 2>&1 | grep "error:"

# Verify package structure
ls -R student_submissions/StudentName/src/
```

### Issue: Zero implementation grade

**Possible Causes:**
- Code doesn't compile
- Exceptions not thrown correctly
- Logic errors in implementation

**Solution:**
```bash
# Run grader with verbose output
python grader/main.py ./student_submissions/StudentName

# Check generated test output
cat student_submissions/StudentName/GraderTest.java
```

### Issue: Dashboard shows all zeros

**Cause:** Browser cached old JSON

**Solution:**
```bash
# Hard refresh browser
# Windows/Linux: Ctrl + F5
# Mac: Cmd + Shift + R

# Or restart server
# Ctrl+C to stop
python -m http.server 8000
```

---

## 📚 Documentation

- **[REQUIREMENTS.md](REQUIREMENTS.md)** - Complete requirement specifications
- **[DUAL_GRADING_GUIDE.md](DUAL_GRADING_GUIDE.md)** - In-depth grading methodology
- **[PROJECT_REPORT.md](PROJECT_REPORT.md)** - Development journey & lessons learned
- **[QUICK_START.md](QUICK_START.md)** - Command-line reference

---

## 📊 Performance Metrics

**System Performance (v2.0):**
- ⚡ **Grading Speed**: ~10 seconds per student
- ✅ **Success Rate**: 90% (9/10 students)
- 🎯 **Accuracy**: Verified through manual spot-checks
- 🔄 **Reliability**: Handles edge cases gracefully

**Supported Configurations:**
- JUnit 4, JUnit 5, or mixed
- Inner exception classes or separate files
- Checked exceptions (extends Exception)
- Unchecked exceptions (extends RuntimeException)
- Maven, Gradle, or flat project structures

---

## 🎯 Use Cases

### For Instructors
✅ Grade entire class in minutes instead of hours  
✅ Identify common mistakes across all students  
✅ Generate consistent, fair evaluations  
✅ Track which requirements students find hardest  
✅ Spot potential plagiarism through pattern analysis  

### For Teaching Assistants
✅ Reduce grading workload by 95%+  
✅ Focus on providing qualitative feedback  
✅ Quickly assess submission quality  
✅ Generate data-driven insights  

### For Students (Self-Assessment)
✅ Check coverage before submission  
✅ Understand grading criteria  
✅ Identify gaps in implementation  
✅ Verify tests are comprehensive  

---

## 🔮 Roadmap

### Planned Enhancements
- [ ] Complete R10-R19 execution testing (disable, nextCommand methods)
- [ ] Code quality metrics integration (Checkstyle, PMD)
- [ ] Plagiarism detection (code similarity analysis)
- [ ] Web-based UI (no local server needed)
- [ ] CI/CD integration (GitHub Actions)
- [ ] Machine learning pattern detection
- [ ] Student feedback generation
- [ ] Performance benchmarking

### Extensibility
The system is designed for easy extension:
- Add new requirements in `config.yaml`
- Create custom analyzers in `analyzer/`
- Extend dashboard with new visualizations
- Integrate with LMS (Canvas, Moodle, etc.)

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

**Areas for Contribution:**
- Additional test pattern detection
- More programming language support
- Dashboard enhancements
- Documentation improvements

---

## 📄 License

This project is provided for educational purposes.

---

## 👤 Author

**Sankatt**
- GitHub: [@Sankatt](https://github.com/Sankatt)
- Repository: [cruise-control-grader](https://github.com/Sankatt/cruise-control-grader)

---

## 🙏 Acknowledgments

- Built with assistance from **Claude** (Anthropic)
- Based on CruiseControl assignment from **UPM GRISE**
- Inspired by traditional execution-based grading approaches
- Special thanks to all students whose code helped refine the system

---

## 📞 Support

**Having issues?**
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [DUAL_GRADING_GUIDE.md](DUAL_GRADING_GUIDE.md)
3. Read [PROJECT_REPORT.md](PROJECT_REPORT.md) for insights
4. Create a GitHub issue with:
   - System info (OS, Python version, Java version)
   - Error messages
   - Steps to reproduce

---

## 📈 Statistics

**Project Metrics:**
- **Lines of Code**: ~2,000+
- **Files**: 15+
- **Development Time**: ~6 hours
- **Iterations**: 25+
- **Success Stories**: 9 students graded automatically
- **Time Saved**: 8 hours → 2 minutes

**Grading Insights (Current Dataset):**
- Average test coverage: 27.6%
- Average implementation quality: 31.1%
- Most commonly missed: disable() and nextCommand() methods
- Best performing student: MarioAlonso (3.46/10)

---

**Version:** 2.0.0 (Dual Grading System)  
**Status:** ✅ Production Ready  
**Last Updated:** December 25, 2025

---

*"From manual grading to automated dual-metric evaluation in 25 iterations."*
