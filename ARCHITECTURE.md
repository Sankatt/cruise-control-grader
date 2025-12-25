# System Architecture & Workflow

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED GRADING SYSTEM                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   STUDENTS   │      │    GITHUB    │      │     YOU      │
│              │─────▶│  Repositories│◀─────│   (Admin)    │
│ Submit Code  │      │              │      │ Configure &  │
└──────────────┘      └──────┬───────┘      │   Monitor    │
                             │               └──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  GitHub Cloner  │
                    │ (scripts/)      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Student      │
                    │  Submissions/   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Test Analyzer  │
                    │ (analyzer/)     │
                    │  - Find tests   │
                    │  - Detect R1-19 │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Grader      │
                    │  (grader/)      │
                    │  - Calculate    │
                    │  - Generate     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
            ┌──────────────┐   ┌──────────────┐
            │ JSON Results │   │  Dashboard   │
            │ (results/)   │   │ (dashboard/) │
            └──────────────┘   └──────────────┘
                    │                 │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   FINAL GRADES  │
                    │  & ANALYTICS    │
                    └─────────────────┘
```

## 🔄 Workflow Step-by-Step

### Phase 1: Data Collection
```
1. You create student_repos.txt
   ├─ student001,https://github.com/student001/repo
   ├─ student002,https://github.com/student002/repo
   └─ ...

2. Run: python scripts/github_cloner.py student_repos.txt
   ├─ Clones each repo
   ├─ Saves to student_submissions/
   └─ Generates clone_results.json

Result: student_submissions/
        ├─ student001/
        │  └─ Test.java
        ├─ student002/
        │  └─ CruiseControlTest.java
        └─ ...
```

### Phase 2: Analysis
```
3. Run: python grader/main.py ./student_submissions

For each student:
   ├─ Find test file
   │  └─ Search: src/test/java/, test/, ./
   │
   ├─ Analyze test file
   │  ├─ Extract test methods
   │  ├─ Match patterns for R1-R19
   │  └─ Calculate coverage
   │
   ├─ Calculate grade
   │  ├─ Sum requirement weights
   │  └─ Apply formula: (earned/100) × 10
   │
   └─ Save results
      └─ results/student001_20241225.json

Result: results/
        ├─ student001_20241225.json
        ├─ student002_20241225.json
        ├─ ...
        └─ grading_summary.json
```

### Phase 3: Visualization
```
4. Open: dashboard/index.html

Dashboard shows:
   ├─ Total students
   ├─ Average grade
   ├─ Average coverage
   ├─ Pass rate
   │
   └─ Table with:
      ├─ Student ID
      ├─ Grade (color coded)
      ├─ Coverage bar
      ├─ Requirements covered
      └─ Details button
```

## 📊 Data Flow

```
┌─────────────┐
│ Test.java   │
│ (Student)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  TEST ANALYZER                      │
│  ─────────────────────────────────  │
│                                     │
│  1. Load file content               │
│  2. Extract test methods            │
│     ├─ @Test annotations            │
│     └─ test* method names           │
│                                     │
│  3. For each method:                │
│     ├─ Match name patterns          │
│     ├─ Match code patterns          │
│     ├─ Detect exceptions            │
│     └─ Find assertions              │
│                                     │
│  4. Map to requirements             │
│     ├─ R1: speedSet.*null           │
│     ├─ R4: IncorrectSpeedSet...     │
│     └─ ...                          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  ANALYSIS RESULT                    │
│  {                                  │
│    "requirements_covered": [        │
│      "R1", "R2", "R3", "R4"         │
│    ],                               │
│    "requirements_missing": [        │
│      "R5", "R6", ...                │
│    ],                               │
│    "coverage_percentage": 60.0      │
│  }                                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  GRADER                             │
│  ─────────────────────────────────  │
│                                     │
│  Calculate weighted score:          │
│                                     │
│  R1 (covered) = 2.0 points  ✓       │
│  R2 (covered) = 2.0 points  ✓       │
│  R3 (covered) = 3.0 points  ✓       │
│  R4 (covered) = 3.0 points  ✓       │
│  R5 (missing) = 0.0 points  ✗       │
│  ...                                │
│  ───────────────────────────        │
│  Total:        10.0 / 100           │
│                                     │
│  Grade = (10/100) × 10 = 1.0/10     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  FINAL OUTPUT                       │
│  {                                  │
│    "student_id": "student001",      │
│    "grade": 1.0,                    │
│    "analysis": { ... },             │
│    "timestamp": "2024-12-25..."     │
│  }                                  │
└─────────────────────────────────────┘
```

## 🎯 Pattern Matching Logic

```
REQUIREMENT: R4 - Throw IncorrectSpeedSetException

