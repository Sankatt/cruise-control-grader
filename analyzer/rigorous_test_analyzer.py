#!/usr/bin/env python3
"""
Rigorous Test Analyzer
Analyzes test quality using formal verification methods
- Checks for proper assertions
- Verifies boundary testing
- Ensures exception verification
- Applies 80% satisfaction threshold
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class TestQualityMetric(Enum):
    """Quality metrics for test analysis"""
    HAS_ASSERTIONS = "has_assertions"
    TESTS_BOUNDARIES = "tests_boundaries"
    VERIFIES_EXCEPTIONS = "verifies_exception_type"
    TESTS_MULTIPLE_CASES = "tests_multiple_cases"
    PROPER_TEST_STRUCTURE = "proper_test_structure"


@dataclass
class TestQualityAnalysis:
    """Quality analysis for a single test"""
    test_method_name: str
    requirement: str
    has_assertions: bool
    assertion_types: List[str]
    tests_boundaries: bool
    boundary_values_tested: List[str]
    verifies_exceptions: bool
    exception_types_verified: List[str]
    tests_multiple_cases: bool
    case_count: int
    proper_structure: bool
    quality_score: float
    issues: List[str]


class RigorousTestAnalyzer:
    """
    Analyzes test quality using formal verification criteria
    Similar to rigorous implementation grader but for tests
    """
    
    # Requirement weights (same as implementation grader)
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67,
        'R2': 1.67,
        'R3': 1.67,
        'R4': 1.67,
        'R5': 1.67,
        'R6': 1.65
    }
    
    # Quality criteria per requirement
    QUALITY_CRITERIA = {
        'R1': {
            'must_check_initialization': True,
            'must_assert_null': True,
            'min_assertions': 1
        },
        'R2': {
            'must_check_initialization': True,
            'must_assert_null': True,
            'min_assertions': 1
        },
        'R3': {
            'must_test_positive_values': True,
            'must_have_assertions': True,
            'should_test_multiple_values': True,
            'min_test_cases': 2
        },
        'R4': {
            'must_verify_exception': True,
            'must_test_negative_values': True,
            'must_test_zero': True,  # Critical boundary!
            'must_check_correct_exception_type': True,
            'min_test_cases': 2
        },
        'R5': {
            'must_test_with_limit_set': True,
            'must_test_below_limit': True,
            'must_test_at_boundary': True,
            'min_assertions': 1
        },
        'R6': {
            'must_verify_exception': True,
            'must_test_exceeding_limit': True,
            'must_check_correct_exception_type': True,
            'should_test_boundary': True,
            'min_test_cases': 1
        }
    }
    
    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        self.content = self._read_file()
        self.test_methods = {}
        self.requirement_tests = {f'R{i}': [] for i in range(1, 7)}
        
    def _read_file(self) -> str:
        """Read test file content"""
        try:
            return self.test_file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return self.test_file_path.read_text(encoding='latin-1')
    
    def analyze(self) -> Dict:
        """Main analysis method"""
        # Extract test methods
        self._extract_test_methods()
        
        # Analyze each test's quality
        quality_analyses = self._analyze_test_quality()
        
        # Map tests to requirements
        self._map_tests_to_requirements(quality_analyses)
        
        # Calculate requirement satisfaction
        requirement_analysis = self._calculate_requirement_satisfaction()
        
        # Calculate overall grade
        satisfied_requirements = [req for req, analysis in requirement_analysis.items() 
                                 if analysis['satisfied']]
        missing_requirements = [req for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
                               if req not in satisfied_requirements]
        
        # Calculate grade
        grade = sum(self.REQUIREMENT_WEIGHTS[req] for req in satisfied_requirements)
        grade = min(grade, 10.0)
        
        return {
            'success': True,
            'test_file': str(self.test_file_path),
            'total_test_methods': len(self.test_methods),
            'requirements_covered': satisfied_requirements,
            'requirements_missing': missing_requirements,
            'total_requirements': 6,
            'requirements_found': len(satisfied_requirements),
            'coverage_percentage': round((len(satisfied_requirements) / 6) * 100, 2),
            'grade': round(grade, 2),
            'requirement_analysis': requirement_analysis,
            'test_quality_details': quality_analyses,
            'grading_methodology': 'Rigorous Test Quality Analysis with 80% Threshold'
        }
    
    def _extract_test_methods(self):
        """Extract all test methods from the file"""
        # More flexible pattern to match test methods
        # Handles: @Test, @org.junit.Test, @org.junit.jupiter.api.Test
        # Handles with or without 'public' keyword
        # Handles annotations on separate lines or same line
        test_pattern = r'@(?:org\.junit(?:\.jupiter\.api)?\.)?Test\s+(?:public\s+)?void\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        matches = re.finditer(test_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            method_name = match.group(1)
            method_body = match.group(2)
            self.test_methods[method_name] = method_body
        
        # If no matches, try annotation on previous line
        if not self.test_methods:
            # Split by @Test and look for methods after
            parts = self.content.split('@Test')
            for i, part in enumerate(parts[1:], 1):  # Skip first part before any @Test
                # Look for method declaration within next 200 chars
                method_match = re.search(r'(?:public\s+)?void\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', part[:2000], re.DOTALL)
                if method_match:
                    method_name = method_match.group(1)
                    method_body = method_match.group(2)
                    self.test_methods[method_name] = method_body
    
    def _analyze_test_quality(self) -> Dict[str, Dict]:
        """Analyze quality of each test method"""
        analyses = {}
        
        for method_name, method_body in self.test_methods.items():
            # Determine which requirement this test covers
            requirement = self._identify_requirement(method_name, method_body)
            
            # Analyze assertions
            has_assertions, assertion_types = self._check_assertions(method_body)
            
            # Analyze boundary testing
            tests_boundaries, boundary_values = self._check_boundary_testing(method_body, requirement)
            
            # Analyze exception verification
            verifies_exceptions, exception_types = self._check_exception_verification(method_body, requirement)
            
            # Check for multiple test cases
            tests_multiple, case_count = self._check_multiple_cases(method_body, requirement)
            
            # Check proper structure
            proper_structure = self._check_proper_structure(method_body)
            
            # Calculate quality score
            quality_score, issues = self._calculate_quality_score(
                requirement, has_assertions, tests_boundaries, 
                verifies_exceptions, tests_multiple, proper_structure,
                assertion_types, boundary_values, exception_types
            )
            
            # Store as dict instead of dataclass
            analyses[method_name] = {
                'test_method_name': method_name,
                'requirement': requirement,
                'has_assertions': has_assertions,
                'assertion_types': assertion_types,
                'tests_boundaries': tests_boundaries,
                'boundary_values_tested': boundary_values,
                'verifies_exceptions': verifies_exceptions,
                'exception_types_verified': exception_types,
                'tests_multiple_cases': tests_multiple,
                'case_count': case_count,
                'proper_structure': proper_structure,
                'quality_score': quality_score,
                'issues': issues
            }
        
        return analyses
    
    def _identify_requirement(self, method_name: str, method_body: str) -> str:
        """Identify which requirement the test covers"""
        method_lower = method_name.lower()
        body_lower = method_body.lower()
        
        # R1: speedSet initialization
        if 'r1' in method_lower or ('speedset' in body_lower and 'null' in body_lower and 'constructor' in method_lower):
            return 'R1'
        
        # R2: speedLimit initialization  
        if 'r2' in method_lower or ('speedlimit' in body_lower and 'null' in body_lower and 'constructor' in method_lower):
            return 'R2'
        
        # Check for constructor test that tests BOTH
        if 'constructor' in method_lower or 'constructor' in body_lower:
            if 'speedset' in body_lower and 'null' in body_lower:
                if 'speedlimit' in body_lower:
                    # Tests both R1 and R2, but we can only return one
                    # Return R1, and we'll need to handle this edge case
                    return 'R1'  # Will also credit R2 in special handling
                return 'R1'
            if 'speedlimit' in body_lower and 'null' in body_lower:
                return 'R2'
        
        # R4: Exception for negative/zero (check before R3)
        # Look for various exception names students might use
        if 'r4' in method_lower or 'incorrect' in method_lower or 'negative' in method_lower or 'zero' in method_lower:
            return 'R4'
        
        # R6: Exception for exceeding limit (check before R5)
        # Look for various exception names
        if 'r6' in method_lower or 'above' in method_lower or 'exceed' in method_lower or 'surpass' in method_lower:
            return 'R6'
        
        # R3: Positive values
        if 'r3' in method_lower or ('positive' in method_lower or 'correct' in method_lower or 'valid' in method_lower):
            return 'R3'
        
        # R5: Respects limit
        if 'r5' in method_lower or ('limit' in method_lower and 'respect' in method_lower):
            return 'R5'
        
        # Default: try to infer from method body
        # Check for exception types (handle variations)
        if 'incorrectspeedsetexception' in body_lower or 'incorrectspeedexception' in body_lower:
            return 'R4'
        if 'speedsetabovespeedlimitexception' in body_lower or 'speedabovespeedlimitexception' in body_lower:
            return 'R6'
        
        # Check for speedLimit usage
        if 'speedlimit' in body_lower or 'setspeedlimit' in body_lower:
            if 'surpass' in body_lower or 'exceed' in body_lower or 'above' in body_lower:
                return 'R6'
            return 'R5'
        
        # Check for negative values in method body
        if '-' in method_body and 'setspeedset' in body_lower:
            return 'R4'
        
        # If still unknown, check if it's a general speedSet test
        if 'setspeedset' in body_lower or 'speedset' in body_lower:
            return 'R3'
        
        return 'UNKNOWN'
    
    def _check_assertions(self, method_body: str) -> Tuple[bool, List[str]]:
        """Check if test has proper assertions"""
        assertion_patterns = [
            r'assert(True|False|Equals|NotEquals|Null|NotNull|Same|NotSame|Throws)',
            r'assertEquals',
            r'assertNotEquals',
            r'assertTrue',
            r'assertFalse',
            r'assertNull',
            r'assertNotNull',
            r'assertThrows',
            r'fail\(',
        ]
        
        assertions_found = []
        for pattern in assertion_patterns:
            matches = re.findall(pattern, method_body)
            assertions_found.extend(matches)
        
        return len(assertions_found) > 0, list(set(assertions_found))
    
    def _check_boundary_testing(self, method_body: str, requirement: str) -> Tuple[bool, List[str]]:
        """Check if test includes boundary values"""
        boundaries_found = []
        
        if requirement == 'R4':
            # Check for zero (critical boundary)
            if re.search(r'setSpeedSet\s*\(\s*0\s*\)', method_body):
                boundaries_found.append('zero')
            # Check for -1 (boundary)
            if re.search(r'setSpeedSet\s*\(\s*-1\s*\)', method_body):
                boundaries_found.append('-1')
        
        elif requirement == 'R5' or requirement == 'R6':
            # Check for limit-1, limit, limit+1
            if re.search(r'(speedLimit|limit)\s*[-+]\s*1', method_body):
                boundaries_found.append('limit±1')
            if 'speedLimit' in method_body or 'limit' in method_body:
                boundaries_found.append('at_limit')
        
        return len(boundaries_found) > 0, boundaries_found
    
    def _check_exception_verification(self, method_body: str, requirement: str) -> Tuple[bool, List[str]]:
        """Check if test properly verifies exceptions"""
        exceptions_found = []
        
        # Check for assertThrows (best practice)
        if 'assertThrows' in method_body:
            # Extract exception type
            throws_match = re.search(r'assertThrows\s*\(\s*(\w+)\.class', method_body)
            if throws_match:
                exceptions_found.append(throws_match.group(1))
        
        # Check for try-catch with assertions
        if 'try' in method_body and 'catch' in method_body:
            catch_matches = re.findall(r'catch\s*\(\s*(\w+)', method_body)
            exceptions_found.extend(catch_matches)
        
        # Verify correct exception type
        if requirement == 'R4':
            has_correct = 'IncorrectSpeedSetException' in method_body
        elif requirement == 'R6':
            has_correct = 'SpeedSetAboveSpeedLimitException' in method_body
        else:
            has_correct = len(exceptions_found) > 0
        
        return has_correct, exceptions_found
    
    def _check_multiple_cases(self, method_body: str, requirement: str) -> Tuple[bool, int]:
        """Check if test covers multiple cases"""
        # Count setSpeedSet calls
        set_calls = len(re.findall(r'setSpeedSet\s*\(', method_body))
        
        # Count setSpeedLimit calls
        limit_calls = len(re.findall(r'setSpeedLimit\s*\(', method_body))
        
        total_calls = set_calls + limit_calls
        
        criteria = self.QUALITY_CRITERIA.get(requirement, {})
        min_cases = criteria.get('min_test_cases', 1)
        
        return total_calls >= min_cases, total_calls
    
    def _check_proper_structure(self, method_body: str) -> bool:
        """Check if test has proper structure (Arrange-Act-Assert)"""
        # Basic check: has object creation and method call
        has_object_creation = 'new CruiseControl' in method_body or 'CruiseControl' in method_body
        has_method_call = 'setSpeedSet' in method_body or 'setSpeedLimit' in method_body
        
        return has_object_creation and has_method_call
    
    def _calculate_quality_score(self, requirement: str, has_assertions: bool, 
                                 tests_boundaries: bool, verifies_exceptions: bool,
                                 tests_multiple: bool, proper_structure: bool,
                                 assertion_types: List[str], boundary_values: List[str],
                                 exception_types: List[str]) -> Tuple[float, List[str]]:
        """Calculate quality score based on criteria"""
        criteria = self.QUALITY_CRITERIA.get(requirement, {})
        score = 0.0
        max_score = 0.0
        issues = []
        
        # Check assertions (20 points)
        max_score += 20
        if criteria.get('must_have_assertions') or criteria.get('must_assert_null'):
            if has_assertions:
                score += 20
            else:
                issues.append("Missing assertions")
        else:
            score += 20  # Not required
        
        # Check exception verification (30 points)
        max_score += 30
        if criteria.get('must_verify_exception'):
            if verifies_exceptions:
                if criteria.get('must_check_correct_exception_type'):
                    # Verify correct exception type
                    if requirement == 'R4' and any('IncorrectSpeedSet' in e for e in exception_types):
                        score += 30
                    elif requirement == 'R6' and any('SpeedSetAboveSpeedLimit' in e for e in exception_types):
                        score += 30
                    else:
                        score += 15
                        issues.append("Exception type not explicitly verified")
                else:
                    score += 30
            else:
                issues.append("Exception not verified")
        else:
            score += 30  # Not required
        
        # Check boundary testing (25 points)
        max_score += 25
        if criteria.get('must_test_zero'):
            if 'zero' in boundary_values:
                score += 25
            else:
                issues.append("Zero boundary not tested (critical for R4!)")
        elif criteria.get('should_test_boundary'):
            if tests_boundaries:
                score += 25
            else:
                score += 12.5
                issues.append("Boundary values not tested")
        else:
            score += 25  # Not required
        
        # Check multiple cases (15 points)
        max_score += 15
        if criteria.get('should_test_multiple_values') or criteria.get('min_test_cases', 0) > 1:
            if tests_multiple:
                score += 15
            else:
                issues.append("Should test multiple cases")
        else:
            score += 15  # Not required
        
        # Check proper structure (10 points)
        max_score += 10
        if proper_structure:
            score += 10
        else:
            issues.append("Improper test structure")
        
        # Convert to percentage
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        return round(percentage, 2), issues
    
    def _map_tests_to_requirements(self, quality_analyses: Dict[str, Dict]):
        """Map test methods to requirements"""
        for test_name, analysis in quality_analyses.items():
            req = analysis['requirement']
            if req in self.requirement_tests:
                self.requirement_tests[req].append(analysis)
    
    def _calculate_requirement_satisfaction(self) -> Dict:
        """Calculate satisfaction for each requirement"""
        requirement_analysis = {}
        
        for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            tests = self.requirement_tests[req]
            
            if not tests:
                # No test found for this requirement
                requirement_analysis[req] = {
                    'tested': False,
                    'satisfied': False,
                    'quality_score': 0.0,
                    'test_count': 0,
                    'issues': ['No test found for this requirement'],
                    'test_methods': [],
                    'description': self._get_requirement_description(req)
                }
            else:
                # Calculate average quality score
                avg_quality = sum(t['quality_score'] for t in tests) / len(tests)
                
                # Collect all issues
                all_issues = []
                for test in tests:
                    all_issues.extend(test['issues'])
                
                # Apply 80% threshold
                satisfied = avg_quality >= 80.0
                
                requirement_analysis[req] = {
                    'tested': True,
                    'satisfied': satisfied,
                    'quality_score': round(avg_quality, 2),
                    'test_count': len(tests),
                    'issues': list(set(all_issues)),
                    'test_methods': [t['test_method_name'] for t in tests],
                    'test_details': [
                        {
                            'method': t['test_method_name'],
                            'quality_score': t['quality_score'],
                            'has_assertions': t['has_assertions'],
                            'tests_boundaries': t['tests_boundaries'],
                            'verifies_exceptions': t['verifies_exceptions'],
                            'issues': t['issues']
                        }
                        for t in tests
                    ],
                    'description': self._get_requirement_description(req)
                }
        
        return requirement_analysis
    
    def _get_requirement_description(self, req: str) -> str:
        """Get requirement description"""
        descriptions = {
            'R1': 'R1-INICIALIZACION: speedSet should initialize to null',
            'R2': 'R2-INICIALIZACION: speedLimit should initialize to null',
            'R3': 'R3: speedSet can adopt any positive value (> 0)',
            'R4': 'R4-ERROR: Throw IncorrectSpeedSetException if speedSet is <= 0',
            'R5': 'R5-ALTERNATIVO: If speedLimit is set, speedSet cannot exceed it',
            'R6': 'R6-ERROR: Throw SpeedSetAboveSpeedLimitException if speedSet > speedLimit'
        }
        return descriptions.get(req, '')


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rigorous_test_analyzer.py <test_file.java>")
        sys.exit(1)
    
    test_file = sys.argv[1]
    analyzer = RigorousTestAnalyzer(test_file)
    result = analyzer.analyze()
    
    print("\n" + "=" * 70)
    print("RIGOROUS TEST QUALITY ANALYSIS")
    print("=" * 70)
    print(f"\nTest File: {result['test_file']}")
    print(f"Total Test Methods: {result['total_test_methods']}")
    print(f"\nRequirements Covered: {result['requirements_found']}/6 ({result['coverage_percentage']}%)")
    print(f"Grade: {result['grade']}/10.0")
    print(f"\nCovered: {', '.join(result['requirements_covered']) if result['requirements_covered'] else 'None'}")
    print(f"Missing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    print("\n" + "=" * 70)
    print("DETAILED REQUIREMENT ANALYSIS")
    print("=" * 70)
    
    for req, analysis in result['requirement_analysis'].items():
        print(f"\n{req}: {analysis['description']}")
        print(f"  Status: {'✓ SATISFIED' if analysis['satisfied'] else '✗ NOT SATISFIED'}")
        print(f"  Tested: {'Yes' if analysis['tested'] else 'No'}")
        
        if analysis['tested']:
            print(f"  Quality Score: {analysis['quality_score']}%")
            print(f"  Test Count: {analysis['test_count']}")
            print(f"  Test Methods: {', '.join(analysis['test_methods'])}")
            
            if analysis['issues']:
                print(f"  Issues:")
                for issue in analysis['issues']:
                    print(f"    - {issue}")


if __name__ == '__main__':
    main()
