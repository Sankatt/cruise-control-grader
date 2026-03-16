#!/usr/bin/env python3
"""
Dual Grading System v3 - Pattern-Based + Rigorous Implementation Graders
Now with three-layer test analysis:
  1. TestAnalyzer           - original pattern + holistic (existing)
  2. ImprovedTestAnalyzer   - strict combination rules (new, optional)
  3. MutationTestAnalyzer   - execution-based mutation testing (new, optional)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# --- Existing analyzers (unchanged) ---
from analyzer.test_analyzer import ImprovedTestAnalyzer as TestAnalyzer
from analyzer.execution_grader import PatternBasedGrader
from analyzer.rigorous_implementation_grader import RigorousImplementationGrader

# --- New test analyzers (optional — system works without them) ---
# Try to import the separate improved_test_analyzer if available
try:
    from analyzer.improved_test_analyzer import ImprovedTestAnalyzer as _ImprovedTA
    IMPROVED_AVAILABLE = True
    _ImprovedTestAnalyzerClass = _ImprovedTA
except ImportError:
    try:
        # Maybe it uses a different class name inside
        import importlib as _il
        _mod = _il.import_module('analyzer.improved_test_analyzer')
        _ImprovedTestAnalyzerClass = next(
            (v for k, v in vars(_mod).items()
             if isinstance(v, type) and not k.startswith('_')
             and k not in ('Path', 'Dict', 'List', 'Tuple', 'Set')), None
        )
        IMPROVED_AVAILABLE = _ImprovedTestAnalyzerClass is not None
    except Exception:
        IMPROVED_AVAILABLE = False
        _ImprovedTestAnalyzerClass = None

try:
    from analyzer.mutation_test_analyzer import MutationTestAnalyzer
    MUTATION_AVAILABLE = True
except ImportError:
    MUTATION_AVAILABLE = False


class DualGradingSystem:
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67, 'R2': 1.67, 'R3': 1.67,
        'R4': 1.67, 'R5': 1.67, 'R6': 1.65
    }

    def __init__(self):
        self.results = []

    def find_student_submissions(self, submissions_dir: str):
        submissions_path = Path(submissions_dir)
        if not submissions_path.exists():
            print(f"Error: Submissions directory '{submissions_dir}' not found.")
            return []
        students = []
        for student_dir in submissions_path.iterdir():
            if not student_dir.is_dir():
                continue
            student_id = student_dir.name
            test_file = impl_file = None
            for java_file in student_dir.rglob("*.java"):
                if "Test" in java_file.stem or "test" in java_file.stem.lower():
                    test_file = java_file
                elif "CruiseControl" in java_file.stem and "Test" not in java_file.stem:
                    impl_file = java_file
            if test_file and impl_file:
                students.append((student_id, student_dir, test_file, impl_file))
            else:
                print(f"  WARNING: Skipping {student_id}: Missing files")
        return sorted(students)

    def calculate_grade(self, requirements):
        grade = sum(self.REQUIREMENT_WEIGHTS.get(req, 0) for req in requirements)
        return min(round(grade, 2), 10.0)

    def build_mutation_analysis(self, mutation_result: dict) -> dict:
        """Build a clean mutation_analysis section for the student JSON output."""
        if not mutation_result or not mutation_result.get('success'):
            return {
                "success": False,
                "grade": None,
                "requirements_covered": [],
                "requirements_missing": ["R1", "R2", "R3", "R4", "R5", "R6"],
                "total_tests_run": 0,
                "mutants": {},
                "error": mutation_result.get('error', 'Mutation testing did not run') if mutation_result else 'Mutation testing did not run'
            }

        mutants = {}
        for req, detail in mutation_result.get('requirement_details', {}).items():
            mutants[req] = {
                "status": detail.get("status", "UNKNOWN"),
                "tests_failed": detail.get("mutant_tests_failed", 0),
                "tests_passed": detail.get("mutant_tests_passed", 0),
                "failing_tests": detail.get("failing_tests", []),
                "details": detail.get("details", ""),
            }

        return {
            "success": True,
            "grade": mutation_result.get("grade", 0.0),
            "requirements_covered": mutation_result.get("requirements_covered", []),
            "requirements_missing": mutation_result.get("requirements_missing", []),
            "total_tests_run": mutation_result.get("reference_tests_total", 0),
            "all_test_methods": mutation_result.get("reference_test_methods", []),
            "mutants": mutants,
            "error": None,
        }

    def analyze_tests(self, test_file: Path, student_dir: Path, student_id: str = 'Unknown'):
        """Run all available test analyzers and return a combined result."""
        results = {}

        # 1. Original TestAnalyzer
        try:
            # ImprovedTestAnalyzer: __init__ takes no args, file path goes to analyze()
            ta = TestAnalyzer()
            results['original'] = ta.analyze(str(test_file))
        except Exception as e:
            print(f"    WARNING: Original analyzer error: {e}")
            results['original'] = None

        # 2. ImprovedTestAnalyzer
        if IMPROVED_AVAILABLE and _ImprovedTestAnalyzerClass:
            try:
                ita = _ImprovedTestAnalyzerClass()
                results['improved'] = ita.analyze(str(test_file))
            except Exception as e:
                print(f"    WARNING: Improved analyzer error: {e}")
                results['improved'] = None

        # 3. MutationTestAnalyzer
        if MUTATION_AVAILABLE:
            src_dir = None
            for root, dirs, files in os.walk(student_dir):
                if "CruiseControl.java" in files and "Test" not in root:
                    src_dir = root
                    break
            try:
                mta = MutationTestAnalyzer()
                results['mutation'] = mta.analyze(str(test_file), src_dir)
                mut = results['mutation']
                if mut.get('success'):
                    print(f"    Mutation: {mut.get('requirements_covered', [])}  "
                          f"grade={mut.get('grade', 0):.2f}")
                else:
                    print(f"    Mutation FAILED: {mut.get('error', 'unknown')[:100]}")
            except Exception as e:
                print(f"    WARNING: Mutation analyzer error: {e}")
                results['mutation'] = None

        # Combine results
        covered_sets = []
        orig = results.get('original')
        if orig and orig.get('success'):
            covered_sets.append(set(orig.get('requirements_covered', [])))
        improved = results.get('improved')
        if improved and improved.get('success'):
            covered_sets.append(set(improved.get('requirements_covered', [])))

        mut = results.get('mutation')
        mutation_ran = mut and mut.get('success')

        if mutation_ran:
            mutation_covered = set(mut.get('requirements_covered', []))
            both_static = set.intersection(*covered_sets) if len(covered_sets) >= 2 else (covered_sets[0] if covered_sets else set())
            final_covered = sorted(mutation_covered | both_static)
        elif covered_sets:
            final_covered = sorted(set.union(*covered_sets))
        else:
            final_covered = []

        grade = self.calculate_grade(final_covered)

        return {
            'success': True,
            'grade': grade,
            'requirements_covered': final_covered,
            'requirements_missing': [r for r in ['R1','R2','R3','R4','R5','R6'] if r not in final_covered],
            'requirements_found': len(final_covered),
            'coverage_percentage': round(len(final_covered) / 6 * 100, 2),
            'requirement_details': (orig or {}).get('requirement_details', {}),
            'original_result': orig,
            'improved_result': improved,
            'mutation_result': mut,
            'mutation_available': mutation_ran,
        }

    def grade_student(self, student_id, student_dir, test_file, impl_file):
        print(f"\nGrading {student_id}...")
        timestamp = datetime.now().strftime('%Y%m%d')

        # Test analysis
        print(f"\n  Running test analysis (all layers)...")
        test_result = self.analyze_tests(test_file, student_dir, student_id)
        test_grade = test_result['grade']

        orig = test_result.get('original_result') or {}
        print(f"    Original:  {orig.get('requirements_covered', [])}  "
              f"grade={self.calculate_grade(orig.get('requirements_covered', [])):.2f}")
        if IMPROVED_AVAILABLE:
            imp = test_result.get('improved_result') or {}
            print(f"    Improved:  {imp.get('requirements_covered', [])}  "
                  f"grade={self.calculate_grade(imp.get('requirements_covered', [])):.2f}")
        print(f"    COMBINED:  {test_result['requirements_covered']}  grade={test_grade:.2f}")

        # Pattern implementation
        pattern_result = None
        pattern_grade = 0
        try:
            print(f"\n  Running PATTERN-BASED grader...")
            pattern_grader = PatternBasedGrader(student_dir)
            pattern_result = pattern_grader.grade_implementation(impl_file, student_id)
            if pattern_result['success']:
                pattern_grade = self.calculate_grade(pattern_result.get('requirements_satisfied', []))
                print(f"    Pattern: {pattern_result['requirements_found']}/6  grade={pattern_grade:.2f}")
        except Exception as e:
            print(f"    ERROR: {e}")

        # Rigorous implementation
        rigorous_result = None
        rigorous_grade = 0
        try:
            print(f"\n  Running RIGOROUS grader...")
            rigorous_grader = RigorousImplementationGrader(student_dir)
            rigorous_result = rigorous_grader.grade_implementation(impl_file)
            if rigorous_result['success']:
                rigorous_grade = self.calculate_grade(rigorous_result.get('requirements_satisfied', []))
                print(f"    Rigorous: {rigorous_result['requirements_found']}/6  grade={rigorous_grade:.2f}  "
                      f"({rigorous_result.get('total_test_cases', 0)} test cases)")
        except Exception as e:
            print(f"    ERROR: {e}")

        pattern_combined  = round((test_grade + pattern_grade)  / 2, 2)
        rigorous_combined = round((test_grade + rigorous_grade) / 2, 2)

        if pattern_grade and rigorous_grade:
            print(f"\n  COMPARISON:")
            print(f"    Test Coverage: {test_grade}/10.0")
            print(f"    Pattern Impl:  {pattern_grade}/10.0")
            print(f"    Rigorous Impl: {rigorous_grade}/10.0")
            print(f"    Difference:    {abs(pattern_grade - rigorous_grade):.2f}")

        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)

        if pattern_result:
            pattern_data = {
                "student_id": student_id,
                "grader_type": "Pattern-Based Execution Grader",
                "timestamp": datetime.now().isoformat(),
                "test_coverage": {
                    "grade": test_grade,
                    "requirements_covered": test_result.get('requirements_covered', []),
                    "requirements_missing": test_result.get('requirements_missing', []),
                    "coverage_percentage": test_result.get('coverage_percentage', 0),
                    "requirement_details": test_result.get('requirement_details', {}),
                    "original_covered": (test_result.get('original_result') or {}).get('requirements_covered', []),
                    "improved_covered": (test_result.get('improved_result') or {}).get('requirements_covered', []),
                    "mutation_covered": (test_result.get('mutation_result') or {}).get('requirements_covered', []),
                    "mutation_available": test_result.get('mutation_available', False),
                },
                "mutation_analysis": self.build_mutation_analysis(test_result.get('mutation_result')),
                "implementation": pattern_result,
                "implementation_grade": pattern_grade,
                "combined_grade": pattern_combined
            }
            with open(results_dir / f"{student_id}_pattern_{timestamp}.json", 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, indent=2, ensure_ascii=False)
            print(f"\n  Saved: {student_id}_pattern_{timestamp}.json")

        if rigorous_result:
            req_descriptions = {
                'R1': 'speedSet initializes to null', 'R2': 'speedLimit initializes to null',
                'R3': 'setSpeedSet accepts positive values',
                'R4': 'Throws IncorrectSpeedSetException for zero/negative',
                'R5': 'speedSet respects speedLimit',
                'R6': 'Throws SpeedSetAboveSpeedLimitException when exceeding'
            }
            requirement_details = {}
            for req in ['R1','R2','R3','R4','R5','R6']:
                ra = rigorous_result.get('requirement_analysis', {}).get(req, {})
                satisfied = req in rigorous_result.get('requirements_satisfied', [])
                requirement_details[req] = {
                    "requirement": req,
                    "description": req_descriptions.get(req, ''),
                    "status": "SATISFIED" if satisfied else "NOT SATISFIED",
                    "satisfied": satisfied,
                    "tests_run": ra.get('total_tests', 0),
                    "tests_passed": ra.get('passed_tests', 0),
                    "tests_failed": ra.get('failed_tests', 0),
                    "pass_rate": f"{ra.get('satisfaction_rate', 0)}%",
                    "threshold": "80% required",
                    "failure_details": ra.get('failure_details', []),
                }

            rigorous_data = {
                "student_id": student_id,
                "grader_type": "Rigorous Property-Based Grader",
                "timestamp": datetime.now().isoformat(),
                "test_coverage": {
                    "grade": test_grade,
                    "requirements_covered": test_result.get('requirements_covered', []),
                    "requirements_missing": test_result.get('requirements_missing', []),
                    "coverage_percentage": test_result.get('coverage_percentage', 0),
                    "requirement_details": test_result.get('requirement_details', {}),
                    "mutation_covered": (test_result.get('mutation_result') or {}).get('requirements_covered', []),
                    "mutation_available": test_result.get('mutation_available', False),
                },
                "mutation_analysis": self.build_mutation_analysis(test_result.get('mutation_result')),
                "implementation": {
                    "overall_result": {
                        "grade": rigorous_grade,
                        "requirements_satisfied": rigorous_result.get('requirements_satisfied', []),
                        "requirements_missing": rigorous_result.get('requirements_missing', []),
                        "total_test_cases_run": rigorous_result.get('total_test_cases', 0),
                        "satisfaction_percentage": rigorous_result.get('satisfaction_percentage', 0)
                    },
                    "detailed_requirements": requirement_details,
                    "testing_methodology": {
                        "name": "Rigorous Property-Based Testing",
                        "test_cases": rigorous_result.get('total_test_cases', 23),
                        "techniques_used": [
                            "Equivalence Partitioning", "Boundary Value Analysis",
                            "Property-Based Testing", "State Verification"
                        ],
                        "properties_verified": rigorous_result.get('properties_verified', [])
                    },
                    "raw_data": rigorous_result
                },
                "implementation_grade": rigorous_grade,
                "combined_grade": rigorous_combined
            }
            with open(results_dir / f"{student_id}_rigorous_{timestamp}.json", 'w', encoding='utf-8') as f:
                json.dump(rigorous_data, f, indent=2, ensure_ascii=False)
            print(f"  Saved: {student_id}_rigorous_{timestamp}.json")

    def grade_all(self, submissions_dir):
        students = self.find_student_submissions(submissions_dir)
        if not students:
            print("No student submissions found.")
            return

        print(f"\n{'='*70}")
        print(f"Found {len(students)} student submission(s)")
        print(f"  ImprovedTestAnalyzer: {'available' if IMPROVED_AVAILABLE else 'not found'}")
        print(f"  MutationTestAnalyzer: {'available' if MUTATION_AVAILABLE else 'not found'}")
        print(f"{'='*70}")

        for student_id, student_dir, test_file, impl_file in students:
            self.grade_student(student_id, student_dir, test_file, impl_file)

        print(f"\n{'='*70}")
        print("Grading complete!")
        print(f"{'='*70}")
        self.generate_dashboard_summary()

    def generate_dashboard_summary(self):
        results_dir = Path(__file__).parent / "results"
        if not results_dir.exists():
            return

        pattern_files  = list(results_dir.glob("*_pattern_*.json"))
        rigorous_files = list(results_dir.glob("*_rigorous_*.json"))

        student_names = set()
        for f in pattern_files:
            student_names.add(f.stem.split('_pattern_')[0])

        students = []
        for student_name in sorted(student_names):
            pf = next((f for f in pattern_files  if f.stem.startswith(student_name + '_pattern_')),  None)
            rf = next((f for f in rigorous_files if f.stem.startswith(student_name + '_rigorous_')), None)

            sd = {
                'success': True, 'student_id': student_name,
                'test_coverage_grade': 0,
                'test_analysis': {'coverage_percentage': 0, 'requirements_found': 0, 'requirements_covered': []},
                'implementation_grade': 0,
                'implementation_analysis': {'satisfaction_percentage': 0, 'requirements_satisfied': []},
                'combined_grade': 0, 'pattern': None, 'rigorous': None
            }

            if pf:
                with open(pf, 'r', encoding='utf-8') as f:
                    pd = json.load(f)
                sd['test_coverage_grade'] = pd.get('test_coverage', {}).get('grade', 0)
                sd['test_analysis'] = {
                    'coverage_percentage': pd.get('test_coverage', {}).get('coverage_percentage', 0),
                    'requirements_found':  len(pd.get('test_coverage', {}).get('requirements_covered', [])),
                    'requirements_covered': pd.get('test_coverage', {}).get('requirements_covered', [])
                }
                sd['implementation_grade']    = pd.get('implementation_grade', 0)
                sd['implementation_analysis'] = {
                    'satisfaction_percentage': pd.get('implementation', {}).get('satisfaction_percentage', 0),
                    'requirements_satisfied':  pd.get('implementation', {}).get('requirements_satisfied', [])
                }
                sd['combined_grade'] = pd.get('combined_grade', 0)
                sd['pattern'] = {
                    'test_grade': pd.get('test_coverage', {}).get('grade', 0),
                    'implementation_grade': pd.get('implementation_grade', 0),
                    'combined_grade': pd.get('combined_grade', 0),
                    'requirements_covered': pd.get('test_coverage', {}).get('requirements_covered', []),
                    'requirements_satisfied': pd.get('implementation', {}).get('requirements_satisfied', []),
                    'test_details': pd.get('test_coverage', {}).get('requirement_details', {}),
                    'impl_details': pd.get('implementation', {}).get('requirement_details', {}),
                    'test_original_covered': pd.get('test_coverage', {}).get('original_covered', []),
                    'test_improved_covered': pd.get('test_coverage', {}).get('improved_covered', []),
                    'test_mutation_covered': pd.get('test_coverage', {}).get('mutation_covered', []),
                    'mutation_available':    pd.get('test_coverage', {}).get('mutation_available', False),
                }

            if rf:
                with open(rf, 'r', encoding='utf-8') as f:
                    rd = json.load(f)
                sd['rigorous'] = {
                    'test_grade': rd.get('test_coverage', {}).get('grade', 0),
                    'implementation_grade': rd.get('implementation_grade', 0),
                    'combined_grade': rd.get('combined_grade', 0),
                    'requirements_covered': rd.get('test_coverage', {}).get('requirements_covered', []),
                    'requirements_satisfied': rd.get('implementation', {}).get('overall_result', {}).get('requirements_satisfied', []),
                    'test_details': rd.get('test_coverage', {}).get('requirement_details', {}),
                    'impl_details': rd.get('implementation', {}).get('detailed_requirements', {}),
                    'test_mutation_covered': rd.get('test_coverage', {}).get('mutation_covered', []),
                    'mutation_available': rd.get('test_coverage', {}).get('mutation_available', False),
                }

            students.append(sd)

        summary = {
            'generated': datetime.now().isoformat(),
            'total_students': len(students),
            'results': students,
            'statistics': self.calculate_statistics(students)
        }

        output_file = results_dir / 'grading_summary.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Dashboard summary: {output_file}")

    def calculate_statistics(self, students):
        stats = {}
        for key in ('pattern', 'rigorous'):
            grp = [s for s in students if s.get(key)]
            if not grp:
                stats[key] = {}
                continue
            stats[key] = {
                'avg_test_grade':     round(sum(s[key]['test_grade']           for s in grp) / len(grp), 2),
                'avg_impl_grade':     round(sum(s[key]['implementation_grade'] for s in grp) / len(grp), 2),
                'avg_combined_grade': round(sum(s[key]['combined_grade']       for s in grp) / len(grp), 2),
            }
            for req in ['R1','R2','R3','R4','R5','R6']:
                stats[key][f'total_{req.lower()}'] = sum(
                    1 for s in grp if req in s[key]['requirements_satisfied']
                )
        return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python main_dual.py <submissions_directory>")
        sys.exit(1)
    print("=" * 70)
    print("DUAL GRADING SYSTEM v3")
    print("=" * 70)
    DualGradingSystem().grade_all(sys.argv[1])


if __name__ == '__main__':
    main()