DETECTION PATTERNS:
┌──────────────────────────────────────────────┐
│ 1. Exception in method signature:           │
│    @Test(expected = IncorrectSpeedSet...)    │
│                                              │
│ 2. Exception name in code:                  │
│    IncorrectSpeedSetException                │
│                                              │
│ 3. Test method name:                         │
│    testIncorrectSpeedSet()                   │
│    testNegativeSpeedSet()                    │
│    testZeroSpeedSet()                        │
│                                              │
│ 4. Code patterns:                            │
│    setSpeedSet(0)                            │
│    setSpeedSet(-1)                           │
│    "negative.*speedSet"                      │
└──────────────────────────────────────────────┘

MATCHING PROCESS:
┌──────────────────────────────────────────────┐
│ For each test method:                        │
│   ├─ Concatenate: name + code               │
│   ├─ Convert to lowercase                   │
│   ├─ For each pattern in R4:                │
│   │   ├─ Apply regex                        │
│   │   └─ If match: ADD R4 to covered        │
│   └─ Return set of covered requirements     │
└──────────────────────────────────────────────┘
```

## 🔧 Configuration Impact

```
config.yaml
│
├─ requirement_weights:
│  ├─ R1: 2.0  ──┐
│  ├─ R2: 2.0    │  These define
│  ├─ R3: 3.0    │  how much each
│  └─ ...        │  requirement is
│                 │  worth
│  Total: 100 ◄──┘
│
├─ grading:
│  ├─ max_grade: 10.0
│  └─ passing_grade: 5.0
│
└─ analysis:
   └─ confidence_threshold: 0.7
```

## 📈 Scalability

```
CURRENT CAPACITY:
┌──────────────────────────────────┐
│ Students:    1-100 (comfortable) │
│ Time/student: ~3-5 seconds       │
│ Total time:   5-8 minutes        │
│ Storage:      ~100KB per student │
└──────────────────────────────────┘

BOTTLENECKS:
┌──────────────────────────────────┐
│ 1. GitHub cloning (network I/O) │
│ 2. Pattern matching (CPU)       │
│ 3. File system operations       │
└──────────────────────────────────┘

OPTIMIZATION PATHS:
┌──────────────────────────────────┐
│ • Parallel processing (10x)     │
│ • Cache cloned repos (2x)       │
│ • Pre-compile patterns (1.5x)   │
│ • Database instead of JSON (5x) │
└──────────────────────────────────┘
```

## 🎨 Component Dependencies

```
grader/main.py
    │
    ├─ imports: analyzer/test_analyzer.py
    ├─ reads:   config.yaml
    ├─ uses:    student_submissions/
    └─ writes:  results/*.json

analyzer/test_analyzer.py
    │
    ├─ reads:   Test.java files
    └─ returns: Analysis dictionaries

scripts/github_cloner.py
    │
    ├─ reads:   student_repos.txt
    ├─ clones:  GitHub repositories
    └─ writes:  student_submissions/

dashboard/index.html
    │
    └─ reads:   results/grading_summary.json
```

## 🚦 Error Handling Flow

```
START
  │
  ├─ Clone repo
  │  ├─ SUCCESS → Continue
  │  └─ FAIL → Log error, skip student
  │
  ├─ Find test file
  │  ├─ FOUND → Continue
  │  └─ NOT FOUND → Log error, grade = 0
  │
  ├─ Parse test file
  │  ├─ SUCCESS → Continue
  │  └─ FAIL → Log error, grade = 0
  │
  ├─ Analyze requirements
  │  ├─ SUCCESS → Calculate grade
  │  └─ FAIL → Log error, grade = 0
  │
  └─ Save results
     ├─ SUCCESS → Display on dashboard
     └─ FAIL → Log error, retry
```

## 💾 File System Layout

```
cruise-control-grader/
│
├─ Configuration
│  ├─ config.yaml
│  └─ student_repos.txt
│
├─ Documentation
│  ├─ README.md
│  ├─ REQUIREMENTS.md
│  ├─ ROADMAP.md
│  ├─ GETTING_STARTED.md
│  └─ QUICK_START.md
│
├─ Code
│  ├─ analyzer/test_analyzer.py
│  ├─ grader/main.py
│  └─ scripts/github_cloner.py
│
├─ Data
│  ├─ student_submissions/ (generated)
│  └─ results/ (generated)
│
└─ Visualization
   └─ dashboard/index.html
```
