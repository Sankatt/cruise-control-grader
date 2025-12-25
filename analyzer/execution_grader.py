#!/usr/bin/env python3
"""
Execution-Based Implementation Grader
Based on the proven grading_system.py - actually compiles and runs student code
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, Tuple


class ExecutionBasedGrader:
    """Grades implementation by actually compiling and running the code"""
    
    # Requirement weights matching the spec
    REQUIREMENT_WEIGHTS = {
        'R1': 2,   # speedSet initialization
        'R2': 2,   # speedLimit initialization  
        'R3': 3,   # setSpeedSet accepts positive values
        'R4': 3,   # Exception for zero/negative values
        'R5': 3,   # setSpeedSet respects speedLimit
        'R6': 3,   # Exception when exceeding speedLimit
        'R7': 2,   # setSpeedLimit accepts positive
        'R8': 2,   # setSpeedLimit exception for zero/negative
        'R9': 3,   # Cannot set speedLimit after speedSet
        # R10-R19 would be added when those methods are required
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
            
            # Copy all exception files from the same directory
            exception_patterns = [
                '*Exception.java',
                'IncorrectSpeedSetException.java',
                'SpeedSetAboveSpeedLimitException.java',
                'IncorrectSpeedLimitException.java',
                'CannotSetSpeedLimitException.java'
            ]
            
            for pattern in exception_patterns:
                for exception_file in original_source_dir.glob(pattern):
                    exception_dest = package_dir / exception_file.name
                    if exception_file.resolve() != exception_dest.resolve():
                        shutil.copy(exception_file, exception_dest)
            
            # Copy Speedometer.java to package directory
            if not self.speedometer_file.exists():
                return False, f"Speedometer.java not found at {self.speedometer_file}"
            
            speedometer_dest = package_dir / "Speedometer.java"
            
            # Only copy if not already there or different
            if not speedometer_dest.exists() or speedometer_dest.resolve() != self.speedometer_file.resolve():
                shutil.copy(self.speedometer_file, speedometer_dest)
            
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
        """Create the test Java file"""
        test_code = '''import es.upm.grise.profundizacion.cruiseControl.*;

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
                System.out.println("FAIL:R1");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R1:EXCEPTION");
        }
        
        // Test R2 - speedLimit initializes to null
        try {
            CruiseControl cc2 = new CruiseControl(speedometer);
            if (cc2.getSpeedLimit() == null) {
                System.out.println("PASS:R2");
            } else {
                System.out.println("FAIL:R2");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R2:EXCEPTION");
        }
        
        // Test R3 - Accepts positive value
        try {
            CruiseControl cc3 = new CruiseControl(speedometer);
            cc3.setSpeedSet(50);
            if (cc3.getSpeedSet() == 50) {
                System.out.println("PASS:R3");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R3:EXCEPTION");
        }
        
        // Test R4 - Throws exception for zero
        try {
            CruiseControl cc4 = new CruiseControl(speedometer);
            cc4.setSpeedSet(0);
            System.out.println("FAIL:R4:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("IncorrectSpeed")) {
                System.out.println("PASS:R4");
            }
        }
        
        // Test R5 - speedSet respects speedLimit (below limit)
        try {
            CruiseControl cc5 = new CruiseControl(speedometer);
            cc5.setSpeedLimit(100);
            cc5.setSpeedSet(80);
            if (cc5.getSpeedSet() == 80) {
                System.out.println("PASS:R5");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R5:EXCEPTION");
        }
        
        // Test R6 - Exception when exceeding speedLimit
        try {
            CruiseControl cc6 = new CruiseControl(speedometer);
            cc6.setSpeedLimit(100);
            cc6.setSpeedSet(120);
            System.out.println("FAIL:R6:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("SpeedSetAboveSpeedLimit") ||
                e.getClass().getSimpleName().contains("AboveLimit")) {
                System.out.println("PASS:R6");
            }
        }
        
        // Test R7 - setSpeedLimit accepts positive
        try {
            CruiseControl cc7 = new CruiseControl(speedometer);
            cc7.setSpeedLimit(100);
            if (cc7.getSpeedLimit() == 100) {
                System.out.println("PASS:R7");
            }
        } catch (Throwable e) {
            System.out.println("FAIL:R7:EXCEPTION");
        }
        
        // Test R8 - setSpeedLimit throws exception for zero/negative
        try {
            CruiseControl cc8 = new CruiseControl(speedometer);
            cc8.setSpeedLimit(0);
            System.out.println("FAIL:R8:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("IncorrectSpeedLimit") ||
                e.getClass().getSimpleName().contains("SpeedLimit")) {
                System.out.println("PASS:R8");
            }
        }
        
        // Test R9 - Cannot set speedLimit after speedSet
        try {
            CruiseControl cc9 = new CruiseControl(speedometer);
            cc9.setSpeedSet(80);
            cc9.setSpeedLimit(100);
            System.out.println("FAIL:R9:NO_EXCEPTION");
        } catch (Throwable e) {
            if (e.getClass().getSimpleName().contains("CannotSetSpeedLimit") ||
                e.getClass().getSimpleName().contains("Cannot")) {
                System.out.println("PASS:R9");
            }
        }
        
        System.out.println("TESTING_END");
    }
}
'''
        
        test_file = self.student_dir / "GraderTest.java"
        test_file.write_text(test_code)
        return test_file
    
    def run_tests(self) -> Tuple[bool, Dict]:
        """Compile and run the test file"""
        try:
            # Create test file
            test_file = self.create_test_file()
            
            # Compile test
            compile_result = subprocess.run(
                ['javac', '-cp', '.', str(test_file.name)],
                cwd=self.student_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False, {'error': f'Test compilation failed: {compile_result.stderr}'}
            
            # Run test
            run_result = subprocess.run(
                ['java', '-cp', '.', 'GraderTest'],
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
            (self.student_dir / 'GraderTest.class').unlink(missing_ok=True)
            
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
        """Main grading method - returns full analysis"""
        try:
            # Setup environment
            setup_success, setup_msg = self.setup_environment(cruise_control_file)
            if not setup_success:
                return {
                    'success': False,
                    'error': setup_msg,
                    'requirements_satisfied': [],
                    'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                    'total_requirements': 19,
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
                    'total_requirements': 19,
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
                    'total_requirements': 19,
                    'requirements_found': 0,
                    'satisfaction_percentage': 0.0
                }
            
            # Process results
            passed = test_results['passed']
            all_reqs = [f'R{i}' for i in range(1, 20)]
            missing = [r for r in all_reqs if r not in passed]
            
            return {
                'success': True,
                'requirements_satisfied': passed,
                'requirements_missing': missing,
                'total_requirements': 19,
                'requirements_found': len(passed),
                'satisfaction_percentage': round((len(passed) / 19) * 100, 2),
                'test_details': test_results.get('failed', [])
            }
            
        except Exception as e:
            self.cleanup()
            return {
                'success': False,
                'error': f'Grading error: {str(e)}',
                'requirements_satisfied': [],
                'requirements_missing': list(self.REQUIREMENT_WEIGHTS.keys()),
                'total_requirements': 19,
                'requirements_found': 0,
                'satisfaction_percentage': 0.0
            }


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python execution_grader.py <path_to_CruiseControl.java>")
        sys.exit(1)
    
    cruise_control_file = Path(sys.argv[1])
    student_dir = cruise_control_file.parent
    
    grader = ExecutionBasedGrader(student_dir)
    result = grader.grade_implementation(cruise_control_file)
    
    print("\n" + "=" * 70)
    print("EXECUTION-BASED IMPLEMENTATION GRADING")
    print("=" * 70)
    print(f"\nRequirements Satisfied: {result['requirements_found']}/19 ({result['satisfaction_percentage']}%)")
    print(f"\nPassed: {', '.join(result['requirements_satisfied']) if result['requirements_satisfied'] else 'None'}")
    print(f"\nMissing: {', '.join(result['requirements_missing']) if result['requirements_missing'] else 'None'}")
    
    if not result['success']:
        print(f"\nError: {result['error']}")


if __name__ == '__main__':
    main()
