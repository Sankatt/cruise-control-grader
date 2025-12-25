# CruiseControl Exam Automated Grading System

Automated testing and grading system for the CruiseControl programming exam.

## 📋 Overview

This system automatically:
- Clones student submissions from GitHub
- Executes their test files
- Analyzes which requirements are covered by their tests
- Generates grading reports and dashboards

## 🏗️ Project Structure

```
.
├── specifications/          # Exam specifications and requirements
├── analyzer/               # Test analysis and requirement mapping
├── grader/                 # Automated grading engine
├── dashboard/              # Results visualization
├── results/                # JSON output files
└── scripts/                # Utility scripts
```

## 📝 Requirements Coverage

Based on the CruiseControl specification, students must test:

### Initialization Requirements
- **R1**: speedSet initialized to null
- **R2**: speedLimit initialized to null

### setSpeedSet() Requirements
- **R3**: speedSet accepts positive values (> 0)
- **R4**: Throws IncorrectSpeedSetException for zero/negative values
- **R5**: speedSet cannot exceed speedLimit (if speedLimit is set)
- **R6**: Throws SpeedSetAboveSpeedLimitException if speedSet > speedLimit

### setSpeedLimit() Requirements
- **R7**: speedLimit accepts positive values (> 0)
- **R8**: Throws IncorrectSpeedLimitException for zero/negative values
- **R9**: Throws CannotSetSpeedLimitException if speedSet already set

### disable() Requirements
- **R10**: Sets speedSet to null
- **R11**: Does not alter speedLimit

### nextCommand() Requirements
- **R12**: Returns IDLE when speedSet not initialized
- **R13**: Returns IDLE when disabled
- **R14**: Returns REDUCE when current speed > speedSet
- **R15**: Returns INCREASE when current speed < speedSet (with road min check)
- **R16**: Returns REDUCE when current speed > speedLimit
- **R17**: Returns REDUCE when current speed > road max
- **R18**: Returns KEEP when current speed == speedSet
- **R19**: Returns INCREASE when current speed < road min

## 🚀 Quick Start

```bash
# Clone this repository
git clone https://github.com/yourusername/cruise-control-grader.git

# Install dependencies
pip install -r requirements.txt

# Run the grading system
python grader/main.py --student-repos student_repos.txt

# View results
python dashboard/serve.py
```

## 📊 Output Format

Results are saved in JSON format in the `results/` directory:

```json
{
  "student_id": "student123",
  "repo_url": "https://github.com/student123/cruise-control",
  "timestamp": "2024-12-25T10:30:00Z",
  "requirements_covered": ["R1", "R2", "R3", "R4"],
  "requirements_missing": ["R5", "R6", "R7", "R8"],
  "coverage_percentage": 50.0,
  "grade": 5.0
}
```

## 🔧 Configuration

Edit `config.yaml` to customize:
- GitHub authentication
- Grading weights
- Requirement priorities
- Output formats

## 📖 Documentation

- [Requirement Mapping Guide](docs/requirement_mapping.md)
- [Test Analyzer Guide](docs/test_analyzer.md)
- [Grading Rubric](docs/grading_rubric.md)

## 🤝 Contributing

This is an educational grading tool. For questions, contact [your email].

## 📄 License

MIT License - See LICENSE file for details
