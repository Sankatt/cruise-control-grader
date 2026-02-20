#!/usr/bin/env python3
"""
Dual Grading System - Runs BOTH Pattern-Based and Rigorous Implementation Graders
This is the WORKING VERSION from January 14, 2026
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.test_analyzer import TestAnalyzer
from analyzer.execution_grader import PatternBasedGrader  # Updated to use new pattern-based grader
from analyzer.rigorous_implementation_grader import RigorousImplementationGrader


class DualGradingSystem:
    """Runs both pattern-based and rigorous implementation graders"""
    
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67,
        'R2': 1.67,
        'R3': 1.67,
        'R4': 1.67,
        'R5': 1.67,
        'R6': 1.65
    }
    
    def __init__(self):
        self.results = []
    
    def find_student_submissions(self, submissions_dir: str):
        """Find all student submissions"""
        submissions_path = Path(submissions_dir)
        
        if not submissions_path.exists():
            print(f"Error: Submissions directory '{submissions_dir}' not found.")
            return []
        
        students = []
        
        for student_dir in submissions_path.iterdir():
            if not student_dir.is_dir():
                continue
            
            student_id = student_dir.name
            
            test_file = None
            impl_file = None
            
            for java_file in student_dir.rglob("*.java"):
                if "Test" in java_file.stem or "test" in java_file.stem.lower():
                    test_file = java_file
                elif "CruiseControl" in java_file.stem and "Test" not in java_file.stem:
                    impl_file = java_file
            
            if test_file and impl_file:
                students.append((student_id, student_dir, test_file, impl_file))
            else:
                print(f"  ⚠ Skipping {student_id}: Missing files")
        
        return sorted(students)
    
    def calculate_grade(self, requirements):
        """Calculate grade from requirements"""
        grade = sum(self.REQUIREMENT_WEIGHTS.get(req, 0) for req in requirements)
        return min(round(grade, 2), 10.0)
    
    def grade_student(self, student_id, student_dir, test_file, impl_file):
        """Grade a single student"""
        print(f"\nGrading {student_id}...")
        
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Test coverage analysis
        test_result = None
        test_grade = 0
        try:
            test_analyzer = TestAnalyzer(str(test_file))
            test_result = test_analyzer.analyze()
            if test_result['success']:
                test_grade = self.calculate_grade(test_result.get('requirements_covered', []))
                print(f"  Test Coverage: {test_result['requirements_found']}/6 ({test_result['coverage_percentage']}%)")
                print(f"  Test Grade: {test_grade}/10.0")
        except Exception as e:
            print(f"  ✗ Test analysis error: {e}")
        
        # Pattern-based implementation
        pattern_result = None
        pattern_grade = 0
        try:
            print(f"\n  Running PATTERN-BASED grader...")
            pattern_grader = PatternBasedGrader(student_dir)
            pattern_result = pattern_grader.grade_implementation(impl_file, student_id)
            if pattern_result['success']:
                pattern_grade = self.calculate_grade(pattern_result.get('requirements_satisfied', []))
                print(f"    Pattern: {pattern_result['requirements_found']}/6")
                print(f"    Pattern Grade: {pattern_grade}/10.0")
                
                # Show pattern matching details if available
                if pattern_result.get('pattern_matching_used'):
                    print(f"    Pattern Matching: Active (YAML-based)")
        except Exception as e:
            print(f"    ✗ Pattern error: {e}")
        
        # Rigorous implementation
        rigorous_result = None
        rigorous_grade = 0
        try:
            print(f"\n  Running RIGOROUS grader...")
            rigorous_grader = RigorousImplementationGrader(student_dir)
            rigorous_result = rigorous_grader.grade_implementation(impl_file)
            if rigorous_result['success']:
                rigorous_grade = self.calculate_grade(rigorous_result.get('requirements_satisfied', []))
                print(f"    Rigorous: {rigorous_result['requirements_found']}/6")
                print(f"    Rigorous Grade: {rigorous_grade}/10.0")
                print(f"    Test Cases Run: {rigorous_result.get('total_test_cases', 0)}")
        except Exception as e:
            print(f"    ✗ Rigorous error: {e}")
        
        # Calculate combined grades
        pattern_combined = round((test_grade + pattern_grade) / 2, 2) if test_result and pattern_result else 0
        rigorous_combined = round((test_grade + rigorous_grade) / 2, 2) if test_result and rigorous_result else 0
        
        if pattern_grade and rigorous_grade:
            diff = abs(pattern_grade - rigorous_grade)
            print(f"\n  📊 COMPARISON:")
            print(f"    Pattern Impl:  {pattern_grade}/10.0")
            print(f"    Rigorous Impl: {rigorous_grade}/10.0")
            print(f"    Difference:    {diff:.2f}")
        
        # Save pattern JSON
        if pattern_result:
            pattern_data = {
                "student_id": student_id,
                "grader_type": "Pattern-Based Execution Grader",
                "timestamp": datetime.now().isoformat(),
                "test_coverage": {
                    "grade": test_grade,
                    "requirements_covered": test_result.get('requirements_covered', []) if test_result else [],
                    "requirements_missing": test_result.get('requirements_missing', []) if test_result else [],
                    "coverage_percentage": test_result.get('coverage_percentage', 0) if test_result else 0,
                    "requirement_details": test_result.get('requirement_details', {}) if test_result else {}
                },
                "implementation": pattern_result,
                "implementation_grade": pattern_grade,
                "combined_grade": pattern_combined
            }
            
            pattern_file = Path("results") / f"{student_id}_pattern_{timestamp}.json"
            pattern_file.parent.mkdir(exist_ok=True)
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            print(f"\n  ✓ Saved: {pattern_file.name}")
        
        # Save rigorous JSON
        if rigorous_result:
            # Build detailed requirement explanations
            requirement_details = {}
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                req_analysis = rigorous_result.get('requirement_analysis', {}).get(req, {})
                
                # Get basic info
                satisfied = req in rigorous_result.get('requirements_satisfied', [])
                total_tests = req_analysis.get('total_tests', 0)
                passed_tests = req_analysis.get('passed_tests', 0)
                failed_tests = req_analysis.get('failed_tests', 0)
                satisfaction_rate = req_analysis.get('satisfaction_rate', 0)
                
                # Build explanation
                detail = {
                    "requirement": req,
                    "description": req_analysis.get('description', ''),
                    "status": "✓ SATISFIED" if satisfied else "✗ NOT SATISFIED",
                    "satisfied": satisfied,
                    "tests_run": total_tests,
                    "tests_passed": passed_tests,
                    "tests_failed": failed_tests,
                    "pass_rate": f"{satisfaction_rate}%",
                    "threshold": "80% required",
                    "result": "",
                    "what_was_checked": [],
                    "what_passed": [],
                    "what_failed": [],
                    "explanation": ""
                }
                
                # Add what was checked (categories)
                categories = req_analysis.get('categories_tested', [])
                if 'equivalence_partition' in categories:
                    detail["what_was_checked"].append("Different types of input values (valid/invalid partitions)")
                if 'boundary_value' in categories:
                    detail["what_was_checked"].append("Edge cases at boundaries (e.g., zero, limit±1)")
                if 'property_based' in categories:
                    detail["what_was_checked"].append("Mathematical properties that must always hold")
                if 'state_transition' in categories:
                    detail["what_was_checked"].append("State consistency after operations")
                
                # Add specific results based on requirement
                if req == 'R1':
                    detail["result"] = "Checked that speedSet initializes to null in constructor"
                    if satisfied:
                        detail["what_passed"].append("Constructor correctly sets speedSet = null")
                    else:
                        detail["what_failed"].append("speedSet is not null after construction")
                
                elif req == 'R2':
                    detail["result"] = "Checked that speedLimit initializes to null in constructor"
                    if satisfied:
                        detail["what_passed"].append("Constructor correctly sets speedLimit = null")
                    else:
                        detail["what_failed"].append("speedLimit is not null after construction")
                
                elif req == 'R3':
                    detail["result"] = f"Tested {total_tests} positive values (1, 50, 100, 1000)"
                    if satisfied:
                        detail["what_passed"].append(f"All {passed_tests} positive values were accepted correctly")
                    else:
                        detail["what_failed"].append(f"{failed_tests} positive value(s) were rejected or caused errors")
                
                elif req == 'R4':
                    detail["result"] = f"Tested {total_tests} invalid values including negatives and zero"
                    
                    # Check specific failures
                    failure_details = req_analysis.get('failure_details', [])
                    zero_failed = any('0000' in f.get('test_id', '') for f in failure_details)
                    
                    if satisfied:
                        if failed_tests > 0:
                            detail["what_passed"].append(f"{passed_tests}/{total_tests} tests passed (≥80% threshold met)")
                            for failure in failure_details:
                                if 'NO_EXCEPTION' in failure.get('reason', ''):
                                    detail["what_failed"].append(f"Test {failure['test_id']}: Did not throw exception")
                        else:
                            detail["what_passed"].append("All negative and zero values correctly throw IncorrectSpeedSetException")
                    else:
                        detail["what_failed"].append(f"Only {passed_tests}/{total_tests} tests passed (below 80% threshold)")
                        if zero_failed:
                            detail["what_failed"].append("⚠️ CRITICAL: Zero (0) does not throw exception - likely using < instead of <=")
                        for failure in failure_details:
                            if 'NO_EXCEPTION' in failure.get('reason', ''):
                                test_id = failure.get('test_id', '')
                                if '0000' in test_id:
                                    detail["what_failed"].append("Test with value 0: Expected exception but none was thrown")
                                elif '0001' in test_id:
                                    detail["what_failed"].append("Test with value -1: Expected exception but none was thrown")
                                else:
                                    detail["what_failed"].append(f"{test_id}: Expected exception but none was thrown")
                    
                    # Add explanation
                    if not satisfied and zero_failed:
                        detail["explanation"] = "Common bug: Code uses 'if (speedSet < 0)' instead of 'if (speedSet <= 0)', missing the zero case"
                
                elif req == 'R5':
                    detail["result"] = f"Tested {total_tests} scenarios with speedLimit set"
                    if satisfied:
                        detail["what_passed"].append("speedSet correctly stays below or equal to speedLimit")
                        detail["what_passed"].append("Boundary case (speedSet = speedLimit) handled correctly")
                    else:
                        detail["what_failed"].append(f"Only {passed_tests}/{total_tests} tests passed")
                        for failure in failure_details:
                            detail["what_failed"].append(f"Failed: {failure.get('reason', 'Unknown')}")
                
                elif req == 'R6':
                    detail["result"] = f"Tested {total_tests} scenarios exceeding speedLimit"
                    if satisfied:
                        detail["what_passed"].append("Correctly throws SpeedSetAboveSpeedLimitException when speedSet > speedLimit")
                        detail["what_passed"].append("Boundary test passed (limit + 1)")
                    else:
                        detail["what_failed"].append(f"Only {passed_tests}/{total_tests} tests passed")
                        for failure in failure_details:
                            if 'NO_EXCEPTION' in failure.get('reason', ''):
                                detail["what_failed"].append("Expected exception when exceeding limit but none was thrown")
                
                # Add overall explanation if not satisfied
                if not satisfied and not detail["explanation"]:
                    if satisfaction_rate < 80:
                        detail["explanation"] = f"Pass rate {satisfaction_rate}% is below the 80% threshold needed to satisfy this requirement"
                
                requirement_details[req] = detail
            
            rigorous_data = {
                "student_id": student_id,
                "grader_type": "Rigorous Property-Based Grader",
                "timestamp": datetime.now().isoformat(),
                "test_coverage": {
                    "grade": test_grade,
                    "requirements_covered": test_result.get('requirements_covered', []) if test_result else [],
                    "requirements_missing": test_result.get('requirements_missing', []) if test_result else [],
                    "coverage_percentage": test_result.get('coverage_percentage', 0) if test_result else 0,
                    "requirement_details": test_result.get('requirement_details', {}) if test_result else {}
                },
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
                            "Equivalence Partitioning - Tests different classes of inputs",
                            "Boundary Value Analysis - Tests edge cases like 0, -1, limit±1",
                            "Property-Based Testing - Verifies mathematical invariants",
                            "State Verification - Ensures object state consistency"
                        ],
                        "properties_verified": rigorous_result.get('properties_verified', [])
                    },
                    "raw_data": rigorous_result
                },
                "implementation_grade": rigorous_grade,
                "combined_grade": rigorous_combined
            }
            
            rigorous_file = Path("results") / f"{student_id}_rigorous_{timestamp}.json"
            with open(rigorous_file, 'w') as f:
                json.dump(rigorous_data, f, indent=2)
            print(f"  ✓ Saved: {rigorous_file.name}")
    
    def grade_all(self, submissions_dir):
        """Grade all students"""
        students = self.find_student_submissions(submissions_dir)
        
        if not students:
            print("No student submissions found.")
            return
        
        print(f"\n{'=' * 70}")
        print(f"Found {len(students)} student submissions")
        print(f"{'=' * 70}")
        
        for student_id, student_dir, test_file, impl_file in students:
            self.grade_student(student_id, student_dir, test_file, impl_file)
        
        print(f"\n{'=' * 70}")
        print("✓ Grading complete!")
        print(f"{'=' * 70}")
        
        # Generate dashboard summary automatically
        print("\nGenerating dashboard summary...")
        self.generate_dashboard_summary()
    
    def generate_dashboard_summary(self):
        """Generate grading_summary.json for the HTML dashboard"""
        results_dir = Path("results")
        
        if not results_dir.exists():
            print("Error: results/ directory not found")
            return
        
        # Find all JSON files
        pattern_files = list(results_dir.glob("*_pattern_*.json"))
        rigorous_files = list(results_dir.glob("*_rigorous_*.json"))
        
        students = []
        
        # Get unique student names
        student_names = set()
        for f in pattern_files:
            name = f.stem.split('_pattern_')[0]
            student_names.add(name)
        
        # Process each student
        for student_name in sorted(student_names):
            pattern_file = None
            rigorous_file = None
            
            for f in pattern_files:
                if f.stem.startswith(student_name + '_pattern_'):
                    pattern_file = f
                    break
            
            for f in rigorous_files:
                if f.stem.startswith(student_name + '_rigorous_'):
                    rigorous_file = f
                    break
            
            if not pattern_file and not rigorous_file:
                continue
            
            student_data = {
                'success': True,
                'student_id': student_name,
                'test_coverage_grade': 0,
                'test_analysis': {
                    'coverage_percentage': 0,
                    'requirements_found': 0,
                    'requirements_covered': []
                },
                'implementation_grade': 0,
                'implementation_analysis': {
                    'satisfaction_percentage': 0,
                    'requirements_satisfied': []
                },
                'combined_grade': 0,
                'pattern': None,
                'rigorous': None
            }
            
            # Load pattern data
            if pattern_file:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    pattern_data = json.load(f)
                    
                    # Map to HTML expected structure
                    student_data['test_coverage_grade'] = pattern_data.get('test_coverage', {}).get('grade', 0)
                    student_data['test_analysis'] = {
                        'coverage_percentage': pattern_data.get('test_coverage', {}).get('coverage_percentage', 0),
                        'requirements_found': len(pattern_data.get('test_coverage', {}).get('requirements_covered', [])),
                        'requirements_covered': pattern_data.get('test_coverage', {}).get('requirements_covered', [])
                    }
                    student_data['implementation_grade'] = pattern_data.get('implementation_grade', 0)
                    student_data['implementation_analysis'] = {
                        'satisfaction_percentage': pattern_data.get('implementation', {}).get('satisfaction_percentage', 0),
                        'requirements_satisfied': pattern_data.get('implementation', {}).get('requirements_satisfied', [])
                    }
                    student_data['combined_grade'] = pattern_data.get('combined_grade', 0)
                    
                    # Keep full data for reference
                    student_data['pattern'] = {
                        'test_grade': pattern_data.get('test_coverage', {}).get('grade', 0),
                        'implementation_grade': pattern_data.get('implementation_grade', 0),
                        'combined_grade': pattern_data.get('combined_grade', 0),
                        'requirements_covered': pattern_data.get('test_coverage', {}).get('requirements_covered', []),
                        'requirements_satisfied': pattern_data.get('implementation', {}).get('requirements_satisfied', []),
                        'test_details': pattern_data.get('test_coverage', {}).get('requirement_details', {}),
                        'impl_details': pattern_data.get('implementation', {}).get('requirement_details', {})
                    }
            
            # Load rigorous data
            if rigorous_file:
                with open(rigorous_file, 'r', encoding='utf-8') as f:
                    rigorous_data = json.load(f)
                    student_data['rigorous'] = {
                        'test_grade': rigorous_data.get('test_coverage', {}).get('grade', 0),
                        'implementation_grade': rigorous_data.get('implementation_grade', 0),
                        'combined_grade': rigorous_data.get('combined_grade', 0),
                        'requirements_covered': rigorous_data.get('test_coverage', {}).get('requirements_covered', []),
                        'requirements_satisfied': rigorous_data.get('implementation', {}).get('overall_result', {}).get('requirements_satisfied', []),
                        'test_details': rigorous_data.get('test_coverage', {}).get('requirement_details', {}),
                        'impl_details': rigorous_data.get('implementation', {}).get('detailed_requirements', {})
                    }
            
            students.append(student_data)
        
        # Calculate statistics
        statistics = self.calculate_statistics(students)
        
        # Create summary with correct structure for dashboard
        summary = {
            'generated': datetime.now().isoformat(),
            'total_students': len(students),
            'results': students,  # HTML expects 'results' not 'students'
            'statistics': statistics
        }
        
        # Save summary
        output_file = results_dir / 'grading_summary.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Dashboard summary generated: {output_file}")
        print(f"✓ Open index_dual.html in your browser to view results")
    
    def calculate_statistics(self, students):
        """Calculate aggregate statistics"""
        stats = {
            'pattern': {
                'avg_test_grade': 0,
                'avg_impl_grade': 0,
                'avg_combined_grade': 0,
                'total_r1': 0,
                'total_r2': 0,
                'total_r3': 0,
                'total_r4': 0,
                'total_r5': 0,
                'total_r6': 0
            },
            'rigorous': {
                'avg_test_grade': 0,
                'avg_impl_grade': 0,
                'avg_combined_grade': 0,
                'total_r1': 0,
                'total_r2': 0,
                'total_r3': 0,
                'total_r4': 0,
                'total_r5': 0,
                'total_r6': 0
            }
        }
        
        if not students:
            return stats
        
        # Pattern stats
        pattern_students = [s for s in students if s.get('pattern')]
        if pattern_students:
            stats['pattern']['avg_test_grade'] = round(
                sum(s['pattern']['test_grade'] for s in pattern_students) / len(pattern_students), 2
            )
            stats['pattern']['avg_impl_grade'] = round(
                sum(s['pattern']['implementation_grade'] for s in pattern_students) / len(pattern_students), 2
            )
            stats['pattern']['avg_combined_grade'] = round(
                sum(s['pattern']['combined_grade'] for s in pattern_students) / len(pattern_students), 2
            )
            
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                stats['pattern'][f'total_{req.lower()}'] = sum(
                    1 for s in pattern_students 
                    if req in s['pattern']['requirements_satisfied']
                )
        
        # Rigorous stats
        rigorous_students = [s for s in students if s.get('rigorous')]
        if rigorous_students:
            stats['rigorous']['avg_test_grade'] = round(
                sum(s['rigorous']['test_grade'] for s in rigorous_students) / len(rigorous_students), 2
            )
            stats['rigorous']['avg_impl_grade'] = round(
                sum(s['rigorous']['implementation_grade'] for s in rigorous_students) / len(rigorous_students), 2
            )
            stats['rigorous']['avg_combined_grade'] = round(
                sum(s['rigorous']['combined_grade'] for s in rigorous_students) / len(rigorous_students), 2
            )
            
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                stats['rigorous'][f'total_{req.lower()}'] = sum(
                    1 for s in rigorous_students 
                    if req in s['rigorous']['requirements_satisfied']
                )
        
        return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python main_dual.py <submissions_directory>")
        print("\nExample:")
        print("  python main_dual.py ../student_submissions")
        sys.exit(1)
    
    submissions_dir = sys.argv[1]
    
    print("=" * 70)
    print("DUAL GRADING SYSTEM")
    print("Pattern-Based vs Rigorous Implementation Graders")
    print("=" * 70)
    
    grader = DualGradingSystem()
    grader.grade_all(submissions_dir)


if __name__ == '__main__':
    main()
