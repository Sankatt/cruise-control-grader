#!/usr/bin/env python3
"""
Main Grading System
Orchestrates cloning, testing, analysis, and report generation
Now includes both TEST COVERAGE and IMPLEMENTATION QUALITY grading
Implementation grading uses actual code execution for maximum accuracy
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.test_analyzer import TestAnalyzer
from analyzer.execution_grader import ExecutionBasedGrader


class GradingSystem:
    """Main grading system orchestrator"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.results = []
        
    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> dict:
        """Return default configuration"""
        return {
            'grading': {
                'max_grade': 10.0,
                'requirement_weights': {f'R{i}': 5.26 for i in range(1, 20)}
            },
            'output': {
                'results_directory': './results',
                'summary_file': 'grading_summary.json'
            }
        }
    
    def find_test_file(self, student_dir: Path) -> Path:
        """Find the test file in student directory"""
        # Common test file locations - expanded to handle different structures
        search_paths = [
            student_dir,
            student_dir / 'src' / 'test' / 'java',
            student_dir / 'src' / 'test',
            student_dir / 'test' / 'java',  # Without src/ prefix
            student_dir / 'test',
        ]
        
        # Debug: Print what we're searching
        print(f"    Searching for test file in: {student_dir}")
        
        for search_path in search_paths:
            # Try to handle special characters by converting to string
            try:
                if not search_path.exists():
                    continue
                
                print(f"    Checking path: {search_path}")
                
                # Look specifically for CruiseControlTest.java (case-insensitive)
                for test_file in search_path.rglob('*.java'):
                    if test_file.is_file():
                        filename_lower = test_file.name.lower()
                        if 'cruisecontroltest' in filename_lower.replace('_', '').replace('-', ''):
                            print(f"    Found test file: {test_file}")
                            return test_file
                
            except Exception as e:
                print(f"    Error accessing {search_path}: {e}")
                continue
        
        print(f"    No test file found after checking all paths")
        return None
    
    def find_implementation_file(self, student_dir: Path) -> Path:
        """Find the CruiseControl.java implementation file"""
        # Common implementation locations - expanded
        search_paths = [
            student_dir,
            student_dir / 'src' / 'main' / 'java',
            student_dir / 'src',
            student_dir / 'main' / 'java',  # Without src/ prefix
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            # Look for CruiseControl.java
            for impl_file in search_path.rglob('CruiseControl.java'):
                # Make sure it's not a test file
                if 'Test' not in impl_file.name:
                    return impl_file
        
        return None
    
    def calculate_grade(self, analysis: Dict) -> float:
        """Calculate grade based on requirement coverage or satisfaction"""
        if not analysis.get('success'):
            return 0.0
        
        weights = self.config['grading']['requirement_weights']
        max_grade = self.config['grading']['max_grade']
        
        # Calculate weighted score
        total_weight = sum(weights.values())
        earned_weight = 0.0
        
        # Handle both test analysis (requirements_covered) and implementation analysis (requirements_satisfied)
        requirements = analysis.get('requirements_covered', analysis.get('requirements_satisfied', []))
        
        for req in requirements:
            earned_weight += weights.get(req, 0)
        
        # Calculate final grade
        grade = (earned_weight / total_weight) * max_grade
        
        # Apply bonus if all requirements covered/satisfied
        if len(requirements) == analysis['total_requirements']:
            bonus = self.config['grading'].get('bonus', {}).get('all_requirements_covered', 0)
            grade = min(grade + bonus, max_grade)
        
        return round(grade, 2)
    
    def grade_student(self, student_id: str, student_dir: Path) -> Dict:
        """Grade a single student's submission - both test coverage and implementation"""
        result = {
            'student_id': student_id,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'test_file': None,
            'implementation_file': None,
            'test_analysis': None,
            'implementation_analysis': None,
            'test_coverage_grade': 0.0,
            'implementation_grade': 0.0,
            'combined_grade': 0.0,
            'error': None
        }
        
        print(f"\nGrading {student_id}...")
        
        # Find test file
        test_file = self.find_test_file(student_dir)
        
        if not test_file:
            result['error'] = "No test file found"
            print(f"  ✗ No test file found in {student_dir}")
            return result
        
        result['test_file'] = str(test_file)
        print(f"  Found test file: {test_file.name}")
        
        # Find implementation file
        impl_file = self.find_implementation_file(student_dir)
        
        if not impl_file:
            result['error'] = "No implementation file found"
            print(f"  ✗ No CruiseControl.java found in {student_dir}")
            return result
        
        result['implementation_file'] = str(impl_file)
        print(f"  Found implementation: {impl_file.name}")
        
        # Analyze test file
        try:
            test_analyzer = TestAnalyzer(str(test_file))
            test_analysis = test_analyzer.analyze()
            result['test_analysis'] = test_analysis
            
            if test_analysis['success']:
                test_grade = self.calculate_grade(test_analysis)
                result['test_coverage_grade'] = test_grade
                print(f"  Test Coverage: {test_analysis['requirements_found']}/{test_analysis['total_requirements']} ({test_analysis['coverage_percentage']}%)")
                print(f"  Test Grade: {test_grade}/{self.config['grading']['max_grade']}")
            else:
                print(f"  ✗ Test analysis failed: {test_analysis.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"  ✗ Error during test analysis: {e}")
        
        # Analyze implementation by ACTUALLY EXECUTING IT
        try:
            # Create execution-based grader
            grader = ExecutionBasedGrader(student_dir)
            impl_analysis = grader.grade_implementation(impl_file)
            
            result['implementation_analysis'] = impl_analysis
            
            if impl_analysis['success']:
                impl_grade = self.calculate_grade(impl_analysis)
                result['implementation_grade'] = impl_grade
                print(f"  Implementation: {impl_analysis['requirements_found']}/{impl_analysis['total_requirements']} ({impl_analysis['satisfaction_percentage']}%)")
                print(f"  Implementation Grade: {impl_grade}/{self.config['grading']['max_grade']}")
            else:
                print(f"  ✗ Implementation testing failed: {impl_analysis.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"  ✗ Error during implementation testing: {e}")
        
        # Calculate combined grade (average of both)
        if result['test_coverage_grade'] > 0 or result['implementation_grade'] > 0:
            result['combined_grade'] = round((result['test_coverage_grade'] + result['implementation_grade']) / 2, 2)
            result['success'] = True
            print(f"  Combined Grade: {result['combined_grade']}/{self.config['grading']['max_grade']}")
        
        return result
    
    def grade_all_students(self, submissions_dir: str) -> List[Dict]:
        """Grade all student submissions"""
        submissions_path = Path(submissions_dir)
        
        if not submissions_path.exists():
            print(f"Error: Submissions directory not found: {submissions_dir}")
            return []
        
        # Get all student directories
        student_dirs = [d for d in submissions_path.iterdir() if d.is_dir()]
        
        print(f"\nFound {len(student_dirs)} student submissions")
        print("=" * 70)
        
        for student_dir in student_dirs:
            student_id = student_dir.name
            result = self.grade_student(student_id, student_dir)
            self.results.append(result)
        
        print("\n" + "=" * 70)
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print grading summary"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total - successful
        
        if successful > 0:
            avg_test_grade = sum(r.get('test_coverage_grade', 0) for r in self.results if r['success']) / successful
            avg_impl_grade = sum(r.get('implementation_grade', 0) for r in self.results if r['success']) / successful
            avg_combined = sum(r.get('combined_grade', 0) for r in self.results if r['success']) / successful
            
            avg_test_coverage = sum(
                r['test_analysis']['coverage_percentage'] 
                for r in self.results 
                if r['success'] and r.get('test_analysis')
            ) / successful
            
            avg_impl_satisfaction = sum(
                r['implementation_analysis']['satisfaction_percentage']
                for r in self.results
                if r['success'] and r.get('implementation_analysis')
            ) / successful
        else:
            avg_test_grade = avg_impl_grade = avg_combined = 0.0
            avg_test_coverage = avg_impl_satisfaction = 0.0
        
        max_grade = self.config['grading']['max_grade']
        
        print(f"\nGrading Summary:")
        print(f"  Total Students: {total}")
        print(f"  Successfully Graded: {successful}")
        print(f"  Failed: {failed}")
        print(f"\n  Test Coverage Grades:")
        print(f"    Average Grade: {avg_test_grade:.2f}/{max_grade}")
        print(f"    Average Coverage: {avg_test_coverage:.1f}%")
        print(f"\n  Implementation Grades:")
        print(f"    Average Grade: {avg_impl_grade:.2f}/{max_grade}")
        print(f"    Average Satisfaction: {avg_impl_satisfaction:.1f}%")
        print(f"\n  Combined Grade: {avg_combined:.2f}/{max_grade}")
        
        if failed > 0:
            print(f"\nFailed submissions:")
            for result in self.results:
                if not result['success']:
                    print(f"  • {result['student_id']}: {result['error']}")

    
    def save_results(self):
        """Save grading results to files"""
        results_dir = Path(self.config['output']['results_directory'])
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual results
        for result in self.results:
            filename = f"{result['student_id']}_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Calculate summary statistics
        successful_results = [r for r in self.results if r['success']]
        total_successful = len(successful_results)
        
        avg_test_grade = 0.0
        avg_impl_grade = 0.0
        avg_combined_grade = 0.0
        
        if total_successful > 0:
            avg_test_grade = sum(r.get('test_coverage_grade', 0) for r in successful_results) / total_successful
            avg_impl_grade = sum(r.get('implementation_grade', 0) for r in successful_results) / total_successful
            avg_combined_grade = sum(r.get('combined_grade', 0) for r in successful_results) / total_successful
        
        # Save summary
        summary_file = results_dir / self.config['output']['summary_file']
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_students': len(self.results),
            'successful': total_successful,
            'average_test_grade': round(avg_test_grade, 2),
            'average_implementation_grade': round(avg_impl_grade, 2),
            'average_combined_grade': round(avg_combined_grade, 2),
            'results': self.results
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nResults saved to: {results_dir}")
        print(f"Summary saved to: {summary_file}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <student_submissions_directory>")
        print("\nExample:")
        print("  python main.py ./student_submissions")
        print("\nThis will:")
        print("  1. Find all student directories")
        print("  2. Locate their test files")
        print("  3. Analyze requirement coverage")
        print("  4. Calculate grades")
        print("  5. Generate reports")
        sys.exit(1)
    
    submissions_dir = sys.argv[1]
    
    grader = GradingSystem()
    grader.grade_all_students(submissions_dir)
    grader.save_results()


if __name__ == '__main__':
    main()
