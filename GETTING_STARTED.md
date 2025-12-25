# Getting Started Guide

## Quick Start (5 minutes)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/cruise-control-grader.git
cd cruise-control-grader
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Prepare Student Repository List
Create a file `student_repos.txt` with student GitHub repositories:
```
student001,https://github.com/student001/cruise-control-exam
student002,https://github.com/student002/cruise-control
```

### Step 4: Clone Student Repositories
```bash
python scripts/github_cloner.py student_repos.txt
```

### Step 5: Run the Grading System
```bash
python grader/main.py ./student_submissions
```

### Step 6: View Results
Open `dashboard/index.html` in your browser to see the dashboard!

---

## Detailed Workflow

### 1. Setting Up Student Submissions

#### Option A: From GitHub (Automated)
```bash
# Create student_repos.txt with format:
# student_id,github_url

python scripts/github_cloner.py student_repos.txt ./student_submissions
```

#### Option B: Manual Setup
```bash
mkdir -p student_submissions
cd student_submissions
git clone https://github.com/student001/project student001
git clone https://github.com/student002/project student002
```

### 2. Analyzing Individual Student

To test a single student's test file:
```bash
python analyzer/test_analyzer.py ./student_submissions/student001/Test.java
```

Output:
```
======================================================================
TEST ANALYSIS REPORT
======================================================================
Test File: ./student_submissions/student001/Test.java
Test Methods Found: 8

Requirements Coverage: 12/19 (63.16%)

COVERED REQUIREMENTS:
  ✓ R1
  ✓ R2
  ✓ R3
  ...
```

### 3. Running Full Grading

Grade all students at once:
```bash
python grader/main.py ./student_submissions
```

This will:
1. Find all student directories
2. Locate test files
3. Analyze requirement coverage
4. Calculate grades
5. Generate JSON reports

### 4. Viewing Results

#### Option A: HTML Dashboard
Simply open `dashboard/index.html` in your browser.

#### Option B: JSON Files
Results are saved in `./results/`:
- `grading_summary.json` - Overall summary
- `student001_20241225.json` - Individual student results

Example individual result:
```json
{
  "student_id": "student001",
  "grade": 7.5,
  "analysis": {
    "requirements_covered": ["R1", "R2", "R3", "R4"],
    "requirements_missing": ["R5", "R6", "R7"],
    "coverage_percentage": 63.16
  }
}
```

---

## Understanding the Grading

### Grade Calculation
Grades are calculated based on requirement weights defined in `config.yaml`:

```yaml
requirement_weights:
  R1: 2.0   # 2 points for R1
  R2: 2.0   # 2 points for R2
  R3: 3.0   # 3 points for R3
  ...
```

Total possible points = 100  
Max grade = 10.0

**Formula**: `grade = (earned_points / 100) * 10`

### Requirement Detection
The analyzer identifies requirements by looking for:

1. **Test method names**
   - `testSpeedSetInitializationNull()` → R1
   - `testIncorrectSpeedSetException()` → R4

2. **Code patterns**
   - Exception handling: `@Test(expected = IncorrectSpeedSetException.class)`
   - Assertions: `assertEquals(null, cruise.getSpeedSet())`

3. **Comments**
   - `// Testing R3 - positive speedSet values`

---

## Customization

### Adjusting Grading Weights
Edit `config.yaml`:
```yaml
grading:
  max_grade: 10.0
  requirement_weights:
    R1: 5.0  # Make R1 worth more points
    R2: 5.0
```

### Changing Analysis Patterns
Edit `analyzer/test_analyzer.py` - `REQUIREMENT_PATTERNS` dictionary:
```python
REQUIREMENT_PATTERNS = {
    'R1': [
        r'speedSet.*null',
        r'your_custom_pattern'
    ],
}
```

---

## Troubleshooting

### No test file found
**Problem**: Student repository structure doesn't match expected paths.

**Solution**: The analyzer searches these paths:
- `./`
- `./src/test/java/`
- `./src/test/`
- `./test/`

Add custom paths in `grader/main.py` → `find_test_file()` method.

### Clone fails
**Problem**: Private repositories require authentication.

**Solution**: Set GitHub token:
```bash
export GITHUB_TOKEN=your_github_token
python scripts/github_cloner.py student_repos.txt
```

### Low requirement coverage detected
**Problem**: Analyzer isn't detecting tests properly.

**Solution**: Check that:
1. Test methods are named descriptively
2. Tests include comments indicating requirements
3. Tests use standard JUnit patterns

---

## Advanced Usage

### Batch Processing
Process 100+ students:
```bash
# Clone all repositories
python scripts/github_cloner.py large_student_list.txt

# Grade with progress
python grader/main.py ./student_submissions 2>&1 | tee grading.log
```

### Export to CSV
```python
import json
import csv

with open('results/grading_summary.json') as f:
    data = json.load(f)

with open('grades.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Student ID', 'Grade', 'Coverage %'])
    
    for result in data['results']:
        if result['success']:
            writer.writerow([
                result['student_id'],
                result['grade'],
                result['analysis']['coverage_percentage']
            ])
```

### Integration with LMS
Results can be imported into most Learning Management Systems:
1. Export to CSV (see above)
2. Import into Moodle/Canvas/Blackboard grade book

---

## Next Steps

1. **Improve Detection**: Review false positives/negatives and adjust patterns
2. **Add Execution Tests**: Actually run student code to verify functionality
3. **Automated Feedback**: Generate personalized feedback for each student
4. **Continuous Integration**: Set up GitHub Actions to grade on push

See [ROADMAP.md](ROADMAP.md) for future enhancements!
