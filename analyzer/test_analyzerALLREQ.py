#!/usr/bin/env python3
"""
Test Analyzer - Identifies which requirements are covered by student tests

This script parses a student's test file and maps each test method to 
the requirements it covers based on:
1. Test method names
2. Code patterns (exceptions, assertions, etc.)
3. Comments/annotations
"""

import re
import json
from typing import List, Dict, Set
from pathlib import Path


# Requirement keywords mapping - improved patterns
REQUIREMENT_PATTERNS = {
    'R1': [
        r'speedSet.*null',
        r'getSpeedSet\(\).*null',
        r'initialization.*speedSet',
        r'constructor.*speedSet.*null',
        r'default.*speedSet',
        r'assertNull.*speedSet'
    ],
    'R2': [
        r'speedLimit.*null',
        r'getSpeedLimit\(\).*null', 
        r'initialization.*speedLimit',
        r'constructor.*speedLimit.*null',
        r'default.*speedLimit',
        r'assertNull.*speedLimit'
    ],
    'R3': [
        r'setSpeedSet.*positive',
        r'setSpeedSet\s*\(\s*[1-9]',
        r'valid.*speedSet',
        r'setting.*valid.*speed',
        r'assertEquals.*speedSet'
    ],
    'R4': [
        r'IncorrectSpeedSetException',
        r'setSpeedSet\s*\(\s*0',
        r'setSpeedSet\s*\(\s*-',
        r'negative.*speedSet',
        r'zero.*speedSet',
        r'assertThrows.*setSpeedSet\s*\(\s*[0-]'
    ],
    'R5': [
        r'speedSet.*speedLimit',
        r'setSpeedSet.*limit',
        r'above.*limit',
        r'exceed.*limit',
        r'setSpeedLimit.*setSpeedSet'
    ],
    'R6': [
        r'SpeedSetAboveSpeedLimitException',
        r'speedSet.*exceed.*speedLimit',
        r'assertThrows.*SpeedSetAbove',
        r'above.*limit.*exception'
    ],
    'R7': [
        r'setSpeedLimit.*positive',
        r'setSpeedLimit\s*\(\s*[1-9]',
        r'valid.*speedLimit'
    ],
    'R8': [
        r'IncorrectSpeedLimitException',
        r'setSpeedLimit\s*\(\s*[0-]',
        r'negative.*speedLimit',
        r'zero.*speedLimit'
    ],
    'R9': [
        r'CannotSetSpeedLimitException',
        r'setSpeedLimit.*after.*speedSet'
    ],
    'R10': [
        r'disable.*speedSet.*null',
        r'disable.*getSpeedSet'
    ],
    'R11': [
        r'disable.*speedLimit.*not',
        r'disable.*speedLimit.*unchanged'
    ],
    'R12': [
        r'nextCommand.*IDLE.*not.*initialized',
        r'IDLE.*speedSet.*null'
    ],
    'R13': [
        r'nextCommand.*IDLE.*disable',
        r'disable.*IDLE'
    ],
    'R14': [
        r'REDUCE.*speed.*greater',
        r'current.*speed.*>.*speedSet'
    ],
    'R15': [
        r'INCREASE.*minimum.*road',
        r'road.*minimum.*speed'
    ],
    'R16': [
        r'INCREASE.*speed.*less',
        r'current.*speed.*<.*speedSet'
    ],
    'R17': [
        r'REDUCE.*speedLimit.*exceed',
        r'speed.*>.*speedLimit'
    ],
    'R18': [
        r'REDUCE.*maximum.*road',
        r'road.*maximum.*speed'
    ],
    'R19': [
        r'KEEP.*equal',
        r'current.*speed.*==.*speedSet'
    ]
}


