#!/usr/bin/env python3
"""
Main Grading System
Orchestrates cloning, testing, analysis, and report generation
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.test_analyzer import TestAnalyzer


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
        # Common test file locations
        search_paths = [
            student_dir,
            student_dir / 'src' / 'test' / 'java',
            student_dir / 'src' / 'test',
            student_dir / 'test',
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            # Look for *Test.java files
            for test_file in search_path.rglob('*Test.java'):
                return test_file
        
        return None
    
    def calculate_grade(self, analysis: Dict) -> float:
        """Calculate grade based on requirement coverage"""
        if not analysis.get('success'):
            return 0.0
        
        weights = self.config['grading']['requirement_weights']
        max_grade = self.config['grading']['max_grade']
        
        # Calculate weighted score
        total_weight = sum(weights.values())
        earned_weight = 0.0
        
        for req in analysis['requirements_covered']:
            earned_weight += weights.get(req, 0)
        
        # Calculate final grade
        grade = (earned_weight / total_weight) * max_grade
        
        # Apply bonus if all requirements covered
        if len(analysis['requirements_covered']) == analysis['total_requirements']:
            bonus = self.config['grading'].get('bonus', {}).get('all_requirements_covered', 0)
            grade = min(grade + bonus, max_grade)
        
        return round(grade, 2)
    
    def grade_student(self, student_id: str, student_dir: Path) -> Dict:
        """Grade a single student's submission"""
        result = {
            'student_id': student_id,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'test_file': None,
            'analysis': None,
            'grade': 0.0,
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
        
        # Analyze test file
        try:
            analyzer = TestAnalyzer(str(test_file))
            analysis = analyzer.analyze()
            result['analysis'] = analysis
            
            if analysis['success']:
                # Calculate grade
                grade = self.calculate_grade(analysis)
                result['grade'] = grade
                result['success'] = True
                
                print(f"  Coverage: {analysis['requirements_found']}/{analysis['total_requirements']} ({analysis['coverage_percentage']}%)")
                print(f"  Grade: {grade}/{self.config['grading']['max_grade']}")
            else:
                result['error'] = analysis.get('error', 'Analysis failed')
                print(f"  ✗ Analysis failed: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"  ✗ Error during analysis: {e}")
        
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
            avg_grade = sum(r['grade'] for r in self.results if r['success']) / successful
            avg_coverage = sum(
                r['analysis']['coverage_percentage'] 
                for r in self.results 
                if r['success']
            ) / successful
        else:
            avg_grade = 0.0
            avg_coverage = 0.0
        
        print(f"\nGrading Summary:")
        print(f"  Total Students: {total}")
        print(f"  Successfully Graded: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Average Grade: {avg_grade:.2f}/{self.config['grading']['max_grade']}")
        print(f"  Average Coverage: {avg_coverage:.1f}%")
        
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
        
        # Save summary
        summary_file = results_dir / self.config['output']['summary_file']
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_students': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'average_grade': round(
                sum(r['grade'] for r in self.results if r['success']) / max(sum(1 for r in self.results if r['success']), 1),
                2
            ),
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
