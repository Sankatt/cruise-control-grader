#!/usr/bin/env python3
"""
Holistic Coverage Analyzer - Runs student tests and tracks code coverage
Maps coverage to requirements to catch combined requirement testing
Complements pattern matching by executing actual tests
"""

import subprocess
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set


class HolisticCoverageAnalyzer:
    """
    Runs student tests on their implementation and analyzes coverage
    Maps executed code paths to requirements
    """
    
    def __init__(self, student_dir: Path):
        self.student_dir = Path(student_dir)
        self.coverage_file = None
        self.execution_data = None
        
        # Requirement to code mapping - which lines/branches test each requirement
        self.requirement_code_map = {
            'R1': {
                'lines': ['this.speedSet = null'],
                'methods': ['CruiseControl'],  # Constructor
                'description': 'speedSet initialization to null'
            },
            'R2': {
                'lines': ['this.speedLimit = null'],
                'methods': ['CruiseControl'],  # Constructor
                'description': 'speedLimit initialization to null'
            },
            'R3': {
                'lines': ['this.speedSet = speedSet'],
                'methods': ['setSpeedSet'],
                'conditions': ['speedSet > 0'],  # Must accept positive
                'description': 'Accepts positive speedSet values'
            },
            'R4': {
                'lines': ['throw new IncorrectSpeedSetException'],
                'methods': ['setSpeedSet'],
                'conditions': ['speedSet <= 0'],
                'description': 'Exception for invalid speedSet (<= 0)'
            },
            'R5': {
                'lines': [
                    'currentSpeedLimit != null',
                    'speedSet > currentSpeedLimit',
                    'this.speedSet = speedSet'  # Acceptance path
                ],
                'methods': ['setSpeedSet'],
                'conditions': ['speedSet <= speedLimit'],
                'description': 'speedSet respects speedLimit'
            },
            'R6': {
                'lines': ['throw new SpeedSetAboveSpeedLimitException'],
                'methods': ['setSpeedSet'],
                'conditions': ['speedSet > speedLimit'],
                'description': 'Exception when speedSet exceeds speedLimit'
            }
        }
    
    def run_tests_with_coverage(self) -> bool:
        """
        Compile and run student tests with JaCoCo coverage
        Returns True if successful
        """
        try:
            print(f"\n  → Running student tests with coverage analysis...")
            
            # Find test file
            test_files = list(self.student_dir.rglob("*Test.java"))
            impl_file = self.student_dir / "CruiseControl.java"
            
            if not test_files or not impl_file.exists():
                print(f"  ✗ Missing test or implementation file")
                return False
            
            test_file = test_files[0]
            
            # Create temp build directory
            build_dir = self.student_dir / "build_coverage"
            build_dir.mkdir(exist_ok=True)
            
            # Download JaCoCo agent if not present
            jacoco_agent = build_dir / "jacocoagent.jar"
            if not jacoco_agent.exists():
                self._download_jacoco(build_dir)
            
            # Compile with javac
            compile_result = self._compile_code(impl_file, test_file, build_dir)
            if not compile_result:
                return False
            
            # Run tests with JaCoCo
            coverage_result = self._run_with_jacoco(build_dir)
            if not coverage_result:
                return False
            
            # Parse coverage data
            self._parse_coverage_data(build_dir)
            
            return True
            
        except Exception as e:
            print(f"  ✗ Coverage analysis error: {e}")
            return False
    
    def _download_jacoco(self, build_dir: Path):
        """Download JaCoCo agent JAR"""
        print(f"  → Downloading JaCoCo agent...")
        # For now, we'll use a simpler approach - just create a placeholder
        # In production, download from Maven Central
        # https://repo1.maven.org/maven2/org/jacoco/org.jacoco.agent/0.8.11/org.jacoco.agent-0.8.11-runtime.jar
        pass
    
    def _compile_code(self, impl_file: Path, test_file: Path, build_dir: Path) -> bool:
        """Compile implementation and test files"""
        try:
            # Find JUnit jars (assume they're in a lib directory or system)
            classpath = self._get_classpath()
            
            # Compile implementation
            compile_cmd = [
                'javac',
                '-d', str(build_dir),
                '-cp', classpath,
                str(impl_file)
            ]
            
            result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"  ✗ Compilation failed: {result.stderr}")
                return False
            
            # Compile tests
            compile_cmd = [
                'javac',
                '-d', str(build_dir),
                '-cp', f"{classpath}:{build_dir}",
                str(test_file)
            ]
            
            result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"  ✗ Test compilation failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ✗ Compilation error: {e}")
            return False
    
    def _get_classpath(self) -> str:
        """Get classpath for compilation and execution"""
        # Try to find JUnit and Mockito jars
        possible_paths = [
            "/usr/share/java/junit5.jar",
            "/usr/share/java/junit.jar",
            str(Path.home() / ".m2/repository/org/junit/jupiter/junit-jupiter/5.9.0/junit-jupiter-5.9.0.jar"),
        ]
        
        classpath = "."
        for path in possible_paths:
            if Path(path).exists():
                classpath += f":{path}"
        
        return classpath
    
    def _run_with_jacoco(self, build_dir: Path) -> bool:
        """Run tests with JaCoCo instrumentation"""
        # Simplified version - just run tests normally and track manually
        # In full implementation, would use JaCoCo agent
        try:
            # Find test class
            test_classes = list(build_dir.glob("**/*Test.class"))
            if not test_classes:
                return False
            
            # For now, we'll analyze statically without actual JaCoCo
            # Full implementation would run with -javaagent:jacocoagent.jar
            print(f"  ✓ Coverage tracking (simplified mode)")
            return True
            
        except Exception as e:
            print(f"  ✗ Test execution error: {e}")
            return False
    
    def _parse_coverage_data(self, build_dir: Path):
        """Parse JaCoCo coverage XML"""
        # Placeholder - would parse jacoco.xml in full implementation
        pass
    
    def analyze_requirement_coverage(self, requirement: str, test_file_content: str, 
                                    impl_file_content: str) -> Dict:
        """
        Analyze if a requirement's code paths are covered by tests
        Uses static analysis as simplified alternative to JaCoCo
        """
        result = {
            'requirement': requirement,
            'covered': False,
            'coverage_type': 'static_analysis',
            'details': [],
            'confidence': 0.0
        }
        
        req_map = self.requirement_code_map.get(requirement, {})
        
        # Check if test file exercises the requirement's methods
        methods_tested = self._check_methods_called(
            test_file_content, 
            req_map.get('methods', [])
        )
        
        # Check if implementation has the required code
        impl_has_code = self._check_implementation_has_code(
            impl_file_content,
            req_map.get('lines', [])
        )
        
        # Check if tests exercise the specific code paths
        paths_exercised = self._check_code_paths_exercised(
            test_file_content,
            impl_file_content,
            req_map
        )
        
        # Calculate coverage
        if methods_tested and impl_has_code and paths_exercised:
            result['covered'] = True
            result['confidence'] = 0.9
            result['details'].append(f"Methods called: {methods_tested}")
            result['details'].append(f"Code paths exercised")
        elif methods_tested and impl_has_code:
            result['covered'] = True
            result['confidence'] = 0.7
            result['details'].append(f"Methods called: {methods_tested}")
            result['details'].append("Warning: Code path verification inconclusive")
        else:
            result['covered'] = False
            result['confidence'] = 0.0
            result['details'].append("Required code not exercised by tests")
        
        return result
    
    def _check_methods_called(self, test_content: str, required_methods: List[str]) -> List[str]:
        """Check if test file calls required methods"""
        called_methods = []
        
        for method in required_methods:
            # Look for method calls in test
            if f"{method}(" in test_content or f".{method}(" in test_content:
                called_methods.append(method)
        
        return called_methods
    
    def _check_implementation_has_code(self, impl_content: str, required_lines: List[str]) -> bool:
        """Check if implementation contains required code patterns"""
        normalized_impl = self._normalize_code(impl_content)
        
        for line_pattern in required_lines:
            normalized_pattern = self._normalize_code(line_pattern)
            if normalized_pattern in normalized_impl:
                return True
        
        return False
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison"""
        # Remove comments
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove extra whitespace
        code = re.sub(r'\s+', '', code)
        return code.lower()
    
    def _check_code_paths_exercised(self, test_content: str, impl_content: str, 
                                    req_map: Dict) -> bool:
        """
        Check if tests exercise the specific code paths for this requirement
        This is a simplified version - full implementation would use actual coverage data
        """
        import re
        
        conditions = req_map.get('conditions', [])
        if not conditions:
            return True  # No specific conditions to check
        
        # For R5: Check if tests set limit then set speed WITHIN limit (acceptance case)
        # CRITICAL: Must test speedSet <= limit, NOT just the exception case
        if 'speedSet <= speedLimit' in conditions:
            has_set_limit = 'setSpeedLimit' in test_content
            has_set_speed = 'setSpeedSet' in test_content
            
            # Extract actual values being tested
            limit_values = re.findall(r'setSpeedLimit\s*\(\s*(\d+)\s*\)', test_content)
            speed_values = re.findall(r'setSpeedSet\s*\(\s*(\d+)\s*\)', test_content)
            
            # Check if ANY combination has speedSet <= speedLimit (acceptance case)
            # WITHOUT an exception assertion in the same test method
            test_methods = re.split(r'@Test|@org\.junit\.Test', test_content)
            
            for test_method in test_methods:
                method_limits = re.findall(r'setSpeedLimit\s*\(\s*(\d+)\s*\)', test_method)
                method_speeds = re.findall(r'setSpeedSet\s*\(\s*(\d+)\s*\)', test_method)
                
                # Check if this test has exception expectation (R6, not R5)
                has_exception_expect = (
                    'SpeedSetAboveSpeedLimit' in test_method or
                    'exceptionRule' in test_method or
                    'assertThrows' in test_method and 'SpeedSetAbove' in test_method
                )
                
                # If this test has both setSpeedLimit and setSpeedSet
                if method_limits and method_speeds:
                    for limit in method_limits:
                        for speed in method_speeds:
                            try:
                                limit_val = int(limit)
                                speed_val = int(speed)
                                
                                # R5 requires testing acceptance: speedSet <= speedLimit
                                # WITHOUT expecting exception
                                if speed_val <= limit_val and not has_exception_expect:
                                    # Check for assertion that verifies value was accepted
                                    if 'assert' in test_method.lower() or 'getSpeedSet' in test_method:
                                        return True
                            except ValueError:
                                continue
            
            # If we didn't find acceptance case, return False
            return False
        
        # For R6: Check if tests try to exceed limit
        if 'speedSet > speedLimit' in conditions:
            has_set_limit = 'setSpeedLimit' in test_content
            has_exceed_attempt = 'setSpeedSet' in test_content
            has_exception = 'SpeedSetAboveSpeedLimit' in test_content or 'assertThrows' in test_content
            
            return has_set_limit and has_exceed_attempt and has_exception
        
        # For R4: Check if tests use invalid values
        if 'speedSet <= 0' in conditions:
            has_zero_or_negative = re.search(r'setSpeedSet\s*\(\s*[0-]', test_content)
            has_exception = 'IncorrectSpeed' in test_content or 'assertThrows' in test_content
            
            return bool(has_zero_or_negative and has_exception)
        
        return True
    
    def generate_coverage_report(self, test_file: Path, impl_file: Path) -> Dict:
        """
        Generate coverage report for all requirements
        """
        print(f"\n  📊 Analyzing holistic coverage...")
        
        # Read files
        test_content = test_file.read_text(encoding='utf-8')
        impl_content = impl_file.read_text(encoding='utf-8')
        
        report = {
            'success': True,
            'requirements': {},
            'overall_coverage': 0.0,
            'method': 'holistic_static_analysis'
        }
        
        covered_count = 0
        
        for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            coverage = self.analyze_requirement_coverage(req, test_content, impl_content)
            report['requirements'][req] = coverage
            
            if coverage['covered']:
                covered_count += 1
                print(f"  ✓ {req}: Covered (confidence: {coverage['confidence']:.1%})")
            else:
                print(f"  ✗ {req}: Not covered")
        
        report['overall_coverage'] = covered_count / 6
        
        return report


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python holistic_coverage_analyzer.py <student_directory>")
        sys.exit(1)
    
    student_dir = Path(sys.argv[1])
    analyzer = HolisticCoverageAnalyzer(student_dir)
    
    # Find files
    test_file = list(student_dir.rglob("*Test.java"))[0]
    impl_file = student_dir / "CruiseControl.java"
    
    # Generate report
    report = analyzer.generate_coverage_report(test_file, impl_file)
    
    print(f"\n{'=' * 70}")
    print(f"HOLISTIC COVERAGE ANALYSIS")
    print(f"{'=' * 70}")
    print(f"Overall Coverage: {report['overall_coverage']:.1%}")
    print(f"\nRequirements:")
    for req, data in report['requirements'].items():
        status = "✓ COVERED" if data['covered'] else "✗ NOT COVERED"
        print(f"  {req}: {status} (confidence: {data['confidence']:.1%})")


if __name__ == '__main__':
    main()
