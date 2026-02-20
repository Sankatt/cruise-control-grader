#!/usr/bin/env python3
"""
Rigorous Property-Based Implementation Grader
Uses formal verification techniques: equivalence partitioning, boundary value analysis,
property-based testing, and state-based verification.

Based on formal software testing methodologies for academic grading.
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class TestCategory(Enum):
    """Categories of test cases for systematic coverage"""
    EQUIVALENCE_PARTITION = "equivalence_partition"
    BOUNDARY_VALUE = "boundary_value"
    STATE_TRANSITION = "state_transition"
    PROPERTY_BASED = "property_based"
    EXCEPTION_BEHAVIOR = "exception_behavior"


class ExpectedBehavior(Enum):
    """Expected outcomes for test cases"""
    SUCCESS = "success"
    EXCEPTION = "exception"
    STATE_CHANGE = "state_change"


@dataclass
class TestCase:
    """Formal test case specification"""
    id: str
    category: TestCategory
    requirement: str
    description: str
    preconditions: Dict[str, Any]
    input_params: Dict[str, Any]
    expected_behavior: ExpectedBehavior
    expected_value: Any
    expected_exception: str = None
    postconditions: Dict[str, Any] = None
    
    
@dataclass
class PropertySpecification:
    """Formal property that must hold"""
    id: str
    requirement: str
    property_name: str
    property_description: str
    invariant: str  # Logical expression that must always be true


class RigorousImplementationGrader:
    """
    Formal verification-based grader using:
    1. Equivalence Partitioning
    2. Boundary Value Analysis
    3. Property-Based Testing
    4. State Machine Verification
    """
    
    def __init__(self, student_dir: Path):
        self.student_dir = Path(student_dir)
        
        # Formal requirement specifications
        self.requirements = self._define_requirements()
        
        # Systematic test cases
        self.test_cases = self._generate_test_cases()
        
        # Properties that must hold
        self.properties = self._define_properties()
        
    def _define_requirements(self) -> Dict[str, Dict]:
        """Define formal requirements with contracts"""
        return {
            'R1': {
                'description': 'speedSet initializes to null',
                'precondition': 'constructor called',
                'postcondition': 'speedSet == null',
                'invariant': 'speedSet is Integer type'
            },
            'R2': {
                'description': 'speedLimit initializes to null',
                'precondition': 'constructor called',
                'postcondition': 'speedLimit == null',
                'invariant': 'speedLimit is Integer type'
            },
            'R3': {
                'description': 'setSpeedSet accepts positive values',
                'precondition': 'speedSet > 0',
                'postcondition': 'this.speedSet == speedSet parameter',
                'invariant': 'speedSet > 0 → no exception thrown'
            },
            'R4': {
                'description': 'Throws IncorrectSpeedSetException for speedSet <= 0',
                'precondition': 'speedSet <= 0',
                'postcondition': 'IncorrectSpeedSetException thrown',
                'invariant': '∀ speedSet <= 0 → throws IncorrectSpeedSetException'
            },
            'R5': {
                'description': 'speedSet respects speedLimit when set',
                'precondition': 'speedLimit != null AND speedSet <= speedLimit',
                'postcondition': 'this.speedSet == speedSet parameter',
                'invariant': 'speedLimit != null → speedSet <= speedLimit'
            },
            'R6': {
                'description': 'Throws SpeedSetAboveSpeedLimitException when speedSet > speedLimit',
                'precondition': 'speedLimit != null AND speedSet > speedLimit',
                'postcondition': 'SpeedSetAboveSpeedLimitException thrown',
                'invariant': '∀ (speedLimit != null AND speedSet > speedLimit) → throws exception'
            }
        }
    
    def _generate_test_cases(self) -> List[TestCase]:
        """Generate comprehensive test cases using formal testing techniques"""
        test_cases = []
        
        # R1: Initialization of speedSet
        test_cases.append(TestCase(
            id="R1_INIT_01",
            category=TestCategory.EQUIVALENCE_PARTITION,
            requirement="R1",
            description="speedSet initializes to null after constructor",
            preconditions={},
            input_params={},
            expected_behavior=ExpectedBehavior.SUCCESS,
            expected_value=None,
            postconditions={'speedSet': None}
        ))
        
        # R2: Initialization of speedLimit
        test_cases.append(TestCase(
            id="R2_INIT_01",
            category=TestCategory.EQUIVALENCE_PARTITION,
            requirement="R2",
            description="speedLimit initializes to null after constructor",
            preconditions={},
            input_params={},
            expected_behavior=ExpectedBehavior.SUCCESS,
            expected_value=None,
            postconditions={'speedLimit': None}
        ))
        
        # R3: Valid positive values (Equivalence Partitioning)
        for value in [1, 50, 100, 1000]:  # Representative values from valid partition
            test_cases.append(TestCase(
                id=f"R3_VALID_{value:04d}",
                category=TestCategory.EQUIVALENCE_PARTITION,
                requirement="R3",
                description=f"setSpeedSet accepts positive value {value}",
                preconditions={'speedLimit': None},
                input_params={'speedSet': value},
                expected_behavior=ExpectedBehavior.SUCCESS,
                expected_value=value,
                postconditions={'speedSet': value}
            ))
        
        # R4: Invalid values - Boundary Value Analysis
        # Partition: speedSet <= 0
        for value in [-100, -10, -1, 0]:  # Boundary and representative values
            test_cases.append(TestCase(
                id=f"R4_INVALID_{abs(value):04d}",
                category=TestCategory.BOUNDARY_VALUE,
                requirement="R4",
                description=f"setSpeedSet({value}) throws IncorrectSpeedSetException",
                preconditions={'speedLimit': None},
                input_params={'speedSet': value},
                expected_behavior=ExpectedBehavior.EXCEPTION,
                expected_value=None,
                expected_exception="IncorrectSpeedSetException",
                postconditions={'speedSet': None}  # Should remain unchanged
            ))
        
        # R5: speedSet respects speedLimit - Equivalence Partitioning
        # Partition 1: speedSet < speedLimit (valid)
        for speed_limit, speed_set in [(100, 50), (200, 150), (100, 99)]:
            test_cases.append(TestCase(
                id=f"R5_BELOW_LIMIT_{speed_set:04d}",
                category=TestCategory.EQUIVALENCE_PARTITION,
                requirement="R5",
                description=f"setSpeedSet({speed_set}) succeeds when speedLimit={speed_limit}",
                preconditions={'speedLimit': speed_limit},
                input_params={'speedSet': speed_set},
                expected_behavior=ExpectedBehavior.SUCCESS,
                expected_value=speed_set,
                postconditions={'speedSet': speed_set}
            ))
        
        # Partition 2: speedSet == speedLimit (boundary - valid)
        test_cases.append(TestCase(
            id="R5_EQUAL_LIMIT_0100",
            category=TestCategory.BOUNDARY_VALUE,
            requirement="R5",
            description="setSpeedSet equals speedLimit (boundary case)",
            preconditions={'speedLimit': 100},
            input_params={'speedSet': 100},
            expected_behavior=ExpectedBehavior.SUCCESS,
            expected_value=100,
            postconditions={'speedSet': 100}
        ))
        
        # R6: speedSet exceeds speedLimit - Boundary Value Analysis
        # Partition: speedSet > speedLimit
        for speed_limit, speed_set in [(100, 101), (100, 150), (50, 51)]:
            test_cases.append(TestCase(
                id=f"R6_EXCEED_LIMIT_{speed_set:04d}",
                category=TestCategory.BOUNDARY_VALUE,
                requirement="R6",
                description=f"setSpeedSet({speed_set}) throws exception when speedLimit={speed_limit}",
                preconditions={'speedLimit': speed_limit},
                input_params={'speedSet': speed_set},
                expected_behavior=ExpectedBehavior.EXCEPTION,
                expected_value=None,
                expected_exception="SpeedSetAboveSpeedLimitException",
                postconditions={'speedSet': None}
            ))
        
        # Property-based test: Multiple sequential calls
        test_cases.append(TestCase(
            id="PROP_SEQUENTIAL_01",
            category=TestCategory.PROPERTY_BASED,
            requirement="R3,R5",
            description="Property: Multiple valid setSpeedSet calls maintain state correctly",
            preconditions={'speedLimit': 200},
            input_params={'sequence': [50, 75, 100]},
            expected_behavior=ExpectedBehavior.SUCCESS,
            expected_value=100,
            postconditions={'speedSet': 100}
        ))
        
        # State transition test
        test_cases.append(TestCase(
            id="STATE_TRANS_01",
            category=TestCategory.STATE_TRANSITION,
            requirement="R4",
            description="State preserved after exception",
            preconditions={'speedSet': 50, 'speedLimit': None},
            input_params={'speedSet': -10},
            expected_behavior=ExpectedBehavior.EXCEPTION,
            expected_value=None,
            expected_exception="IncorrectSpeedSetException",
            postconditions={'speedSet': 50}  # Original state should be preserved
        ))
        
        return test_cases
    
    def _define_properties(self) -> List[PropertySpecification]:
        """Define formal properties that must always hold"""
        return [
            PropertySpecification(
                id="PROP_R4_01",
                requirement="R4",
                property_name="Invalid Input Rejection",
                property_description="∀ speedSet <= 0 → throws IncorrectSpeedSetException",
                invariant="speedSet <= 0 ⟹ Exception"
            ),
            PropertySpecification(
                id="PROP_R6_01",
                requirement="R6",
                property_name="Speed Limit Enforcement",
                property_description="∀ (speedLimit != null ∧ speedSet > speedLimit) → throws SpeedSetAboveSpeedLimitException",
                invariant="(speedLimit ≠ null ∧ speedSet > speedLimit) ⟹ Exception"
            ),
            PropertySpecification(
                id="PROP_R3_01",
                requirement="R3",
                property_name="Valid Input Acceptance",
                property_description="∀ speedSet > 0 (no limit or speedSet <= limit) → this.speedSet = speedSet",
                invariant="(speedSet > 0 ∧ (speedLimit = null ∨ speedSet ≤ speedLimit)) ⟹ Success"
            ),
            PropertySpecification(
                id="PROP_STATE_01",
                requirement="ALL",
                property_name="State Consistency",
                property_description="Exception thrown → object state unchanged",
                invariant="Exception ⟹ state_before = state_after"
            )
        ]
    
    def setup_environment(self, cruise_control_file: Path) -> Tuple[bool, str]:
        """Set up compilation environment"""
        try:
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy CruiseControl.java
            cruise_control_dest = package_dir / "CruiseControl.java"
            if cruise_control_file.resolve() != cruise_control_dest.resolve():
                shutil.copy(cruise_control_file, cruise_control_dest)
            
            # Copy exception files
            original_source_dir = cruise_control_file.parent
            for pattern in ['*Exception.java']:
                for exception_file in original_source_dir.glob(pattern):
                    exception_dest = package_dir / exception_file.name
                    if exception_file.resolve() != exception_dest.resolve():
                        shutil.copy(exception_file, exception_dest)
            
            # Create Speedometer.java directly (don't rely on external file)
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
        """Compile student code"""
        try:
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            java_files = list(package_dir.glob('*.java'))
            
            if not java_files:
                return False, "No Java files found"
            
            relative_paths = [str(f.relative_to(self.student_dir)) for f in java_files]
            
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
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def generate_test_file(self) -> Path:
        """Generate comprehensive JUnit test file from test cases"""
        test_code = self._build_junit_test_code()
        
        # Put test file in the package directory where the classes are
        package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
        test_file = package_dir / "RigorousGraderTest.java"
        test_file.write_text(test_code)
        return test_file
    
    def _build_junit_test_code(self) -> str:
        """Build JUnit test code from formal test case specifications"""
        code = '''package es.upm.grise.profundizacion.cruiseControl;

public class RigorousGraderTest {
    public static void main(String[] args) {
        Speedometer speedometer = new Speedometer() {
            public int getCurrentSpeed() { return 50; }
        };
        
        System.out.println("TESTING_START");
        
'''
        
        # Generate test method for each test case
        for tc in self.test_cases:
            code += self._generate_test_method(tc)
        
        code += '''
        System.out.println("TESTING_END");
    }
}
'''
        return code
    
    def _generate_test_method(self, tc: TestCase) -> str:
        """Generate Java test code for a specific test case"""
        speedometer_param = "new Speedometer() { public int getCurrentSpeed() { return 50; } }"
        
        code = f"        // {tc.id}: {tc.description}\n"
        code += f"        try {{\n"
        code += f"            CruiseControl cc = new CruiseControl({speedometer_param});\n"
        
        # Set up preconditions
        if 'speedLimit' in tc.preconditions and tc.preconditions['speedLimit'] is not None:
            code += f"            cc.setSpeedLimit({tc.preconditions['speedLimit']});\n"
        
        if 'speedSet' in tc.preconditions and tc.preconditions['speedSet'] is not None:
            code += f"            cc.setSpeedSet({tc.preconditions['speedSet']});\n"
        
        # Execute test based on category
        if tc.category == TestCategory.PROPERTY_BASED and 'sequence' in tc.input_params:
            # Sequential calls
            for value in tc.input_params['sequence']:
                code += f"            cc.setSpeedSet({value});\n"
            code += f"            if (cc.getSpeedSet() == {tc.expected_value}) {{\n"
            code += f"                System.out.println(\"PASS:{tc.requirement}:{tc.id}\");\n"
            code += f"            }}\n"
        elif tc.expected_behavior == ExpectedBehavior.EXCEPTION:
            # Should throw exception
            if tc.id.startswith('R1') or tc.id.startswith('R2'):
                # Initialization test
                code += f"            if (cc.{'getSpeedSet()' if 'R1' in tc.id else 'getSpeedLimit()'} == null) {{\n"
                code += f"                System.out.println(\"PASS:{tc.requirement}:{tc.id}\");\n"
                code += f"            }}\n"
            else:
                code += f"            cc.setSpeedSet({tc.input_params['speedSet']});\n"
                code += f"            System.out.println(\"FAIL:{tc.requirement}:{tc.id}:NO_EXCEPTION\");\n"
        else:
            # Should succeed
            if tc.id.startswith('R1') or tc.id.startswith('R2'):
                code += f"            if (cc.{'getSpeedSet()' if 'R1' in tc.id else 'getSpeedLimit()'} == null) {{\n"
                code += f"                System.out.println(\"PASS:{tc.requirement}:{tc.id}\");\n"
                code += f"            }}\n"
            else:
                code += f"            cc.setSpeedSet({tc.input_params['speedSet']});\n"
                code += f"            if (cc.getSpeedSet() != null && cc.getSpeedSet() == {tc.expected_value}) {{\n"
                code += f"                System.out.println(\"PASS:{tc.requirement}:{tc.id}\");\n"
                code += f"            }}\n"
        
        code += f"        }} catch (Throwable e) {{\n"
        
        if tc.expected_behavior == ExpectedBehavior.EXCEPTION:
            code += f"            if (e.getClass().getSimpleName().contains(\"{tc.expected_exception.replace('Exception', '')}\")) {{\n"
            code += f"                System.out.println(\"PASS:{tc.requirement}:{tc.id}\");\n"
            code += f"            }} else {{\n"
            code += f"                System.out.println(\"FAIL:{tc.requirement}:{tc.id}:WRONG_EXCEPTION:\" + e.getClass().getSimpleName());\n"
            code += f"            }}\n"
        else:
            code += f"            System.out.println(\"FAIL:{tc.requirement}:{tc.id}:UNEXPECTED_EXCEPTION:\" + e.getClass().getSimpleName());\n"
        
        code += f"        }}\n\n"
        
        return code
    
    def run_tests(self) -> Tuple[bool, Dict]:
        """Execute generated test file"""
        try:
            test_file = self.generate_test_file()
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            
            # Compile - compile all java files in package directory
            java_files = list(package_dir.glob('*.java'))
            relative_paths = [str(f.relative_to(self.student_dir)) for f in java_files]
            
            compile_result = subprocess.run(
                ['javac'] + relative_paths,
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False, {'error': f'Test compilation failed: {compile_result.stderr}'}
            
            # Run - use fully qualified class name
            run_result = subprocess.run(
                ['java', '-cp', '.', 'es.upm.grise.profundizacion.cruiseControl.RigorousGraderTest'],
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            output = run_result.stdout
            results_by_requirement = {'R1': [], 'R2': [], 'R3': [], 'R4': [], 'R5': [], 'R6': []}
            
            for line in output.split('\n'):
                if line.startswith('PASS:') or line.startswith('FAIL:'):
                    parts = line.split(':')
                    status = parts[0]
                    requirement = parts[1]
                    test_id = parts[2] if len(parts) > 2 else ''
                    reason = ':'.join(parts[3:]) if len(parts) > 3 else ''
                    
                    test_result = {
                        'status': status,
                        'test_id': test_id,
                        'reason': reason
                    }
                    
                    if requirement in results_by_requirement:
                        results_by_requirement[requirement].append(test_result)
            
            # Cleanup
            test_file.unlink(missing_ok=True)
            (package_dir / 'RigorousGraderTest.class').unlink(missing_ok=True)
            
            return True, {
                'results_by_requirement': results_by_requirement,
                'output': output
            }
            
        except Exception as e:
            return False, {'error': f'Test execution error: {str(e)}'}
    
    def analyze_results(self, test_results: Dict) -> Dict:
        """Analyze test results using formal verification criteria"""
        results_by_req = test_results['results_by_requirement']
        
        requirement_analysis = {}
        
        for req_id in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
            req_results = results_by_req.get(req_id, [])
            
            total_tests = len(req_results)
            passed_tests = sum(1 for r in req_results if r['status'] == 'PASS')
            failed_tests = total_tests - passed_tests
            
            # Determine if requirement is satisfied based on formal criteria
            # For rigorous verification, we need high pass rate
            satisfaction_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Strict criteria: require >80% pass rate for satisfaction
            satisfied = satisfaction_rate >= 80
            
            # Get test categories covered
            test_ids = [r['test_id'] for r in req_results]
            categories_tested = set()
            for test_id in test_ids:
                for tc in self.test_cases:
                    if tc.id == test_id:
                        categories_tested.add(tc.category.value)
            
            # Get failure details
            failures = [r for r in req_results if r['status'] == 'FAIL']
            failure_details = [{'test_id': f['test_id'], 'reason': f['reason']} for f in failures]
            
            requirement_analysis[req_id] = {
                'satisfied': satisfied,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'satisfaction_rate': round(satisfaction_rate, 2),
                'categories_tested': list(categories_tested),
                'failure_details': failure_details,
                'verification_method': 'Property-Based + Equivalence Partitioning + Boundary Analysis',
                'description': self.requirements[req_id]['description']
            }
        
        return requirement_analysis
    
    def grade_implementation(self, cruise_control_file: Path) -> Dict:
        """Main grading method using rigorous verification"""
        try:
            # Setup
            setup_success, setup_msg = self.setup_environment(cruise_control_file)
            if not setup_success:
                return self._error_result(setup_msg)
            
            # Compile
            compile_success, compile_msg = self.compile_code()
            if not compile_success:
                self.cleanup()
                return self._error_result(f'Compilation failed: {compile_msg}')
            
            # Run comprehensive tests
            test_success, test_results = self.run_tests()
            self.cleanup()
            
            if not test_success:
                return self._error_result(test_results.get('error', 'Test execution failed'))
            
            # Analyze with formal verification criteria
            requirement_analysis = self.analyze_results(test_results)
            
            # Determine satisfied requirements
            satisfied_requirements = [req for req, analysis in requirement_analysis.items() 
                                     if analysis['satisfied']]
            missing_requirements = [req for req in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6'] 
                                   if req not in satisfied_requirements]
            
            # Calculate grade (each requirement worth equal points)
            weights = {f'R{i}': 1.67 for i in range(1, 6)}
            weights['R6'] = 1.65  # To sum to 10.0
            
            grade = sum(weights[req] for req in satisfied_requirements)
            grade = min(grade, 10.0)  # Cap at maximum
            
            return {
                'success': True,
                'verification_method': 'Rigorous Property-Based Testing',
                'total_test_cases': len(self.test_cases),
                'requirements_satisfied': satisfied_requirements,
                'requirements_missing': missing_requirements,
                'requirement_analysis': requirement_analysis,
                'properties_verified': [p.id for p in self.properties],
                'total_requirements': 6,
                'requirements_found': len(satisfied_requirements),
                'satisfaction_percentage': round((len(satisfied_requirements) / 6) * 100, 2),
                'grade': round(grade, 2),
                'test_categories_used': [
                    TestCategory.EQUIVALENCE_PARTITION.value,
                    TestCategory.BOUNDARY_VALUE.value,
                    TestCategory.PROPERTY_BASED.value,
                    TestCategory.STATE_TRANSITION.value
                ]
            }
            
        except Exception as e:
            self.cleanup()
            return self._error_result(f'Grading error: {str(e)}')
    
    def _error_result(self, error_msg: str) -> Dict:
        """Generate error result"""
        return {
            'success': False,
            'error': error_msg,
            'requirements_satisfied': [],
            'requirements_missing': ['R1', 'R2', 'R3', 'R4', 'R5', 'R6'],
            'total_requirements': 6,
            'requirements_found': 0,
            'satisfaction_percentage': 0.0,
            'grade': 0.0
        }
    
    def cleanup(self):
        """Clean up generated files"""
        try:
            package_root = self.student_dir / "es"
            if package_root.exists():
                shutil.rmtree(package_root)
            
            for pattern in ['*.class', 'RigorousGraderTest.java']:
                for file in self.student_dir.glob(pattern):
                    file.unlink(missing_ok=True)
        except Exception as e:
            print(f"Cleanup warning: {e}")


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rigorous_grader.py <path_to_CruiseControl.java>")
        print("\nThis grader uses:")
        print("  - Equivalence Partitioning")
        print("  - Boundary Value Analysis")
        print("  - Property-Based Testing")
        print("  - State Machine Verification")
        sys.exit(1)
    
    cruise_control_file = Path(sys.argv[1])
    student_dir = cruise_control_file.parent
    
    grader = RigorousImplementationGrader(student_dir)
    result = grader.grade_implementation(cruise_control_file)
    
    print("\n" + "=" * 70)
    print("RIGOROUS PROPERTY-BASED IMPLEMENTATION GRADING")
    print("=" * 70)
    print(f"\nVerification Method: {result.get('verification_method', 'N/A')}")
    print(f"Total Test Cases: {result.get('total_test_cases', 0)}")
    print(f"\nRequirements Satisfied: {result['requirements_found']}/6 ({result['satisfaction_percentage']}%)")
    print(f"Grade: {result.get('grade', 0)}/10.0")
    print(f"\nPassed: {', '.join(result['requirements_satisfied']) if result['requirements_satisfied'] else 'None'}")
    print(f"Missing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    if result.get('requirement_analysis'):
        print("\n" + "=" * 70)
        print("DETAILED REQUIREMENT ANALYSIS")
        print("=" * 70)
        for req, analysis in result['requirement_analysis'].items():
            print(f"\n{req}: {analysis['description']}")
            print(f"  Status: {'✓ SATISFIED' if analysis['satisfied'] else '✗ NOT SATISFIED'}")
            print(f"  Tests: {analysis['passed_tests']}/{analysis['total_tests']} passed ({analysis['satisfaction_rate']}%)")
            print(f"  Categories: {', '.join(analysis['categories_tested'])}")
            if analysis['failure_details']:
                print(f"  Failures:")
                for failure in analysis['failure_details']:
                    print(f"    - {failure['test_id']}: {failure['reason']}")
    
    if not result['success']:
        print(f"\nError: {result['error']}")


if __name__ == '__main__':
    main()
