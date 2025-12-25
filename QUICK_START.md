# 🚀 QUICK REFERENCE - CruiseControl Automated Grading System

## 📂 What You Have

A complete automated grading system with:
- ✅ Requirement detection & analysis
- ✅ GitHub repository cloning
- ✅ Automated grading calculation
- ✅ HTML dashboard for visualization
- ✅ JSON output format
- ✅ Complete documentation

---

## ⚡ Quick Commands

### 1. Setup (First Time Only)
```bash
cd cruise-control-grader
pip install -r requirements.txt
```

### 2. Clone Student Repositories
```bash
python scripts/github_cloner.py student_repos.txt
```

### 3. Grade All Students
```bash
python grader/main.py ./student_submissions
```

### 4. View Dashboard
Open `dashboard/index.html` in your browser

### 5. Analyze Single Test File
```bash
python analyzer/test_analyzer.py path/to/TestFile.java
```

---

## 📋 Task List: Easiest to Hardest

### 🟢 EASY (Do These First)
1. ✅ **Setup GitHub Repo** (15 min)
   - Already created! Just need to push to GitHub
   
2. **Test with Sample Data** (30 min)
   - Get 2-3 real student test files
   - Run analyzer on them
   - See what gets detected

3. **Fix student_repos.txt** (5 min)
   - Replace example URLs with real student repos
   - Format: `student_id,github_url`

### 🟡 MEDIUM (Do These Next)
4. **Improve Pattern Detection** (3-5 hours)
   - Review which requirements are missed
   - Adjust regex patterns in `analyzer/test_analyzer.py`
   - Test again

5. **Add Test Execution** (5 hours)
   - Currently only analyzes code
   - Add actual test running
   - See file: `grader/test_executor.py` (YOU NEED TO CREATE THIS)

6. **Enhance Dashboard** (3 hours)
   - Add charts
   - Add detailed student views
   - Add export to CSV

### 🟠 HARD (Do These Later)
7. **Automated Feedback** (10 hours)
   - Generate personalized reports
   - Email to students
   
8. **GitHub Actions CI/CD** (10 hours)
   - Auto-grade on commit
   
9. **Web Application** (20+ hours)
   - Full backend/frontend
   - Database
   - User authentication

---

## 🎯 Your Immediate Next Steps

### Step 1: Push to GitHub (15 minutes)
```bash
cd cruise-control-grader
git init
git add .
git commit -m "Initial commit: Automated grading system"
git remote add origin https://github.com/YOUR_USERNAME/cruise-control-grader.git
git push -u origin main
```

### Step 2: Get Real Data (1 hour)
- Contact 3 students who took the exam
- Get their GitHub repo URLs
- Add to `student_repos.txt`

### Step 3: Test Everything (1 hour)
```bash
# Clone repos
python scripts/github_cloner.py student_repos.txt

# Grade them
python grader/main.py ./student_submissions

# Check results
cat results/grading_summary.json

# View dashboard
# Open dashboard/index.html in browser
```

### Step 4: Validate Results (2 hours)
- Manually grade the same 3 students
- Compare with automated grades
- Check which requirements were detected correctly
- Note any issues

### Step 5: Document Issues (30 minutes)
Create a file `ISSUES.md`:
```markdown
# Issues Found

## False Positives
- R5 detected but test doesn't actually cover it
- Pattern too broad: [explain]

## False Negatives
- R7 not detected even though test is there
- Need better pattern: [explain]

## Missing Features
- Can't handle test files in weird locations
- No actual test execution
```

---

## 📊 Understanding the Output

### JSON Result Format
```json
{
  "student_id": "student001",
  "grade": 7.5,
  "analysis": {
    "requirements_covered": ["R1", "R2", "R3"],
    "requirements_missing": ["R4", "R5"],
    "coverage_percentage": 60.0,
    "test_methods": [
      {
        "name": "testInitialization",
        "requirements": ["R1", "R2"]
      }
    ]
  }
}
```

### Grading Formula
```
Total Points = Sum of requirement weights (100 points)
Grade = (Earned Points / 100) × 10
```

Example:
- R1 (2 pts) ✓
- R2 (2 pts) ✓
- R3 (3 pts) ✓
- Others (93 pts) ✗
- **Grade = (7/100) × 10 = 0.7/10** 😬

---

## 🔧 Common Issues & Solutions

