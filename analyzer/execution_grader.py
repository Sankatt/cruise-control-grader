#!/usr/bin/env python3
"""
Pattern-Based Execution Grader - Reads patterns from YAML
Checks code via lines, paths, and entirety
Uses functional/operator approach instead of long if-then chains
"""

import subprocess
import os
import shutil
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Callable


class PatternBasedGrader:
    """Grades implementation by pattern matching and execution"""
    
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67,
        'R2': 1.67,
        'R3': 1.67,
        'R4': 1.67,
        'R5': 1.67,
        'R6': 1.65
    }
    
    def __init__(self, student_dir: Path, patterns_file: str = "implementation_patterns.yml"):
        self.student_dir = Path(student_dir)
        self.patterns_file = Path(__file__).parent / patterns_file
        self.pending_file = Path(__file__).parent / "pending_patterns.yml"
        self.patterns = self.load_patterns()
        self.code_content = ""
        self.code_lines = []
        
        # Requirement checker functions - functional approach
        self.requirement_checkers = {
            'R1': self.check_r1,
            'R2': self.check_r2,
            'R3': self.check_r3,
            'R4': self.check_r4,
            'R5': self.check_r5,
            'R6': self.check_r6
        }
    
    def load_patterns(self) -> Dict:
        """Load patterns from YAML file"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load patterns file: {e}")
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
    
    def load_code(self, cruise_control_file: Path) -> bool:
        """Load student code for pattern matching"""
        try:
            self.code_content = cruise_control_file.read_text(encoding='utf-8')
            self.code_lines = self.code_content.split('\n')
            self.normalized_code = self.normalize_code(self.code_content)
            return True
        except Exception as e:
            print(f"Error loading code: {e}")
            return False
    
    def parse_java_structure(self) -> Dict:
        """Parse Java code structure to find constructors, methods, fields"""
        structure = {
            'fields': [],
            'constructor': None,
            'methods': [],
            'constructor_body': ''
        }
        
        try:
            # Find field declarations
            field_pattern = r'private\s+(\w+)\s+(\w+)\s*;'
            for match in re.finditer(field_pattern, self.code_content):
                structure['fields'].append({
                    'type': match.group(1),
                    'name': match.group(2)
                })
            
            # Find constructor
            constructor_pattern = r'public\s+CruiseControl\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            constructor_match = re.search(constructor_pattern, self.code_content, re.DOTALL)
            if constructor_match:
                structure['constructor'] = constructor_match.group(0)
                structure['constructor_body'] = constructor_match.group(1)
            
            # Find methods
            method_pattern = r'(public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            for match in re.finditer(method_pattern, self.code_content, re.DOTALL):
                method_name = match.group(2)
                method_body = match.group(3)
                structure['methods'].append({
                    'name': method_name,
                    'body': method_body,
                    'full': match.group(0)
                })
        
        except Exception as e:
            print(f"Warning: Could not parse Java structure: {e}")
        
        return structure
    
    def check_pattern_flexible(self, patterns: List[str], search_space: str = None) -> bool:
        """
        Flexible pattern matching:
        1. Removes whitespace sensitivity
        2. Supports regex patterns (patterns starting with 'regex:')
        3. Case-insensitive option (patterns starting with 'i:')
        """
        if search_space is None:
            search_space = self.code_content
        
        normalized_space = self.normalize_code(search_space)
        
        for pattern in patterns:
            # Check for special pattern prefixes
            case_insensitive = False
            is_regex = False
            
            if pattern.startswith('i:'):
                case_insensitive = True
                pattern = pattern[2:]
            
            if pattern.startswith('regex:'):
                is_regex = True
                pattern = pattern[6:]
            
            if is_regex:
                # Use regex matching
                flags = re.IGNORECASE if case_insensitive else 0
                if re.search(pattern, search_space, flags):
                    return True
            else:
                # Normalize pattern and do substring matching
                normalized_pattern = self.normalize_code(pattern)
                
                if case_insensitive:
                    if normalized_pattern.lower() in normalized_space.lower():
                        return True
                else:
                    if normalized_pattern in normalized_space:
                        return True
        
        return False
    
    def check_initialization_in_constructor(self, field_name: str, expected_value: str = "null") -> bool:
        """
        Check if a field is initialized in the constructor
        Uses Java structure parsing for accuracy
        """
        structure = self.parse_java_structure()
        
        if not structure['constructor_body']:
            return False
        
        constructor_body = structure['constructor_body']
        
        # Check for various initialization patterns
        patterns = [
            rf'{field_name}\s*=\s*{expected_value}',
            rf'this\.{field_name}\s*=\s*{expected_value}',
        ]
        
        for pattern in patterns:
            if re.search(pattern, constructor_body):
                return True
        
        return False
    
    def check_pattern_in_lines(self, patterns: List[str]) -> bool:
        """Check if any pattern exists in any line"""
        for line in self.code_lines:
            line_clean = line.strip()
            for pattern in patterns:
                if pattern in line_clean:
                    return True
        return False
    
    def check_pattern_in_content(self, patterns: List[str]) -> bool:
        """Check if any pattern exists in entire content"""
        for pattern in patterns:
            if pattern in self.code_content:
                return True
        return False
    
    def check_pattern_in_paths(self, patterns: List[str], context_patterns: List[str] = None) -> bool:
        """
        Check if patterns exist in code paths (within if/else blocks, methods, etc.)
        Optionally check if they're in the same context
        """
        if not context_patterns:
            return self.check_pattern_in_content(patterns)
        
        # Check if both pattern and context appear together
        for i, line in enumerate(self.code_lines):
            # Find context pattern
            for ctx_pattern in context_patterns:
                if ctx_pattern in line:
                    # Check next 10 lines for the pattern
                    for j in range(i, min(i + 10, len(self.code_lines))):
                        for pattern in patterns:
                            if pattern in self.code_lines[j]:
                                return True
        return False
    
    def check_all_methods(self, requirement: str, patterns_dict: Dict) -> Dict:
        """
        Check requirement using all three methods:
        1. Line-by-line
        2. Code paths (context-aware)
        3. Entire content
        Returns dict with results from each method
        """
        results = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        # Check each category of patterns
        for category, patterns in patterns_dict.items():
            if isinstance(patterns, list):
                # Check by lines
                if self.check_pattern_in_lines(patterns):
                    results['by_lines'] = True
                    results['matched_patterns'].append(f"{category}:line")
                
                # Check by entirety
                if self.check_pattern_in_content(patterns):
                    results['by_entirety'] = True
                    results['matched_patterns'].append(f"{category}:content")
        
        # For path checking, look for contextual patterns
        # e.g., for R4, check if exception throw is inside validation check
        if requirement in ['R4', 'R5', 'R6']:
            validation_patterns = patterns_dict.get('validation_checks', [])
            action_patterns = patterns_dict.get('lines', [])
            
            if validation_patterns and action_patterns:
                if self.check_pattern_in_paths(action_patterns, validation_patterns):
                    results['by_paths'] = True
                    results['matched_patterns'].append("contextual:path")
        
        # Satisfied if ANY method found patterns
        results['satisfied'] = results['by_lines'] or results['by_paths'] or results['by_entirety']
        
        return results
    
    # Requirement checker functions using functional approach
    
    def check_r1(self, code_content: str, patterns: Dict) -> Dict:
        """Check R1: speedSet initialization - using constructor parsing"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        # Method 1: Check using constructor parsing (most reliable)
        if self.check_initialization_in_constructor('speedSet', 'null'):
            result['by_paths'] = True
            result['satisfied'] = True
            result['matched_patterns'].append('constructor:parsed')
            return result
        
        # Method 2: Flexible pattern matching
        code_patterns = patterns.get('R1', {}).get('code_patterns', {})
        for category, pattern_list in code_patterns.items():
            if isinstance(pattern_list, list):
                if self.check_pattern_flexible(pattern_list):
                    result['by_entirety'] = True
                    result['satisfied'] = True
                    result['matched_patterns'].append(f"{category}:flexible")
                    return result
        
        return result
    
    def check_r2(self, code_content: str, patterns: Dict) -> Dict:
        """Check R2: speedLimit initialization - using constructor parsing"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        # Method 1: Check using constructor parsing (most reliable)
        if self.check_initialization_in_constructor('speedLimit', 'null'):
            result['by_paths'] = True
            result['satisfied'] = True
            result['matched_patterns'].append('constructor:parsed')
            return result
        
        # Method 2: Flexible pattern matching
        code_patterns = patterns.get('R2', {}).get('code_patterns', {})
        for category, pattern_list in code_patterns.items():
            if isinstance(pattern_list, list):
                if self.check_pattern_flexible(pattern_list):
                    result['by_entirety'] = True
                    result['satisfied'] = True
                    result['matched_patterns'].append(f"{category}:flexible")
                    return result
        
        return result
    
    def check_r3(self, code_content: str, patterns: Dict) -> Dict:
        """Check R3: Accept positive values - flexible matching"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        code_patterns = patterns.get('R3', {}).get('code_patterns', {})
        
        # Check for method signature
        if 'method_signature' in code_patterns:
            if self.check_pattern_flexible(code_patterns['method_signature']):
                result['by_entirety'] = True
                result['matched_patterns'].append('method_signature:found')
        
        # Check for assignment
        if 'lines' in code_patterns:
            if self.check_pattern_flexible(code_patterns['lines']):
                result['by_lines'] = True
                result['matched_patterns'].append('assignment:found')
        
        # Satisfied if method exists (assignment is sufficient for R3)
        if result['by_lines'] or result['by_entirety']:
            result['satisfied'] = True
        
        return result
    
    def check_r4(self, code_content: str, patterns: Dict) -> Dict:
        """Check R4: Exception for invalid values - flexible matching"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        code_patterns = patterns.get('R4', {}).get('code_patterns', {})
        
        # Need BOTH validation check AND exception throw
        has_validation = False
        has_exception = False
        
        if 'validation_checks' in code_patterns:
            if self.check_pattern_flexible(code_patterns['validation_checks']):
                has_validation = True
                result['matched_patterns'].append('validation:found')
        
        if 'lines' in code_patterns:
            if self.check_pattern_flexible(code_patterns['lines']):
                has_exception = True
                result['matched_patterns'].append('exception:found')
        
        # Check if they appear in same context (path checking)
        if has_validation and has_exception:
            result['by_paths'] = True
            result['satisfied'] = True
        elif has_exception:
            # Exception found but maybe validation is implicit
            result['by_entirety'] = True
            result['satisfied'] = True
        
        return result
    
    def check_r5(self, code_content: str, patterns: Dict) -> Dict:
        """Check R5: Respect speed limit - flexible matching"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        code_patterns = patterns.get('R5', {}).get('code_patterns', {})
        
        # Check for limit validation
        has_null_check = False
        has_comparison = False
        
        if 'null_checks' in code_patterns:
            if self.check_pattern_flexible(code_patterns['null_checks']):
                has_null_check = True
                result['matched_patterns'].append('null_check:found')
        
        if 'lines' in code_patterns:
            if self.check_pattern_flexible(code_patterns['lines']):
                has_comparison = True
                result['matched_patterns'].append('comparison:found')
        
        # Check for combined validation
        if 'combined_validation' in code_patterns:
            if self.check_pattern_flexible(code_patterns['combined_validation']):
                result['by_paths'] = True
                result['satisfied'] = True
                result['matched_patterns'].append('combined:found')
                return result
        
        # Satisfied if has comparison logic
        if has_comparison or has_null_check:
            result['by_entirety'] = True
            result['satisfied'] = True
        
        return result
    
    def check_r6(self, code_content: str, patterns: Dict) -> Dict:
        """Check R6: Exception for exceeding limit - flexible matching"""
        result = {
            'by_lines': False,
            'by_paths': False,
            'by_entirety': False,
            'satisfied': False,
            'matched_patterns': []
        }
        
        code_patterns = patterns.get('R6', {}).get('code_patterns', {})
        
        # Need BOTH validation check AND exception throw
        has_validation = False
        has_exception = False
        
        if 'validation_checks' in code_patterns:
            if self.check_pattern_flexible(code_patterns['validation_checks']):
                has_validation = True
                result['matched_patterns'].append('validation:found')
        
        if 'lines' in code_patterns:
            if self.check_pattern_flexible(code_patterns['lines']):
                has_exception = True
                result['matched_patterns'].append('exception:found')
        
        # Check for combined
        if 'combined_checks' in code_patterns:
            if self.check_pattern_flexible(code_patterns['combined_checks']):
                result['by_paths'] = True
                result['satisfied'] = True
                result['matched_patterns'].append('combined:found')
                return result
        
        # Satisfied if has both pieces
        if has_validation and has_exception:
            result['by_paths'] = True
            result['satisfied'] = True
        elif has_exception:
            result['by_entirety'] = True
            result['satisfied'] = True
        
        return result
    
    def setup_environment(self, cruise_control_file: Path) -> Tuple[bool, str]:
        """Set up proper package structure for compilation"""
        try:
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            cruise_control_dest = package_dir / "CruiseControl.java"
            
            if cruise_control_file.resolve() != cruise_control_dest.resolve():
                shutil.copy(cruise_control_file, cruise_control_dest)
            
            # Copy exception files
            original_source_dir = cruise_control_file.parent
            for exception_file in original_source_dir.glob('*Exception.java'):
                exception_dest = package_dir / exception_file.name
                if exception_file.resolve() != exception_dest.resolve():
                    shutil.copy(exception_file, exception_dest)
            
            # Create Speedometer interface
            speedometer_dest = package_dir / "Speedometer.java"
            speedometer_code = """package es.upm.grise.profundizacion.cruiseControl;

public interface Speedometer {
\t
\tpublic int getCurrentSpeed();

}
"""
            speedometer_dest.write_text(speedometer_code)
            
            return True, "Environment setup successful"
            
        except Exception as e:
            return False, f"Setup error: {str(e)}"
    
    def compile_code(self) -> Tuple[bool, str]:
        """Compile the student's code"""
        try:
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            java_files = list(package_dir.glob("*.java"))
            
            if not java_files:
                return False, "No Java files found"
            
            relative_paths = []
            for f in java_files:
                try:
                    rel_path = f.relative_to(self.student_dir)
                    relative_paths.append(str(rel_path))
                except ValueError:
                    relative_paths.append(str(f))
            
            result = subprocess.run(
                ['javac'] + relative_paths,
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, f"Compilation failed:\n{result.stderr}"
            
            return True, "Compilation successful"
            
        except subprocess.TimeoutExpired:
            return False, "Compilation timeout (>30s)"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def create_test_file_from_patterns(self) -> Path:
        """Create test file dynamically from YAML patterns"""
        test_code_parts = [
            "package es.upm.grise.profundizacion.cruiseControl;",
            "",
            "public class GraderTest {",
            "    public static void main(String[] args) {",
            "        Speedometer speedometer = new Speedometer() {",
            "            public int getCurrentSpeed() { return 50; }",
            "        };",
            "        ",
            "        System.out.println(\"TESTING_START\");",
            ""
        ]
        
        # Generate test for each requirement from patterns
        for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            req_patterns = self.patterns.get(req, {}).get('test_patterns', {})
            test_code_parts.extend(self.generate_test_code(req, req_patterns))
        
        test_code_parts.extend([
            "        System.out.println(\"TESTING_END\");",
            "    }",
            "}"
        ])
        
        test_code = '\n'.join(test_code_parts)
        
        package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
        test_file = package_dir / "GraderTest.java"
        test_file.write_text(test_code)
        
        return test_file
    
    def generate_test_code(self, req: str, patterns: Dict) -> List[str]:
        """Generate test code for a requirement from patterns"""
        code = [f"        // Test {req} - {self.patterns.get(req, {}).get('description', '')}"]
        code.append("        try {")
        code.append(f"            CruiseControl cc{req[-1]} = new CruiseControl(speedometer);")
        
        # Add setup if needed (for R5, R6)
        setup = patterns.get('setup', [])
        if setup:
            for setup_step in setup:
                method = setup_step.get('method', '')
                value = setup_step.get('value', 0)
                code.append(f"            cc{req[-1]}.{method}({value});")
        
        # Determine test type
        expected_exception = patterns.get('expected_exception')
        
        if expected_exception:
            # Exception test
            test_values = patterns.get('test_values', [0])
            method_call = patterns.get('method_call', 'setSpeedSet')
            
            code.append(f"            cc{req[-1]}.{method_call}({test_values[0]});")
            code.append(f"            System.out.println(\"FAIL:{req}:NO_EXCEPTION\");")
            code.append("        } catch (Throwable e) {")
            
            exception_variants = patterns.get('exception_variants', [expected_exception])
            conditions = ' || '.join([f'e.getClass().getSimpleName().contains("{var}")' 
                                     for var in exception_variants])
            
            code.append(f"            if ({conditions}) {{")
            code.append(f"                System.out.println(\"PASS:{req}\");")
            code.append("            } else {")
            code.append(f"                System.out.println(\"FAIL:{req}:WRONG_EXCEPTION:\" + e.getClass().getSimpleName());")
            code.append("            }")
        else:
            # Value test
            check_method = patterns.get('check_method', '')
            expected_result = patterns.get('expected_result', '')
            
            if 'test_values' in patterns and patterns['test_values']:
                # Test with specific value
                test_value = patterns['test_values'][0]
                method_call = patterns.get('method_call', '')
                if method_call:
                    code.append(f"            cc{req[-1]}.{method_call}({test_value});")
                
                if expected_result == 'equals_input':
                    code.append(f"            if (cc{req[-1]}.{check_method} != null && cc{req[-1]}.{check_method} == {test_value}) {{")
                elif expected_result == 'null':
                    code.append(f"            if (cc{req[-1]}.{check_method} == null) {{")
                else:
                    code.append(f"            if (cc{req[-1]}.{check_method} == {expected_result}) {{")
            else:
                # Check for null
                code.append(f"            if (cc{req[-1]}.{check_method} == null) {{")
            
            code.append(f"                System.out.println(\"PASS:{req}\");")
            code.append("            } else {")
            code.append(f"                System.out.println(\"FAIL:{req}:NOT_CORRECT\");")
            code.append("            }")
            code.append("        } catch (Throwable e) {")
            code.append(f"            System.out.println(\"FAIL:{req}:EXCEPTION:\" + e.getClass().getSimpleName());")
        
        code.append("        }")
        code.append("")
        
        return code
    
    def run_tests(self) -> Tuple[bool, Dict]:
        """Run the generated tests"""
        try:
            test_file = self.create_test_file_from_patterns()
            
            # Compile test
            compile_result = subprocess.run(
                ['javac', '-cp', '.', str(test_file.relative_to(self.student_dir))],
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False, {'error': f'Test compilation failed: {compile_result.stderr}'}
            
            # Run test
            run_result = subprocess.run(
                ['java', '-cp', '.', 'es.upm.grise.profundizacion.cruiseControl.GraderTest'],
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = run_result.stdout
            
            # Parse results
            passed = []
            failed = []
            
            for line in output.split('\n'):
                if line.startswith('PASS:'):
                    req = line.split(':')[1]
                    passed.append(req)
                elif line.startswith('FAIL:'):
                    parts = line.split(':')
                    req = parts[1]
                    reason = ':'.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                    failed.append({'requirement': req, 'reason': reason})
            
            return True, {'passed': passed, 'failed': failed}
            
        except subprocess.TimeoutExpired:
            return False, {'error': 'Test execution timeout'}
        except Exception as e:
            return False, {'error': f'Test execution error: {str(e)}'}
    
    def cleanup(self):
        """Clean up generated files"""
        try:
            package_dir = self.student_dir / "es"
            if package_dir.exists():
                shutil.rmtree(package_dir)
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def log_unmatched_pattern(self, student_id: str, requirement: str, execution_passed: bool, pattern_matched: bool):
        """Log cases where execution passed but pattern didn't match"""
        if execution_passed and not pattern_matched:
            try:
                # Load existing pending patterns
                pending = {}
                if self.pending_file.exists():
                    with open(self.pending_file, 'r', encoding='utf-8') as f:
                        pending = yaml.safe_load(f) or {}
                
                # Create entry
                entry_id = f"{requirement}_candidate_{len(pending) + 1:03d}"
                pending[entry_id] = {
                    'student': student_id,
                    'requirement': requirement,
                    'code_snippet': self._extract_relevant_code(requirement),
                    'execution_result': 'PASSED',
                    'status': 'NEEDS_MANUAL_REVIEW',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'reason': 'Code passed execution but pattern not matched'
                }
                
                # Save
                with open(self.pending_file, 'w', encoding='utf-8') as f:
                    yaml.dump(pending, f, default_flow_style=False, allow_unicode=True)
                    
            except Exception as e:
                print(f"Warning: Could not log unmatched pattern: {e}")
    
    def _extract_relevant_code(self, requirement: str) -> str:
        """Extract relevant code snippet for a requirement"""
        # Simple extraction - get lines containing key patterns
        req_patterns = self.patterns.get(requirement, {}).get('code_patterns', {})
        relevant_lines = []
        
        for category, patterns in req_patterns.items():
            if isinstance(patterns, list):
                for pattern in patterns:
                    for line in self.code_lines:
                        if pattern in line and line.strip() not in relevant_lines:
                            relevant_lines.append(line.strip())
        
        return '; '.join(relevant_lines[:3]) if relevant_lines else "No matching code found"
    
    def grade_implementation(self, cruise_control_file: Path, student_id: str = "Unknown") -> Dict:
        """Main grading method combining pattern matching and execution"""
        try:
            # Load code for pattern matching
            if not self.load_code(cruise_control_file):
                return {
                    'success': False,
                    'error': 'Could not load code',
                    'requirements_satisfied': [],
                    'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                    'total_requirements': 6,
                    'requirements_found': 0,
                    'satisfaction_percentage': 0.0
                }
            
            # Pattern matching check
            pattern_results = {}
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                checker = self.requirement_checkers[req]
                pattern_results[req] = checker(self.code_content, self.patterns)
            
            # Setup and compile
            setup_success, setup_msg = self.setup_environment(cruise_control_file)
            if not setup_success:
                return {
                    'success': False,
                    'error': setup_msg,
                    'requirements_satisfied': [],
                    'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                    'total_requirements': 6,
                    'requirements_found': 0,
                    'satisfaction_percentage': 0.0
                }
            
            compile_success, compile_msg = self.compile_code()
            if not compile_success:
                self.cleanup()
                return {
                    'success': False,
                    'error': f'Compilation failed: {compile_msg}',
                    'requirements_satisfied': [],
                    'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                    'total_requirements': 6,
                    'requirements_found': 0,
                    'satisfaction_percentage': 0.0
                }
            
            # Run execution tests
            test_success, test_results = self.run_tests()
            
            # Cleanup
            self.cleanup()
            
            if not test_success:
                return {
                    'success': False,
                    'error': test_results.get('error', 'Test execution failed'),
                    'requirements_satisfied': [],
                    'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                    'total_requirements': 6,
                    'requirements_found': 0,
                    'satisfaction_percentage': 0.0
                }
            
            # Combine pattern and execution results
            passed_execution = test_results['passed']
            combined_passed = []
            
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                execution_passed = req in passed_execution
                pattern_matched = pattern_results[req]['satisfied']
                
                # Require BOTH pattern match AND execution pass
                # OR just execution pass (but log if pattern didn't match)
                if execution_passed:
                    combined_passed.append(req)
                    
                    # Log if pattern didn't match
                    if not pattern_matched:
                        self.log_unmatched_pattern(student_id, req, execution_passed, pattern_matched)
            
            missing = [r for r in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6'] if r not in combined_passed]
            
            # Build detailed results
            req_descriptions = {
                'R1': 'speedSet initializes to null',
                'R2': 'speedLimit initializes to null',
                'R3': 'setSpeedSet accepts positive values',
                'R4': 'Throws IncorrectSpeedSetException for zero/negative',
                'R5': 'speedSet respects speedLimit',
                'R6': 'Throws SpeedSetAboveSpeedLimitException when exceeding'
            }
            
            requirement_details = {}
            failed_details = {item['requirement']: item['reason'] for item in test_results.get('failed', [])}
            
            for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
                satisfied = req in combined_passed
                pattern_result = pattern_results[req]
                
                requirement_details[req] = {
                    'satisfied': satisfied,
                    'status': 'PASS' if satisfied else 'FAIL',
                    'description': req_descriptions.get(req, ''),
                    'pattern_matched': pattern_result['satisfied'],
                    'pattern_details': {
                        'by_lines': pattern_result['by_lines'],
                        'by_paths': pattern_result['by_paths'],
                        'by_entirety': pattern_result['by_entirety'],
                        'matched_patterns': pattern_result['matched_patterns']
                    },
                    'execution_passed': req in passed_execution,
                    'reason': 'Implementation correct' if satisfied else failed_details.get(req, 'Test failed')
                }
            
            return {
                'success': True,
                'requirements_satisfied': combined_passed,
                'requirements_missing': missing,
                'requirement_details': requirement_details,
                'total_requirements': 6,
                'requirements_found': len(combined_passed),
                'satisfaction_percentage': round((len(combined_passed) / 6) * 100, 2),
                'pattern_matching_used': True,
                'test_details': test_results.get('failed', [])
            }
            
        except Exception as e:
            self.cleanup()
            return {
                'success': False,
                'error': f'Grading error: {str(e)}',
                'requirements_satisfied': [],
                'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                'total_requirements': 6,
                'requirements_found': 0,
                'satisfaction_percentage': 0.0
            }


# Keep backward compatibility - alias to old class name
ExecutionBasedGrader = PatternBasedGrader


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python execution_grader.py <path_to_CruiseControl.java>")
        sys.exit(1)
    
    cruise_control_file = Path(sys.argv[1])
    student_dir = cruise_control_file.parent
    student_id = student_dir.name
    
    grader = PatternBasedGrader(student_dir)
    result = grader.grade_implementation(cruise_control_file, student_id)
    
    print("\n" + "=" * 70)
    print("PATTERN-BASED IMPLEMENTATION GRADING")
    print("=" * 70)
    print(f"\nRequirements Satisfied: {result['requirements_found']}/6 ({result['satisfaction_percentage']}%)")
    print(f"\nPassed: {', '.join(result['requirements_satisfied']) if result['requirements_satisfied'] else 'None'}")
    print(f"\nMissing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    if not result['success']:
        print(f"\nError: {result['error']}")


if __name__ == '__main__':
    main()