class TestAnalyzer:
    """Analyzes student test files to identify requirement coverage"""
    
    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        self.test_content = ""
        self.test_methods = []
        self.requirements_covered = set()
        
    def load_test_file(self) -> bool:
        """Load the test file content"""
        try:
            with open(self.test_file_path, 'r', encoding='utf-8') as f:
                self.test_content = f.read()
            return True
        except Exception as e:
            print(f"Error loading test file: {e}")
            return False
    
    def extract_test_methods(self) -> List[Dict]:
        """Extract individual test methods from the file"""
        # Match JUnit test methods - both JUnit 4 and JUnit 5
        # Improved pattern to catch methods with @Test annotation regardless of naming
        test_pattern = r'@Test[^{]*?(?:void|public\s+void)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}'
        
        matches = re.finditer(test_pattern, self.test_content, re.MULTILINE | re.DOTALL)
        
        methods = []
        for match in matches:
            method_name = match.group(1)
            method_body = match.group(2)
            
            methods.append({
                'name': method_name,
                'code': match.group(0),
                'body': method_body,
                'requirements': set()
            })
        
        self.test_methods = methods
        return methods
    
    def analyze_method_for_requirements(self, method: Dict) -> Set[str]:
        """Analyze a single test method to identify covered requirements"""
        covered = set()
        
        # Analyze both method name and full code
        method_name_lower = method['name'].lower()
        method_code_lower = method['code'].lower()
        method_body_lower = method.get('body', '').lower()
        
        # Combine all text for analysis
        combined_text = f"{method_name_lower} {method_code_lower} {method_body_lower}"
        
        for req_id, patterns in REQUIREMENT_PATTERNS.items():
            for pattern in patterns:
                # Search in combined text
                if re.search(pattern, combined_text, re.IGNORECASE):
                    covered.add(req_id)
                    break  # Found this requirement, move to next
        
        return covered
    
    def analyze(self) -> Dict:
        """Main analysis method - returns full analysis report"""
        if not self.load_test_file():
            return {
                'success': False,
                'error': 'Failed to load test file'
            }
        
        self.extract_test_methods()
        
        # Analyze each method
        for method in self.test_methods:
            method['requirements'] = self.analyze_method_for_requirements(method)
            self.requirements_covered.update(method['requirements'])
        
        # Calculate statistics
        all_requirements = set(REQUIREMENT_PATTERNS.keys())
        missing_requirements = all_requirements - self.requirements_covered
        coverage_percentage = (len(self.requirements_covered) / len(all_requirements)) * 100
        
        return {
            'success': True,
            'test_file': str(self.test_file_path),
            'test_methods': [
                {
                    'name': m['name'],
                    'requirements': sorted(list(m['requirements']))
                }
                for m in self.test_methods
            ],
            'requirements_covered': sorted(list(self.requirements_covered)),
            'requirements_missing': sorted(list(missing_requirements)),
            'total_requirements': len(all_requirements),
            'requirements_found': len(self.requirements_covered),
            'coverage_percentage': round(coverage_percentage, 2),
            'test_count': len(self.test_methods)
        }
    
    def generate_report(self) -> str:
        """Generate a human-readable report"""
        analysis = self.analyze()
        
        if not analysis['success']:
            return f"Analysis failed: {analysis.get('error', 'Unknown error')}"
        
        report = []
        report.append("=" * 70)
        report.append("TEST ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Test File: {analysis['test_file']}")
        report.append(f"Test Methods Found: {analysis['test_count']}")
        report.append("")
        
        report.append(f"Requirements Coverage: {analysis['requirements_found']}/{analysis['total_requirements']} ({analysis['coverage_percentage']}%)")
        report.append("")
        
        report.append("COVERED REQUIREMENTS:")
        if analysis['requirements_covered']:
            for req in analysis['requirements_covered']:
                report.append(f"  ✓ {req}")
        else:
            report.append("  (none)")
        report.append("")
        
        report.append("MISSING REQUIREMENTS:")
        if analysis['requirements_missing']:
            for req in analysis['requirements_missing']:
                report.append(f"  ✗ {req}")
        else:
            report.append("  (none)")
        report.append("")
        
        report.append("TEST METHODS:")
        for method in analysis['test_methods']:
            report.append(f"  • {method['name']}")
            if method['requirements']:
                report.append(f"    Requirements: {', '.join(method['requirements'])}")
            else:
                report.append("    Requirements: (none identified)")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <path_to_test_file>")
        print("\nExample:")
        print("  python test_analyzer.py StudentTest.java")
        sys.exit(1)
    
    test_file = sys.argv[1]
    analyzer = TestAnalyzer(test_file)
    
    # Generate and print report
    print(analyzer.generate_report())
    
    # Optionally save JSON
    if len(sys.argv) > 2 and sys.argv[2] == '--json':
        analysis = analyzer.analyze()
        json_output = f"{test_file}.analysis.json"
        with open(json_output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nJSON report saved to: {json_output}")


if __name__ == '__main__':
    main()