### Issue: "No test file found"
**Solution**: Student repo has weird structure
```python
# Edit grader/main.py - add more search paths
search_paths = [
    student_dir / 'src' / 'test' / 'java',
    student_dir / 'tests',  # ADD THIS
    student_dir / 'Test',   # AND THIS
]
```

### Issue: "Requirements not detected"
**Solution**: Test names don't match patterns
```python
# Edit analyzer/test_analyzer.py
REQUIREMENT_PATTERNS = {
    'R1': [
        r'speedSet.*null',
        r'testR1',  # ADD THIS - student put R1 in name
    ]
}
```

### Issue: "Clone failed - authentication required"
**Solution**: Need GitHub token for private repos
```bash
export GITHUB_TOKEN=ghp_your_token_here
python scripts/github_cloner.py student_repos.txt
```

---

## 📁 File Structure Explained

```
cruise-control-grader/
├── README.md              # Overview
├── REQUIREMENTS.md        # All 19 requirements mapped
├── ROADMAP.md            # Future enhancements
├── GETTING_STARTED.md    # Detailed tutorial
├── config.yaml           # Grading weights & settings
├── requirements.txt      # Python dependencies
├── student_repos.txt     # Student GitHub URLs
│
├── analyzer/
│   └── test_analyzer.py  # ⭐ Core detection logic
│
├── grader/
│   └── main.py          # ⭐ Main grading orchestrator
│
├── scripts/
│   └── github_cloner.py # Clone repos from GitHub
│
├── dashboard/
│   └── index.html       # ⭐ Results visualization
│
└── results/             # Generated JSON outputs
    ├── grading_summary.json
    └── student001_20241225.json
```

---

## 💡 Pro Tips

1. **Start Small**: Test with 3 students before 100
2. **Validate Manually**: Compare with manual grading
3. **Iterate**: Make small improvements each week
4. **Document**: Keep notes on what works/doesn't
5. **Get Feedback**: Show results to supervisor regularly

---

## 🎓 Exam Requirements Checklist

All 19 requirements your system should detect:

**Initialization (2)**
- [ ] R1: speedSet initialized to null
- [ ] R2: speedLimit initialized to null

**setSpeedSet (4)**
- [ ] R3: Accepts positive values
- [ ] R4: Throws IncorrectSpeedSetException for ≤0
- [ ] R5: Cannot exceed speedLimit
- [ ] R6: Throws SpeedSetAboveSpeedLimitException

**setSpeedLimit (3)**
- [ ] R7: Accepts positive values
- [ ] R8: Throws IncorrectSpeedLimitException for ≤0
- [ ] R9: Throws CannotSetSpeedLimitException if speedSet exists

**disable (2)**
- [ ] R10: Sets speedSet to null
- [ ] R11: Does not alter speedLimit

**nextCommand (8)**
- [ ] R12: Returns IDLE when not initialized
- [ ] R13: Returns IDLE when disabled
- [ ] R14: Returns REDUCE when speed > speedSet
- [ ] R15: Returns INCREASE for road minimum violation
- [ ] R16: Returns INCREASE when speed < speedSet
- [ ] R17: Returns REDUCE when speed > speedLimit
- [ ] R18: Returns REDUCE when speed > road max
- [ ] R19: Returns KEEP when speed == speedSet

---

## 📞 Need Help?

### Good Questions to Ask:
- "How can I detect R5 when the test method is named testComplexScenario()?"
- "The analyzer gives 90% coverage but manual check shows 60%, why?"
- "Student put all tests in one method, how to handle?"

### Bad Questions:
- "It doesn't work, help!" (be specific!)
- "Can you fix it?" (yes, but you won't learn)

### Resources:
1. **REQUIREMENTS.md** - Detailed requirement specs
2. **GETTING_STARTED.md** - Step-by-step tutorial
3. **ROADMAP.md** - Future improvements
4. **Your supervisor** - Weekly check-ins

---

## ✅ Success Criteria

You know your system works when:
1. ✅ Grades correlate >85% with manual grading
2. ✅ Can process 100 students in <5 minutes
3. ✅ <5% error rate (failures/crashes)
4. ✅ Dashboard shows meaningful insights
5. ✅ You can explain how it works to supervisor

---

## 🎉 You're Ready!

Everything is set up. Just:
1. Push to GitHub
2. Get some real student data
3. Run the grader
4. Check the results
5. Iterate and improve

Good luck! 🚀
