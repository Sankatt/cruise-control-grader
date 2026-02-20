#!/usr/bin/env python3
"""
Pattern-Based Test Analyzer - Reads patterns from YAML
Identifies which requirements are covered by student tests
Uses flexible matching, Java parsing, and functional approach
"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple


class PatternBasedTestAnalyzer:
    """Analyzes test files using YAML patterns and flexible matching"""
    
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67,
        'R2': 1.67,
        'R3': 1.67,
        'R4': 1.67,
        'R5': 1.67,
        'R6': 1.65
    }
    
    def __init__(self, test_file_path: str, patterns_file: str = "test_patterns.yml"):
        self.test_file_path = Path(test_file_path)
        self.patterns_file = Path(__file__).parent / patterns_file
        self.pending_file = Path(__file__).parent / "pending_test_patterns.yml"
        self.patterns = self.load_patterns()
        self.test_content = ""
        self.test_lines = []
        self.normalized_content = ""
        self.test_methods = []
        
        # Requirement checker functions - functional approach
        self.requirement_checkers = {
            'R1': self.check_r1_test,
            'R2': self.check_r2_test,
            'R3': self.check_r3_test,
            'R4': self.check_r4_test,
            'R5': self.check_r5_test,
            'R6': self.check_r6_test
        }
    
    def load_patterns(self) -> Dict:
        """Load test patterns from YAML file"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load test patterns file: {e}")
            return {}
    
    def normalize_code(self, text: str) -> str:
        """Normalize code by removing extra whitespace and comments"""
        # Remove single-line comments
        text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
        # Remove multi-line comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def load_test_file(self) -> bool:
        """Load and parse test file"""
        try:
            with open(self.test_file_path, 'r', encoding='utf-8') as f:
                self.test_content = f.read()
            
            self.test_lines = self.test_content.split('\n')
            self.normalized_content = self.normalize_code(self.test_content)
            self.test_methods = self.parse_test_methods()
            return True
        except Exception as e:
            print(f"Error loading test file: {e}")
            return False
    
    def parse_test_methods(self) -> List[Dict]:
        """
        Parse Java test methods using flexible patterns
        Handles: @Test, @org.junit.jupiter.api.Test, public/private/no modifier
        """
        methods = []
        
        # Pattern for test methods - very flexible
        # Matches: @Test (or @org.junit...) followed by optional public/private, void, method name, params, body
        pattern = r'@(?:org\.junit\.(?:Test|jupiter\.api\.Test)|Test)\s+(?:public\s+|private\s+)?void\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(pattern, self.test_content, re.DOTALL):
            method_name = match.group(1)
            method_body = match.group(2)
            
            methods.append({
                'name': method_name,
                'body': method_body,
                'full': match.group(0),
                'normalized_body': self.normalize_code(method_body)
            })
        
        return methods
    
    def extract_method_calls_with_values(self, code: str) -> List[Dict]:
        """
        Extract method calls with their actual parameter values
        Returns list of {method: 'setSpeedSet', value: 90, line: '...'}
        """
        calls = []
        
        # Pattern to match method calls with numeric parameters
        pattern = r'(setSpeedSet|setSpeedLimit|getSpeedSet|getSpeedLimit)\s*\(\s*(-?\d+)\s*\)'
        
        for match in re.finditer(pattern, code):
            method = match.group(1)
            value = int(match.group(2))
            calls.append({
                'method': method,
                'value': value,
                'line': match.group(0)
            })
        
        return calls
    
    def check_pattern_flexible(self, patterns: List[str], search_space: str = None) -> Tuple[bool, str]:
        """
        Flexible pattern matching with regex support
        Returns (matched, matched_pattern)
        """
        if search_space is None:
            search_space = self.test_content
        
        normalized_space = self.normalize_code(search_space)
        
        for pattern in patterns:
            # Check for regex prefix
            is_regex = pattern.startswith('regex:')
            
            if is_regex:
                pattern = pattern[6:]
                try:
                    if re.search(pattern, search_space, re.IGNORECASE):
                        return True, pattern
                except re.error:
                    continue
            else:
                # Normalize pattern and do substring matching
                normalized_pattern = self.normalize_code(pattern)
                if normalized_pattern.lower() in normalized_space.lower():
                    return True, pattern
        
        return False, ""
    
    def verify_r5_logic(self, method: Dict) -> Dict:
        """
        Logic-based verification for R5: speedSet respects speedLimit
        
        R5 requires:
        1. setSpeedLimit AND setSpeedSet where speedSet <= speedLimit
        2. EXPLICIT INTENT via comment mentioning limit/speedLimit
        
        Requirements can be tested together, but must show explicit intent
        """
        result = {
            'verified': False,
            'reason': '',
            'evidence': []
        }
        
        method_body = method['body']
        calls = self.extract_method_calls_with_values(method_body)
        
        # Find setSpeedLimit and setSpeedSet calls
        limit_values = [c['value'] for c in calls if c['method'] == 'setSpeedLimit']
        set_values = [c['value'] for c in calls if c['method'] == 'setSpeedSet']
        
        if not limit_values or not set_values:
            result['reason'] = 'Missing setSpeedLimit or setSpeedSet calls'
            return result
        
        # CRITICAL: Must have explicit mention of limit in comments
        # This shows INTENT to test R5, not just coincidental
        has_limit_comment = bool(re.search(
            r'//.*\b(limit|limite|speedLimit)\b',
            method_body,
            re.IGNORECASE
        ))
        
        if not has_limit_comment:
            result['reason'] = 'No explicit comment about limit/speedLimit - intent to test R5 not clear'
            result['evidence'].append('Tests set limit and speedSet, but no comment showing R5 intent')
            return result
        
        # Check if there's an assertion verifying the value was accepted
        has_assertion = (
            'assertEquals' in method_body or 
            'assertTrue' in method_body or
            'getSpeedSet' in method_body
        )
        
        if not has_assertion:
            result['reason'] = 'No assertion to verify speedSet was accepted'
            return result
        
        # Check each combination - ACCEPT if speedSet <= speedLimit
        for limit in limit_values:
            for speed_set in set_values:
                if speed_set <= limit:
                    if speed_set == limit:
                        result['verified'] = True
                        result['reason'] = f'Tests boundary with explicit limit comment: setSpeedSet({speed_set}) == setSpeedLimit({limit})'
                        result['evidence'].append(f'Boundary test: {speed_set} == {limit}')
                        result['evidence'].append('Has explicit comment about limit')
                    else:
                        result['verified'] = True
                        result['reason'] = f'Tests within limit with explicit comment: setSpeedSet({speed_set}) < setSpeedLimit({limit})'
                        result['evidence'].append(f'Below limit: {speed_set} < {limit}')
                        result['evidence'].append('Has explicit comment about limit')
                    return result
        
        # If speedSet > speedLimit, that's R6, not R5
        result['verified'] = False
        result['reason'] = f'speedSet ({set_values}) exceeds limit ({limit_values}) - this tests R6, not R5'
        
        return result
    
    def verify_r3_logic(self, method: Dict) -> Dict:
        """
        Logic-based verification for R3: setSpeedSet accepts positive values
        Must call setSpeedSet with positive value AND verify it's stored
        """
        result = {
            'verified': False,
            'reason': '',
            'evidence': []
        }
        
        method_body = method['body']
        calls = self.extract_method_calls_with_values(method_body)
        
        # Find setSpeedSet calls with positive values
        positive_sets = [c for c in calls if c['method'] == 'setSpeedSet' and c['value'] > 0]
        
        if not positive_sets:
            result['reason'] = 'No setSpeedSet calls with positive values'
            return result
        
        # Check if there's an assertion checking the value was stored
        has_assertion = (
            'assertEquals' in method_body and 'getSpeedSet' in method_body
        ) or 'getSpeedSet()' in method_body
        
        if has_assertion:
            result['verified'] = True
            result['reason'] = f'Sets positive value ({positive_sets[0]["value"]}) and verifies storage'
            result['evidence'].append(f'Positive value: {positive_sets[0]["value"]}')
        else:
            result['reason'] = 'Sets positive value but does not verify it was stored'
        
        return result
    
    def verify_r4_logic(self, method: Dict) -> Dict:
        """
        Logic-based verification for R4: Exception for speedSet <= 0
        Must test invalid values (zero OR negative) with exception
        Based on ADHunter standard: testing negative is sufficient
        """
        result = {
            'verified': False,
            'reason': '',
            'evidence': []
        }
        
        method_body = method['body']
        calls = self.extract_method_calls_with_values(method_body)
        
        # Find setSpeedSet calls with invalid values
        zero_tests = [c for c in calls if c['method'] == 'setSpeedSet' and c['value'] == 0]
        negative_tests = [c for c in calls if c['method'] == 'setSpeedSet' and c['value'] < 0]
        
        # Must have exception handling (assertThrows, try-catch, or expected)
        has_exception_check = (
            'assertThrows' in method_body or 
            'catch' in method_body or
            'expected' in method_body.lower() or
            'IncorrectSpeed' in method_body
        )
        
        if not has_exception_check:
            result['reason'] = 'No exception assertion or handling found'
            return result
        
        # Accept EITHER zero OR negative (not both required)
        if zero_tests:
            result['verified'] = True
            result['reason'] = f'Tests zero (critical boundary) with exception handling'
            result['evidence'].append('Zero test: setSpeedSet(0)')
            if negative_tests:
                result['evidence'].append(f'Also tests negative: setSpeedSet({negative_tests[0]["value"]})')
        elif negative_tests:
            result['verified'] = True
            result['reason'] = f'Tests negative value ({negative_tests[0]["value"]}) with exception handling'
            result['evidence'].append(f'Negative test: setSpeedSet({negative_tests[0]["value"]})')
        else:
            result['reason'] = 'No invalid value tests (zero or negative) found'
        
        return result
    
    def verify_r6_logic(self, method: Dict) -> Dict:
        """
        Logic-based verification for R6: Exception when speedSet > speedLimit
        Must set limit, then try to exceed it
        """
        result = {
            'verified': False,
            'reason': '',
            'evidence': []
        }
        
        method_body = method['body']
        calls = self.extract_method_calls_with_values(method_body)
        
        # Find setSpeedLimit and setSpeedSet calls
        limit_values = [c['value'] for c in calls if c['method'] == 'setSpeedLimit']
        set_values = [c['value'] for c in calls if c['method'] == 'setSpeedSet']
        
        # Must have exception assertion
        has_exception_check = 'assertThrows' in method_body and 'SpeedSetAboveSpeedLimit' in method_body
        
        if not has_exception_check:
            result['reason'] = 'No SpeedSetAboveSpeedLimitException assertion found'
            return result
        
        if not limit_values or not set_values:
            result['reason'] = 'Missing setSpeedLimit or setSpeedSet calls'
            return result
        
        # Check if any speedSet exceeds limit
        for limit in limit_values:
            for speed_set in set_values:
                if speed_set > limit:
                    result['verified'] = True
                    result['reason'] = f'Tests exceeding limit: setSpeedSet({speed_set}) > setSpeedLimit({limit})'
                    result['evidence'].append(f'Exceeds: {speed_set} > {limit}')
                    return result
        
        result['reason'] = f'speedSet ({set_values}) does not exceed limit ({limit_values})'
        return result
        """
        Flexible pattern matching with regex support
        Returns (matched, matched_pattern)
        """
        if search_space is None:
            search_space = self.test_content
        
        normalized_space = self.normalize_code(search_space)
        
        for pattern in patterns:
            # Check for regex prefix
            is_regex = pattern.startswith('regex:')
            
            if is_regex:
                pattern = pattern[6:]
                try:
                    if re.search(pattern, search_space, re.IGNORECASE):
                        return True, pattern
                except re.error:
                    continue
            else:
                # Normalize pattern and do substring matching
                normalized_pattern = self.normalize_code(pattern)
                if normalized_pattern.lower() in normalized_space.lower():
                    return True, pattern
        
        return False, ""
    
    def check_requirement_in_method(self, method: Dict, requirement: str) -> Dict:
        """
        Check if a test method tests a specific requirement
        Uses lines, paths, and entirety checking
        Requires MULTIPLE pattern matches for confidence
        """
        result = {
            'tested': False,
            'method_name': method['name'],
            'matched_patterns': [],
            'confidence': 0,
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False
        }
        
        req_patterns = self.patterns.get(requirement, {}).get('patterns', {})
        method_body = method['body']
        
        # Track which categories matched
        matched_categories = set()
        
        # Check each pattern category
        for category, pattern_list in req_patterns.items():
            if isinstance(pattern_list, list):
                matched, pattern = self.check_pattern_flexible(pattern_list, method_body)
                if matched:
                    result['matched_patterns'].append(f"{category}:{pattern[:30]}")
                    matched_categories.add(category)
                    
                    if category in ['assertion_patterns', 'exception_patterns', 'boundary_or_restriction']:
                        result['by_entirety'] = True
                        result['confidence'] += 2  # Higher weight for critical patterns
                    elif category == 'method_calls':
                        result['by_lines'] = True
                        result['confidence'] += 1
                    elif category == 'keywords':
                        result['by_paths'] = True
                        result['confidence'] += 0.5  # Lower weight for keywords
        
        # Special handling per requirement - require specific combinations
        if requirement == 'R1':
            # Must have assertion about getSpeedSet() and null
            result['tested'] = 'assertion_patterns' in matched_categories and result['confidence'] >= 1
        
        elif requirement == 'R2':
            # Must have assertion about getSpeedLimit() and null
            result['tested'] = 'assertion_patterns' in matched_categories and result['confidence'] >= 1
        
        elif requirement == 'R3':
            # Must have method call AND assertion
            result['tested'] = ('method_calls' in matched_categories or 'assertion_patterns' in matched_categories) and result['confidence'] >= 1
        
        elif requirement == 'R4':
            # Must have exception pattern AND method call with invalid value
            result['tested'] = 'exception_patterns' in matched_categories and result['confidence'] >= 2
        
        elif requirement == 'R5':
            # STRICT: Must have method_calls AND boundary_or_restriction (not just keywords)
            result['tested'] = ('method_calls' in matched_categories and 
                              'boundary_or_restriction' in matched_categories and 
                              result['confidence'] >= 2)
        
        elif requirement == 'R6':
            # Must have exception pattern AND method calls
            result['tested'] = 'exception_patterns' in matched_categories and 'method_calls' in matched_categories and result['confidence'] >= 2
        
        else:
            # Default: require confidence >= 2
            result['tested'] = result['confidence'] >= 2
        
        return result
    
    # Requirement-specific checkers using LOGIC-BASED verification
    
    def check_r1_test(self, patterns: Dict) -> List[Dict]:
        """Check for R1 tests: speedSet initialization to null"""
        matches = []
        
        for method in self.test_methods:
            result = self.check_requirement_in_method(method, 'R1')
            if result['tested']:
                matches.append(result)
        
        return matches
    
    def check_r2_test(self, patterns: Dict) -> List[Dict]:
        """Check for R2 tests: speedLimit initialization to null"""
        matches = []
        
        for method in self.test_methods:
            result = self.check_requirement_in_method(method, 'R2')
            if result['tested']:
                matches.append(result)
        
        return matches
    
    def check_r3_test(self, patterns: Dict) -> List[Dict]:
        """Check for R3 tests: accepts positive values - LOGIC-BASED"""
        matches = []
        
        for method in self.test_methods:
            # First try pattern matching
            result = self.check_requirement_in_method(method, 'R3')
            
            # Then verify logic
            logic_check = self.verify_r3_logic(method)
            
            if logic_check['verified']:
                result['tested'] = True
                result['logic_verified'] = True
                result['verification_reason'] = logic_check['reason']
                matches.append(result)
            elif result['tested']:
                # Pattern matched but logic failed
                result['tested'] = False
                result['logic_verified'] = False
                result['verification_reason'] = logic_check['reason']
        
        return matches
    
    def check_r4_test(self, patterns: Dict) -> List[Dict]:
        """Check for R4 tests: exception for invalid values - LOGIC-BASED"""
        matches = []
        
        for method in self.test_methods:
            # First try pattern matching
            result = self.check_requirement_in_method(method, 'R4')
            
            # Then verify logic
            logic_check = self.verify_r4_logic(method)
            
            if logic_check['verified']:
                result['tested'] = True
                result['logic_verified'] = True
                result['verification_reason'] = logic_check['reason']
                matches.append(result)
            elif result['tested']:
                # Pattern matched but logic failed
                result['tested'] = False
                result['logic_verified'] = False
                result['verification_reason'] = logic_check['reason']
        
        return matches
    
    def check_r5_test(self, patterns: Dict) -> List[Dict]:
        """Check for R5 tests: respects speedLimit - LOGIC-BASED (STRICT)"""
        matches = []
        
        for method in self.test_methods:
            # LOGIC-BASED verification is PRIMARY for R5
            logic_check = self.verify_r5_logic(method)
            
            if logic_check['verified']:
                result = {
                    'tested': True,
                    'method_name': method['name'],
                    'matched_patterns': [],
                    'confidence': 3,
                    'logic_verified': True,
                    'verification_reason': logic_check['reason'],
                    'by_lines': True,
                    'by_paths': True,
                    'by_entirety': True
                }
                matches.append(result)
            else:
                # Even if patterns match, if logic fails, it's not a valid test
                result = {
                    'tested': False,
                    'method_name': method['name'],
                    'matched_patterns': [],
                    'confidence': 0,
                    'logic_verified': False,
                    'verification_reason': logic_check['reason'],
                    'by_lines': False,
                    'by_paths': False,
                    'by_entirety': False
                }
        
        return matches
    
    def check_r6_test(self, patterns: Dict) -> List[Dict]:
        """Check for R6 tests: exception when exceeding limit - LOGIC-BASED"""
        matches = []
        
        for method in self.test_methods:
            # First try pattern matching
            result = self.check_requirement_in_method(method, 'R6')
            
            # Then verify logic
            logic_check = self.verify_r6_logic(method)
            
            if logic_check['verified']:
                result['tested'] = True
                result['logic_verified'] = True
                result['verification_reason'] = logic_check['reason']
                matches.append(result)
            elif result['tested']:
                # Pattern matched but logic failed
                result['tested'] = False
                result['logic_verified'] = False
                result['verification_reason'] = logic_check['reason']
        
        return matches
    
    def log_unmatched_test(self, student_id: str, method: Dict):
        """Log test methods that don't match any known patterns"""
        try:
            # Load existing pending patterns
            pending = {}
            if self.pending_file.exists():
                with open(self.pending_file, 'r', encoding='utf-8') as f:
                    pending = yaml.safe_load(f) or {}
            
            # Create entry
            entry_id = f"test_candidate_{len(pending) + 1:03d}"
            pending[entry_id] = {
                'student': student_id,
                'test_method': method['name'],
                'test_code': method['body'][:200],  # First 200 chars
                'status': 'NEEDS_MANUAL_REVIEW',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'reason': 'Test method found but no patterns matched'
            }
            
            # Save
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                yaml.dump(pending, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            print(f"Warning: Could not log unmatched test: {e}")
    
    def analyze(self, student_id: str = "Unknown") -> Dict:
        """Main analysis method - combines pattern matching + holistic coverage"""
        if not self.load_test_file():
            return {
                'success': False,
                'error': 'Could not load test file',
                'requirements_covered': [],
                'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                'total_test_methods': 0,
                'requirements_found': 0,
                'coverage_percentage': 0.0
            }
        
        # PHASE 1: Pattern matching (fast check)
        print(f"  → Phase 1: Pattern matching analysis...")
        pattern_results = self._analyze_with_patterns()
        
        # PHASE 2: Holistic coverage (run tests check code paths)
        print(f"  → Phase 2: Holistic coverage analysis...")
        holistic_results = self._analyze_holistic_coverage()
        
        # COMBINE RESULTS - take best score from each method
        combined_results = self._combine_results(pattern_results, holistic_results)
        
        requirements_covered = combined_results['requirements_covered']
        requirements_missing = [r for r in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6'] 
                               if r not in requirements_covered]
        
        # Calculate grade
        grade = sum(self.REQUIREMENT_WEIGHTS.get(req, 0) for req in requirements_covered)
        grade = min(round(grade, 2), 10.0)
        
        return {
            'success': True,
            'grade': grade,
            'requirements_covered': requirements_covered,
            'requirements_missing': requirements_missing,
            'requirement_details': combined_results['requirement_details'],
            'total_test_methods': len(self.test_methods),
            'requirements_found': len(requirements_covered),
            'coverage_percentage': round((len(requirements_covered) / 6) * 100, 2),
            'analysis_methods_used': ['pattern_matching', 'holistic_coverage']
        }
    
    def _analyze_with_patterns(self) -> Dict:
        """Pattern matching analysis (existing logic)"""
        requirement_results = {}
        
        for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            checker = self.requirement_checkers[req]
            matches = checker(self.patterns)
            
            requirement_results[req] = {
                'tested': len(matches) > 0,
                'test_methods': [m['method_name'] for m in matches],
                'match_details': matches,
                'method': 'pattern_matching'
            }
        
        return requirement_results
    
    def _find_implementation_file(self, test_file_path: Path) -> Path:
        """
        Find implementation file - handles deep package structures
        Structure: student_dir/src/main/java/es/upm/grise/profundizacion/cruiseControl/CruiseControl.java
        """
        # Start from test file and go up to find student root
        current_dir = test_file_path.parent
        
        # Go up until we find a directory that has 'src' subdirectory
        # This should be the student root
        for _ in range(10):  # Search up to 10 levels
            if (current_dir / 'src').exists():
                # Found student root!
                student_dir = current_dir
                break
            if current_dir.parent == current_dir:  # Reached filesystem root
                student_dir = test_file_path.parent
                break
            current_dir = current_dir.parent
        else:
            student_dir = test_file_path.parent
        
        # Now search recursively from student root for CruiseControl.java
        # Exclude test directories
        for impl_file in student_dir.rglob("CruiseControl.java"):
            if impl_file.is_file():
                # Skip if in test directory
                path_str = str(impl_file)
                if 'test' not in path_str.lower() or 'src/main' in path_str or 'src\\main' in path_str:
                    return impl_file
        
        return None
    
    def _analyze_holistic_coverage(self) -> Dict:
        """Holistic coverage analysis (new logic)"""
        from pathlib import Path
        
        try:
            test_file_path = Path(self.test_file_path)
            
            # Find implementation file
            impl_file = self._find_implementation_file(test_file_path)
            
            if not impl_file or not impl_file.exists():
                print(f"  ⚠ Implementation file not found")
                return {}
            
            print(f"  ✓ Found implementation: {impl_file.name}")
            
            # Import from analyzer directory (same level as this file)
            # Since this file is in analyzer/, we can import directly
            from analyzer.holistic_coverage_analyzer import HolisticCoverageAnalyzer
            
            # Create analyzer
            analyzer = HolisticCoverageAnalyzer(test_file_path.parent)
            
            # Generate coverage report
            report = analyzer.generate_coverage_report(test_file_path, impl_file)
            
            # Convert to our format
            holistic_results = {}
            for req, coverage_data in report['requirements'].items():
                holistic_results[req] = {
                    'tested': coverage_data['covered'],
                    'confidence': coverage_data['confidence'],
                    'details': coverage_data['details'],
                    'method': 'holistic_coverage'
                }
            
            return holistic_results
            
        except Exception as e:
            print(f"  ⚠ Holistic coverage analysis failed: {e}")
            return {}
    
    def _combine_results(self, pattern_results: Dict, holistic_results: Dict) -> Dict:
        """
        Combine pattern matching and holistic coverage results
        Use MAX score - if either method verifies, accept it
        """
        combined = {
            'requirements_covered': [],
            'requirement_details': {}
        }
        
        for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            pattern_tested = pattern_results.get(req, {}).get('tested', False)
            holistic_tested = holistic_results.get(req, {}).get('tested', False)
            
            # Take MAX - verified by either method
            verified = pattern_tested or holistic_tested
            
            if verified:
                combined['requirements_covered'].append(req)
            
            # Build detailed report
            combined['requirement_details'][req] = {
                'tested': verified,
                'pattern_matching': {
                    'verified': pattern_tested,
                    'test_methods': pattern_results.get(req, {}).get('test_methods', []),
                },
                'holistic_coverage': {
                    'verified': holistic_tested,
                    'confidence': holistic_results.get(req, {}).get('confidence', 0.0),
                    'details': holistic_results.get(req, {}).get('details', [])
                },
                'verification_method': 'pattern_matching' if pattern_tested else 'holistic_coverage' if holistic_tested else 'none'
            }
        
        return combined


# Keep backward compatibility
TestAnalyzer = PatternBasedTestAnalyzer


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <path_to_test_file.java>")
        sys.exit(1)
    
    test_file = sys.argv[1]
    student_id = Path(test_file).parent.parent.name if Path(test_file).parent.parent.exists() else "Unknown"
    
    analyzer = PatternBasedTestAnalyzer(test_file)
    result = analyzer.analyze(student_id)
    
    print("\n" + "=" * 70)
    print("PATTERN-BASED TEST ANALYSIS")
    print("=" * 70)
    print(f"\nTest Methods Found: {result['total_test_methods']}")
    print(f"Requirements Covered: {result['requirements_found']}/6 ({result['coverage_percentage']}%)")
    print(f"Grade: {result['grade']}/10.0")
    print(f"\nCovered: {', '.join(result['requirements_covered']) if result['requirements_covered'] else 'None'}")
    print(f"Missing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    if not result['success']:
        print(f"\nError: {result.get('error', 'Unknown error')}")


if __name__ == '__main__':
    main()
