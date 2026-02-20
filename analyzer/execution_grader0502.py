#!/usr/bin/env python3
"""
Execution-Based Implementation Grader
Based on the proven grading_system.py - actually compiles and runs student code

Based on ESP-CruiseControlSpecificationForExperimenters document
Only tests requirements R1-R6 (what students are given in the exam)
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, Tuple


class ExecutionBasedGrader:
    """Grades implementation by actually compiling and running the code"""
    
    # Requirement weights matching the ESP spec (R1-R6 only)
    # These are POINTS, not percentages (sum to 10.0)
    REQUIREMENT_WEIGHTS = {
        'R1': 1.67,   # speedSet initialization
        'R2': 1.67,   # speedLimit initialization  
        'R3': 1.67,   # setSpeedSet accepts positive values
        'R4': 1.67,   # Exception for zero/negative values
        'R5': 1.67,   # setSpeedSet respects speedLimit
        'R6': 1.65,   # Exception when exceeding speedLimit (sums to 10.0)
    }
    
    def __init__(self, student_dir: Path, speedometer_file: Path = None):
        self.student_dir = Path(student_dir)
        self.speedometer_file = speedometer_file
        
        # Use the Speedometer.java from project root if not provided
        if not self.speedometer_file:
            # Try to find Speedometer.java in the project root
            project_root = Path(__file__).parent.parent
            self.speedometer_file = project_root / "Speedometer.java"
            
            # If not found, look in common locations
            if not self.speedometer_file.exists():
                # Check if it's in the main grader directory
                alt_path = project_root.parent / "Speedometer.java"
                if alt_path.exists():
                    self.speedometer_file = alt_path
    
    def setup_environment(self, cruise_control_file: Path) -> Tuple[bool, str]:
        """Set up proper package structure for compilation"""
        try:
            # Create package directory structure
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Destination for CruiseControl.java
            cruise_control_dest = package_dir / "CruiseControl.java"
            
            # Only copy if source and destination are different
            if cruise_control_file.resolve() != cruise_control_dest.resolve():
                shutil.copy(cruise_control_file, cruise_control_dest)
            
            # Find the original source directory (where CruiseControl.java came from)
            original_source_dir = cruise_control_file.parent
            
            # Copy all exception files from the same directory (R4, R6 exceptions)
            exception_patterns = [
                '*Exception.java',
                'IncorrectSpeedSetException.java',
                'SpeedSetAboveSpeedLimitException.java',
            ]
            
            for pattern in exception_patterns:
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
        """Compile the student's code"""
        try:
            # First, compile all Java files in the package directory
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            
            if not package_dir.exists():
                return False, "Package directory not found"
            
            # Get all .java files in the package
            java_files = list(package_dir.glob('*.java'))
            
            if not java_files:
                return False, "No Java files found in package directory"
            
            # Create relative paths from student_dir
            relative_paths = []
            for f in java_files:
                try:
                    rel_path = f.relative_to(self.student_dir)
                    relative_paths.append(str(rel_path))
                except ValueError:
                    # If relative path fails, use absolute
                    relative_paths.append(str(f))
            
            # Compile all Java files at once
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
    
    def create_test_file(self) -> Path:
        """Create the test Java file - ONLY R1-R6 tests"""
        test_code = '''package es.upm.grise.profundizacion.cruiseControl;

public class GraderTest {
    public static void main(String[] args) {
        Speedometer speedometer = new Speedometer() {
            public int getCurrentSpeed() { return 50; }
        };
        
        System.out.println("TESTING_START");
        
        // Test R1 - speedSet initializes to null
        try {
            CruiseControl cc1 = new CruiseControl(speedometer);
            if (cc1.getSpeedSet() == null) {
                System.out.println("PASS:R1");
            } else {
                System.out.println("FAIL:R1:NOT_NULL");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R1:EXCEPTION:" + e.getClass().getSimpleName());
        }
        
        // Test R2 - speedLimit initializes to null
        try {
            CruiseControl cc2 = new CruiseControl(speedometer);
            if (cc2.getSpeedLimit() == null) {
                System.out.println("PASS:R2");
            } else {
                System.out.println("FAIL:R2:NOT_NULL");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R2:EXCEPTION:" + e.getClass().getSimpleName());
        }
        
        // Test R3 - Accepts positive value
        try {
            CruiseControl cc3 = new CruiseControl(speedometer);
            cc3.setSpeedSet(50);
            if (cc3.getSpeedSet() != null && cc3.getSpeedSet() == 50) {
                System.out.println("PASS:R3");
            } else {
                System.out.println("FAIL:R3:NOT_SET");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R3:EXCEPTION:" + e.getClass().getSimpleName());
        }
        
        // Test R4 - Throws exception for zero
        try {
            CruiseControl cc4 = new CruiseControl(speedometer);
            cc4.setSpeedSet(0);
            System.out.println("FAIL:R4:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("IncorrectSpeed")) {
                System.out.println("PASS:R4");
            } else {
                System.out.println("FAIL:R4:WRONG_EXCEPTION:" + e.getClass().getSimpleName());
            }
        }
        
        // Test R4b - Throws exception for negative
        try {
            CruiseControl cc4b = new CruiseControl(speedometer);
            cc4b.setSpeedSet(-10);
            System.out.println("FAIL:R4:NO_EXCEPTION_NEGATIVE");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("IncorrectSpeed")) {
                // Already counted in R4, don't print again
            } else {
                System.out.println("FAIL:R4:WRONG_EXCEPTION_NEGATIVE:" + e.getClass().getSimpleName());
            }
        }
        
        // Test R5 - speedSet respects speedLimit (below limit)
        try {
            CruiseControl cc5 = new CruiseControl(speedometer);
            cc5.setSpeedLimit(100);
            cc5.setSpeedSet(80);
            if (cc5.getSpeedSet() != null && cc5.getSpeedSet() == 80) {
                System.out.println("PASS:R5");
            } else {
                System.out.println("FAIL:R5:NOT_SET");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R5:EXCEPTION:" + e.getClass().getSimpleName());
        }
        
        // Test R6 - Throws exception when speedSet exceeds speedLimit
        try {
            CruiseControl cc6 = new CruiseControl(speedometer);
            cc6.setSpeedLimit(80);
            cc6.setSpeedSet(100);
            System.out.println("FAIL:R6:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("SpeedSetAboveSpeedLimit") ||
                e.getClass().getSimpleName().contains("AboveLimit")) {
                System.out.println("PASS:R6");
            } else {
                System.out.println("FAIL:R6:WRONG_EXCEPTION:" + e.getClass().getSimpleName());
            }
        }
        
        System.out.println("TESTING_END");
    }
}
'''
        
        package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
        test_file = package_dir / "GraderTest.java"
        test_file.write_text(test_code)
        return test_file
    
    def run_tests(self) -> Tuple[bool, Dict]:
        """Compile and run the test file"""
        try:
            # Create test file
            test_file = self.create_test_file()
            package_dir = self.student_dir / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
            
            # Compile all java files in package
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
            
            # Run test using fully qualified class name
            run_result = subprocess.run(
                ['java', '-cp', '.', 'es.upm.grise.profundizacion.cruiseControl.GraderTest'],
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            output = run_result.stdout
            passed_tests = []
            failed_tests = []
            
            for line in output.split('\n'):
                if line.startswith('PASS:'):
                    req = line.split(':')[1].strip()
                    if req not in passed_tests:  # Avoid duplicates
                        passed_tests.append(req)
                elif line.startswith('FAIL:'):
                    parts = line.split(':')
                    req = parts[1].strip()
                    reason = ':'.join(parts[2:]) if len(parts) > 2 else 'Failed'
                    failed_tests.append({'requirement': req, 'reason': reason})
            
            # Clean up
            test_file.unlink(missing_ok=True)
            (package_dir / 'GraderTest.class').unlink(missing_ok=True)
            
            return True, {
                'passed': passed_tests,
                'failed': failed_tests,
                'output': output
            }
            
        except subprocess.TimeoutExpired:
            return False, {'error': 'Test execution timeout'}
        except Exception as e:
            return False, {'error': f'Test execution error: {str(e)}'}
    
    def cleanup(self):
        """Clean up created directories and files"""
        try:
            # Remove package directory
            package_root = self.student_dir / "es"
            if package_root.exists():
                shutil.rmtree(package_root)
            
            # Remove any leftover files
            for pattern in ['*.class', 'GraderTest.java']:
                for file in self.student_dir.glob(pattern):
                    file.unlink(missing_ok=True)
                    
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def grade_implementation(self, cruise_control_file: Path) -> Dict:
        """Main grading method - returns full analysis (R1-R6 only)"""
        try:
            # Setup environment
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
            
            # Compile
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
            
            # Run tests
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
            
            # Process results - only R1-R6
            passed = test_results['passed']
            all_reqs = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
            missing = [r for r in all_reqs if r not in passed]
            
            # Requirement descriptions
            req_descriptions = {
                'R1': 'speedSet initializes to null',
                'R2': 'speedLimit initializes to null',
                'R3': 'setSpeedSet accepts positive values',
                'R4': 'Throws IncorrectSpeedSetException for zero/negative',
                'R5': 'speedSet respects speedLimit',
                'R6': 'Throws SpeedSetAboveSpeedLimitException when exceeding'
            }
            
            # Build detailed requirement breakdown
            requirement_details = {}
            failed_details = {item['requirement']: item['reason'] for item in test_results.get('failed', [])}
            
            for req in all_reqs:
                satisfied = req in passed
                requirement_details[req] = {
                    'satisfied': satisfied,
                    'status': 'PASS' if satisfied else 'FAIL',
                    'description': req_descriptions.get(req, ''),
                    'reason': 'Implementation correct' if satisfied else failed_details.get(req, 'Test failed')
                }
            
            return {
                'success': True,
                'requirements_satisfied': passed,
                'requirements_missing': missing,
                'requirement_details': requirement_details,
                'total_requirements': 6,
                'requirements_found': len(passed),
                'satisfaction_percentage': round((len(passed) / 6) * 100, 2),
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


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python execution_grader.py <path_to_CruiseControl.java>")
        print("\nThis grader tests only R1-R6 from ESP specification")
        sys.exit(1)
    
    cruise_control_file = Path(sys.argv[1])
    student_dir = cruise_control_file.parent
    
    grader = ExecutionBasedGrader(student_dir)
    result = grader.grade_implementation(cruise_control_file)
    
    print("\n" + "=" * 70)
    print("EXECUTION-BASED IMPLEMENTATION GRADING")
    print("=" * 70)
    print("Specification: ESP-CruiseControlSpecificationForExperimenters")
    print(f"\nRequirements Satisfied: {result['requirements_found']}/6 ({result['satisfaction_percentage']}%)")
    print(f"\nPassed: {', '.join(result['requirements_satisfied']) if result['requirements_satisfied'] else 'None'}")
    print(f"\nMissing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    if not result['success']:
        print(f"\nError: {result['error']}")


if __name__ == '__main__':
    main()
