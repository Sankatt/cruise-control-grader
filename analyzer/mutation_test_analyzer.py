#!/usr/bin/env python3
"""
Mutation Test Analyzer - Execution-based grading of student CruiseControlTest.java

Strategy:
  1. Compile student's test file against a KNOWN-CORRECT reference CruiseControl.java
  2. Run the tests — if they pass, the test is valid and tests the right behaviour
  3. Then run the same tests against MUTANT implementations (one bug per requirement)
     to verify each test can actually CATCH the bug it's supposed to catch.

Mutant implementations (one per requirement):
  M1: speedSet initializes to 0 instead of null          → R1 test should FAIL
  M2: speedLimit initializes to 0 instead of null        → R2 test should FAIL
  M3: setSpeedSet never assigns this.speedSet            → R3 test should FAIL
  M4: no check for speedSet <= 0 (no exception thrown)   → R4 test should FAIL
  M5: ignores speedLimit (always accepts speedSet)       → R5 test should FAIL (only if limit is set)
  M6: no SpeedSetAboveSpeedLimitException thrown         → R6 test should FAIL

Result logic:
  - Tests pass on reference     → test is structurally valid
  - Tests fail on mutant Mx     → test covers requirement Rx  (mutation killed)
  - Tests pass on mutant Mx     → test does NOT cover Rx     (mutant survived)
"""

import os
import re
import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Dict, Tuple, Optional, List


REQUIREMENT_WEIGHT = 10.0 / 6

# ---------------------------------------------------------------------------
# Reference implementation (perfect, correct)
# ---------------------------------------------------------------------------
REFERENCE_IMPL = '''package es.upm.grise.profundizacion.cruiseControl;

public class CruiseControl {

    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;

    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = null;
    }

    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) {
            throw new IncorrectSpeedSetException();
        }
        if (this.speedLimit != null && speedSet > this.speedLimit) {
            throw new SpeedSetAboveSpeedLimitException();
        }
        this.speedSet = speedSet;
    }

    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
'''

# ---------------------------------------------------------------------------
# Mutant implementations — one intentional bug per requirement
# ---------------------------------------------------------------------------
MUTANTS = {
    "R1": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = 0;      // BUG: should be null
        this.speedLimit = null;
    }
    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) throw new IncorrectSpeedSetException();
        if (this.speedLimit != null && speedSet > this.speedLimit) throw new SpeedSetAboveSpeedLimitException();
        this.speedSet = speedSet;
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
    "R2": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = 0;    // BUG: should be null
    }
    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) throw new IncorrectSpeedSetException();
        if (this.speedLimit != null && speedSet > this.speedLimit) throw new SpeedSetAboveSpeedLimitException();
        this.speedSet = speedSet;
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
    "R3": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = null;
    }
    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) throw new IncorrectSpeedSetException();
        if (this.speedLimit != null && speedSet > this.speedLimit) throw new SpeedSetAboveSpeedLimitException();
        // BUG: never assigns this.speedSet
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
    "R4": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = null;
    }
    public void setSpeedSet(int speedSet) {
        // BUG: no check for <= 0, never throws IncorrectSpeedSetException
        if (this.speedLimit != null && speedSet > this.speedLimit) throw new SpeedSetAboveSpeedLimitException();
        this.speedSet = speedSet;
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
    "R5": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = null;
    }
    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) throw new IncorrectSpeedSetException();
        // BUG: always throws exception when speedLimit is set, even if within limit
        if (this.speedLimit != null) throw new SpeedSetAboveSpeedLimitException();
        this.speedSet = speedSet;
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
    "R6": '''package es.upm.grise.profundizacion.cruiseControl;
public class CruiseControl {
    @SuppressWarnings("unused")
    private Speedometer speedometer;
    private Integer speedSet;
    private Integer speedLimit;
    public CruiseControl(Speedometer speedometer) {
        this.speedometer = speedometer;
        this.speedSet = null;
        this.speedLimit = null;
    }
    public void setSpeedSet(int speedSet) {
        if (speedSet <= 0) throw new IncorrectSpeedSetException();
        // BUG: no check against speedLimit, never throws SpeedSetAboveSpeedLimitException
        this.speedSet = speedSet;
    }
    public Integer getSpeedLimit() { return speedLimit; }
    public void setSpeedLimit(Integer speedLimit) { this.speedLimit = speedLimit; }
    public Integer getSpeedSet() { return speedSet; }
}
''',
}

# ---------------------------------------------------------------------------
# Exception stubs (in case student doesn't provide them)
# ---------------------------------------------------------------------------
EXCEPTION_STUBS = {
    "IncorrectSpeedSetException": '''package es.upm.grise.profundizacion.cruiseControl;
public class IncorrectSpeedSetException extends RuntimeException {
    public IncorrectSpeedSetException() { super(); }
    public IncorrectSpeedSetException(String msg) { super(msg); }
    public IncorrectSpeedSetException(String msg, Throwable cause) { super(msg, cause); }
    public IncorrectSpeedSetException(Throwable cause) { super(cause); }
}
''',
    "SpeedSetAboveSpeedLimitException": '''package es.upm.grise.profundizacion.cruiseControl;
public class SpeedSetAboveSpeedLimitException extends RuntimeException {
    public SpeedSetAboveSpeedLimitException() { super(); }
    public SpeedSetAboveSpeedLimitException(String msg) { super(msg); }
    public SpeedSetAboveSpeedLimitException(String msg, Throwable cause) { super(msg, cause); }
    public SpeedSetAboveSpeedLimitException(Throwable cause) { super(cause); }
}
''',
    "IncorrectSpeedException": '''package es.upm.grise.profundizacion.cruiseControl;
public class IncorrectSpeedException extends RuntimeException {
    public IncorrectSpeedException() { super(); }
    public IncorrectSpeedException(String msg) { super(msg); }
    public IncorrectSpeedException(String msg, Throwable cause) { super(msg, cause); }
    public IncorrectSpeedException(Throwable cause) { super(cause); }
}
''',
}

SPEEDOMETER_STUB = '''package es.upm.grise.profundizacion.cruiseControl;
public interface Speedometer {
    public int getCurrentSpeed();
}
'''



class MutationTestAnalyzer:

    def __init__(self, java_home: Optional[str] = None):
        self.java_home = java_home
        self._javac = self._find_tool("javac")
        self._java  = self._find_tool("java")
        self._junit_jar = self._find_junit_jar()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyze(self, test_file_path: str, student_src_dir: Optional[str] = None) -> dict:
        """
        Analyze a student's CruiseControlTest.java using execution + mutation.
        student_src_dir: path to the student's main/java source directory
                         (used to pick up their own exception classes if present)
        """
        test_path = Path(test_file_path)
        if not test_path.exists():
            return self._error_result(f"Test file not found: {test_file_path}")

        if not self._javac or not self._java:
            return self._error_result(
                "javac/java not found on PATH. Install JDK and ensure it is on PATH."
            )

        workdir = Path(tempfile.mkdtemp(prefix="rigorous_test_"))
        try:
            return self._run_analysis(test_path, student_src_dir, workdir)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    def _run_analysis(self, test_path: Path, student_src_dir: Optional[str],
                      workdir: Path) -> dict:

        pkg_dir = workdir / "src" / "es" / "upm" / "grise" / "profundizacion" / "cruiseControl"
        pkg_dir.mkdir(parents=True)

        # Read actual package from student test file to get correct directory
        test_src = test_path.read_text(encoding="utf-8", errors="replace")
        pkg_match = re.search(r"^package\s+([\w.]+)\s*;", test_src, re.MULTILINE)
        if pkg_match:
            test_pkg_path = pkg_match.group(1).replace(".", "/")
            test_pkg_dir = workdir / "src" / test_pkg_path
        else:
            test_pkg_dir = workdir / "src" / "es" / "upm" / "grise" / "profunduzacion" / "cruiseController"
        test_pkg_dir.mkdir(parents=True, exist_ok=True)

        # Find student project root (directory containing pom.xml)
        student_project_dir: Optional[Path] = None
        search_start = Path(student_src_dir) if student_src_dir else test_path.parent
        for p in [search_start] + list(search_start.parents)[:6]:
            if (p / "pom.xml").exists():
                student_project_dir = p
                break

        # Copy student test file — strip Mockito so it compiles without Mockito jars
        raw_test = test_path.read_text(encoding="utf-8", errors="replace")
        cleaned_test = self._strip_mockito(raw_test)
        (test_pkg_dir / "CruiseControlTest.java").write_text(cleaned_test, encoding="utf-8")

        # DEBUG: save stripped test so we can inspect it
        import tempfile, os
        _student_name = Path(student_src_dir).parts[-1] if student_src_dir else test_path.name
        debug_path = Path(tempfile.gettempdir()) / f"stripped_{_student_name}.java"
        debug_path.write_text(cleaned_test, encoding="utf-8")
        print(f"        [debug] Stripped test written to: {debug_path}")

        # Write stubs
        (pkg_dir / "Speedometer.java").write_text(SPEEDOMETER_STUB)
        for name, code in EXCEPTION_STUBS.items():
            (pkg_dir / f"{name}.java").write_text(code)

        # Do NOT copy student exception files — our stubs support all constructor
        # variants (no-arg, String, RuntimeException, Exception) so they work
        # with any student implementation. Student files may be more restrictive.

        # Step 1: compile + run against REFERENCE
        (pkg_dir / "CruiseControl.java").write_text(REFERENCE_IMPL)
        ref_compile_ok, ref_compile_err = self._compile(workdir, student_project_dir)
        if not ref_compile_ok:
            # Extract just the error reason (after "error:"), skip file path lines
            # Show unique error types
            err_lines = []
            for line in ref_compile_err.splitlines():
                if "error:" in line:
                    part = line[line.index("error:"):].strip()
                    if part not in err_lines:
                        err_lines.append(part)
                if len(err_lines) >= 8:
                    break
            short_err = " | ".join(err_lines)
            # DEBUG: print full compile error
            print(f"        [debug] FULL COMPILE ERROR:\n{ref_compile_err[:2000]}")
            return self._error_result(f"Compile failed: {short_err}")

        ref_results = self._run_tests(workdir, student_project_dir)
        total_tests = ref_results.get("total", 0)
        ref_passed  = ref_results.get("passed", 0)

        if total_tests == 0:
            print(f"        [debug] ref_results raw: {ref_results}")
            return self._error_result("No tests found or all tests errored on reference.")

        # Step 2: run against each MUTANT
        requirement_results = {}
        for req, mutant_code in MUTANTS.items():
            (pkg_dir / "CruiseControl.java").write_text(mutant_code)
            mut_compile_ok, _ = self._compile(workdir, student_project_dir)
            if not mut_compile_ok:
                requirement_results[req] = {
                    "tested": False,
                    "status": "MUTANT_COMPILE_ERROR",
                    "details": "Mutant did not compile",
                }
                continue

            mut_results  = self._run_tests(workdir, student_project_dir)
            mut_passed   = mut_results.get("passed", 0)
            mut_failed   = mut_results.get("failed", 0) + mut_results.get("errors", 0)

            killed = mut_failed > 0

            requirement_results[req] = {
                "tested": killed,
                "status": "KILLED" if killed else "SURVIVED",
                "mutant_tests_failed": mut_failed,
                "mutant_tests_passed": mut_passed,
                "details": (
                    f"Mutant killed — {mut_failed} test(s) failed" if killed
                    else "Mutant survived — no test caught this bug"
                ),
            }

        covered = [r for r, v in requirement_results.items() if v["tested"]]
        missing  = [r for r, v in requirement_results.items() if not v["tested"]]
        grade    = round(min(len(covered) * REQUIREMENT_WEIGHT, 10.0), 2)

        return {
            "success": True,
            "grade": grade,
            "requirements_covered": covered,
            "requirements_missing": missing,
            "requirement_details": requirement_results,
            "total_test_methods": total_tests,
            "requirements_found": len(covered),
            "coverage_percentage": round(len(covered) / 6 * 100, 2),
            "reference_tests_passed": ref_passed,
            "reference_tests_total": total_tests,
            "analyzer": "MutationTestAnalyzer-v1",
        }

    # ------------------------------------------------------------------
    # Mockito stripping — replace Mockito with simple stubs before compile
    # ------------------------------------------------------------------

    def _strip_mockito(self, java_source: str) -> str:
        """
        Strip Mockito from test file so it compiles with only JUnit jars.
        Handles: @Mock, Mockito.mock(), when().thenReturn(), @ExtendWith, etc.
        Also rewrites the class to not use Mockito at all.
        """
        lines = java_source.split("\n")
        result = []
        skip_next = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip blank annotation carry-over
            if skip_next and stripped == "":
                skip_next = False
                result.append(line)
                continue
            skip_next = False

            # Remove Mockito/MockitoExtension imports
            if re.search(r"^import\s+(org\.mockito|org\.junit\.jupiter\.api\.extension)", stripped):
                result.append("// STRIPPED: " + stripped)
                continue

            # Remove @ExtendWith(MockitoExtension.class) annotation
            if re.search(r"@ExtendWith\s*\(", stripped) and "Mockito" in stripped:
                result.append("// STRIPPED: " + stripped)
                continue

            # Remove @Mock / @InjectMocks / @Spy / @Captor wherever they appear.
            # Handles: alone on a line, Windows \r endings, inline before field.
            if re.search(r"@(Mock|InjectMocks|Spy|Captor)\b", stripped):
                if re.match(r"@(Mock|InjectMocks|Spy|Captor)[\s\r]*$", stripped):
                    result.append("// STRIPPED: " + stripped.rstrip())
                    continue
                # Inline before field — remove annotation, keep the rest
                line = re.sub(r"@(Mock|InjectMocks|Spy|Captor)\s*", "", line)

            # Remove MockitoAnnotations.openMocks/initMocks lines
            if re.search(r"MockitoAnnotations\s*\.\s*(openMocks|initMocks)", stripped):
                result.append("// STRIPPED: " + stripped)
                continue

            # Remove when(...).thenReturn(...) — may span multiple forms
            if re.search(r"when\s*\(", stripped) and "thenReturn" in stripped:
                result.append("// STRIPPED: " + stripped)
                continue

            # Replace Mockito.mock(X.class) or mock(X.class) with anonymous stub
            # Handle: Speedometer x = Mockito.mock(Speedometer.class);
            # Handle: Speedometer x = mock(Speedometer.class);
            def replace_mock(m):
                cls = m.group(1)
                if cls == "Speedometer":
                    return (f"= new {cls}() {{ "
                            f"public int getCurrentSpeed() {{ return 50; }} }}")
                else:
                    return f"= null /* mock removed */"
            
            line = re.sub(
                r"=\s*(?:Mockito\s*\.\s*)?mock\s*\(\s*(\w+)\.class\s*\)",
                replace_mock, line
            )

            # Remove standalone mock() calls not in assignment
            line = re.sub(
                r"(?:Mockito\s*\.\s*)?mock\s*\(\s*\w+\.class\s*\)\s*;",
                "// mock removed;", line
            )

            result.append(line)

        return "\n".join(result)

    # ------------------------------------------------------------------
    # Compile helpers
    # ------------------------------------------------------------------

    def _compile(self, workdir: Path, student_project_dir: Optional[Path] = None) -> Tuple[bool, str]:
        """Compile all .java files under workdir/src using our jar cache."""
        src_dir = workdir / "src"
        java_files = list(src_dir.rglob("*.java"))
        if not java_files:
            return False, "No .java files found"

        jars = self._collect_dependency_jars(student_project_dir)
        sep = ";" if os.name == "nt" else ":"
        cp = sep.join(jars) if jars else "."

        cmd = [
            self._javac,
            "-cp", cp,
            "-d", str(workdir / "classes"),
            "-encoding", "UTF-8",
        ] + [str(f) for f in java_files]

        (workdir / "classes").mkdir(exist_ok=True)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, ""
            return False, result.stderr + result.stdout
        except subprocess.TimeoutExpired:
            return False, "Compile timed out"
        except Exception as e:
            return False, str(e)

    def _run_tests(self, workdir: Path, student_project_dir: Optional[Path] = None) -> dict:
        """
        Run compiled tests using JUnit Platform Console Standalone.
        Returns dict with keys: total, passed, failed, errors.
        """
        classes_dir = workdir / "classes"
        jars = self._collect_dependency_jars(student_project_dir)
        sep = ";" if os.name == "nt" else ":"

        # Find the console standalone jar
        standalone_jar = None
        for j in jars:
            if "console-standalone" in j:
                standalone_jar = j
                break

        if not standalone_jar:
            # Fall back to JUnit 4 runner
            return self._run_tests_junit4(workdir, jars, classes_dir)

        cp = sep.join([str(classes_dir)] + jars)

        cmd = [
            self._java,
            "-cp", cp,
            "org.junit.platform.console.ConsoleLauncher",
            "--scan-classpath",
            f"--classpath={classes_dir}",
            "--disable-banner",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(workdir),
            )
            output = result.stdout + result.stderr
            return self._parse_junit_output(output)
        except subprocess.TimeoutExpired:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 1}
        except Exception as e:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 1}

    def _run_tests_junit4(self, workdir: Path, jars: List[str], classes_dir: Path) -> dict:
        """Fallback: run tests with JUnit 4 runner."""
        sep = ";" if os.name == "nt" else ":"
        cp = sep.join([str(classes_dir)] + jars)

        # Find the test class name by scanning for @Test annotations
        test_class = self._find_test_class(classes_dir)
        if not test_class:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 0}

        print(f"        [debug] class_name={test_class}")

        cmd = [
            self._java,
            "-cp", cp,
            "org.junit.runner.JUnitCore",
            test_class,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(workdir),
            )
            output = result.stdout + result.stderr
            print(f"        [debug] JUnit4 out: {output[:200]}")
            return self._parse_junit_output(output)
        except subprocess.TimeoutExpired:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 1}
        except Exception as e:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 1}

    def _find_test_class(self, classes_dir: Path) -> Optional[str]:
        """Find the fully qualified name of the test class from compiled .class files."""
        for class_file in classes_dir.rglob("*Test.class"):
            # Convert path to fully qualified class name
            rel = class_file.relative_to(classes_dir)
            parts = list(rel.parts)
            parts[-1] = parts[-1].replace(".class", "")
            return ".".join(parts)
        # Fallback: any class with Test in name
        for class_file in classes_dir.rglob("*.class"):
            if "Test" in class_file.name and "$" not in class_file.name:
                rel = class_file.relative_to(classes_dir)
                parts = list(rel.parts)
                parts[-1] = parts[-1].replace(".class", "")
                return ".".join(parts)
        return None

    def _parse_junit_output(self, output: str) -> dict:
        """
        Parse JUnit console output to extract pass/fail counts.
        Handles both JUnit 4 and JUnit Platform output formats.
        """
        total = passed = failed = errors = 0

        # JUnit Platform format: "[         3 tests successful ]"
        m = re.search(r"(\d+) tests? successful", output)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) tests? failed", output)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+) tests? aborted", output)
        if m:
            errors += int(m.group(1))

        # JUnit 4 format: "Tests run: X, Failures: Y"
        m4 = re.search(r"Tests run:\s*(\d+).*?Failures:\s*(\d+)", output)
        if m4:
            total = int(m4.group(1))
            failed = int(m4.group(2))
            passed = total - failed

        # JUnit 4 OK format: "OK (N tests)"
        m_ok = re.search(r"OK \((\d+) tests?\)", output)
        if m_ok:
            total = int(m_ok.group(1))
            passed = total
            failed = 0

        if total == 0:
            total = passed + failed + errors

        return {"total": total, "passed": passed, "failed": failed, "errors": errors}

    def _collect_dependency_jars(self, student_project_dir: Optional[Path] = None) -> List[str]:
        """Return list of jar paths for compilation and test execution."""
        m2 = self._find_m2_repository(student_project_dir)
        if m2:
            print(f"        [classpath] .m2 not found locally — downloading from Maven Central...")
        else:
            print(f"        [classpath] .m2 not found locally — downloading from Maven Central...")
        return self._download_jars_if_needed()

    def _find_m2_repository(self, student_project_dir: Optional[Path] = None) -> Optional[Path]:
        """Find the Maven local repository, trying multiple strategies."""
        candidates = []

        # 1. USERPROFILE (most reliable on Windows)
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            candidates.append(Path(userprofile) / ".m2" / "repository")

        # 2. Standard Python home
        candidates.append(Path(os.path.expanduser("~")) / ".m2" / "repository")
        candidates.append(Path.home() / ".m2" / "repository")

        # 3. Derive from APPDATA/LOCALAPPDATA
        for env_var in ("APPDATA", "LOCALAPPDATA"):
            val = os.environ.get(env_var, "")
            if val:
                candidates.append(Path(val).parent.parent / ".m2" / "repository")

        # 4. Scan C:/Users
        users_dir = Path("C:/Users")
        if users_dir.exists():
            try:
                for user_dir in users_dir.iterdir():
                    if user_dir.is_dir():
                        candidate = user_dir / ".m2" / "repository"
                        if candidate.exists():
                            candidates.append(candidate)
            except PermissionError:
                pass

        for c in candidates:
            if c.exists():
                return c
        return None

    def _get_jar_cache_dir(self) -> Path:
        """Get/create a local jar cache directory next to this script."""
        cache_dir = Path(__file__).parent / "_jar_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def _download_jars_if_needed(self) -> List[str]:
        """
        Download required JUnit/Mockito jars from Maven Central into a local
        cache folder next to mutation_test_analyzer.py.
        Only downloads if not already cached.
        """
        cache_dir = self._get_jar_cache_dir()

        # Artifacts to download: (groupId, artifactId, version)
        artifacts = [
            ("org.junit.jupiter",  "junit-jupiter-api",              "5.10.2"),
            ("org.junit.jupiter",  "junit-jupiter-engine",           "5.10.2"),
            ("org.junit.jupiter",  "junit-jupiter-params",           "5.10.2"),
            ("org.junit.platform", "junit-platform-commons",         "1.10.2"),
            ("org.junit.platform", "junit-platform-engine",          "1.10.2"),
            ("org.junit.platform", "junit-platform-launcher",        "1.10.2"),
            ("org.junit.platform", "junit-platform-console-standalone", "1.10.2"),
            ("org.junit.vintage",  "junit-vintage-engine",           "5.10.2"),
            ("junit",              "junit",                          "4.13.2"),
            ("org.hamcrest",       "hamcrest-core",                  "1.3"),
            ("org.mockito",        "mockito-core",                   "5.11.0"),
            ("org.mockito",        "mockito-junit-jupiter",          "5.11.0"),
            ("net.bytebuddy",      "byte-buddy",                     "1.14.12"),
            ("net.bytebuddy",      "byte-buddy-agent",               "1.14.12"),
            ("org.objenesis",      "objenesis",                      "3.3"),
            ("org.opentest4j",     "opentest4j",                     "1.3.0"),
        ]

        base_url = "https://repo1.maven.org/maven2"
        jars = []
        downloaded_any = False

        for group_id, artifact_id, version in artifacts:
            jar_name = f"{artifact_id}-{version}.jar"
            local_path = cache_dir / jar_name

            if local_path.exists():
                jars.append(str(local_path))
                continue

            # Build Maven Central URL
            group_path = group_id.replace(".", "/")
            url = f"{base_url}/{group_path}/{artifact_id}/{version}/{jar_name}"

            try:
                if not downloaded_any:
                    print(f"        [classpath] Downloading jars from Maven Central (one-time setup)...")
                    downloaded_any = True
                print(f"        [classpath] Downloading {jar_name}...")
                urllib.request.urlretrieve(url, local_path)
                jars.append(str(local_path))
            except Exception as e:
                print(f"        [classpath] WARNING: Could not download {jar_name}: {e}")

        if downloaded_any:
            print(f"        [classpath] Downloaded {len(jars)} jars to {cache_dir}")
        else:
            print(f"        [classpath] Using {len(jars)} cached jars from {cache_dir}")

        return jars

        m2 = None
        for candidate in m2_candidates:
            if candidate.exists():
                m2 = candidate
                break
        if m2 is None:
            tried = [str(c) for c in m2_candidates]
            print(f"        [classpath] Tried: {tried}")

        # Also check student pom.xml for exact versions first
        all_jars = []
        if student_project_dir:
            pom_jars = self._jars_from_pom(Path(student_project_dir) / "pom.xml")
            all_jars.extend(pom_jars)

        if all_jars:
            print(f"        [classpath] Found {len(all_jars)} jars via pom.xml")
            return list(set(all_jars))

        if not m2:
            print("        [classpath] WARNING: .m2 repository not found!")
            return []

        print(f"        [classpath] Searching .m2 at: {m2}")

        # Artifact names to search for (glob by filename in entire .m2)
        artifact_prefixes = [
            "junit-jupiter-api",
            "junit-jupiter-engine",
            "junit-platform-commons",
            "junit-platform-engine",
            "junit-platform-launcher",
            "junit-platform-console-standalone",
            "junit-",
            "mockito-core",
            "mockito-junit-jupiter",
            "byte-buddy",
            "byte-buddy-agent",
            "objenesis",
            "hamcrest",
        ]

        seen_prefixes = set()
        for prefix in artifact_prefixes:
            if prefix in seen_prefixes:
                continue
            # Find all jars matching this prefix
            candidates = [
                j for j in m2.rglob(f"{prefix}*.jar")
                if "sources" not in j.name
                and "javadoc" not in j.name
                and not j.name.endswith("-tests.jar")
            ]
            if candidates:
                # Pick newest version
                candidates.sort(key=lambda p: str(p), reverse=True)
                all_jars.append(str(candidates[0]))
                seen_prefixes.add(prefix)

        print(f"        [classpath] Found {len(all_jars)} jars via .m2 glob")
        return list(set(all_jars))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _copy_student_exceptions(self, src_dir: Path, target_dir: Path):
        """Copy student's own exception files if they exist (prefer over stubs)."""
        for name in ["IncorrectSpeedSetException", "SpeedSetAboveSpeedLimitException",
                     "IncorrectSpeedException"]:
            for f in Path(src_dir).rglob(f"{name}.java"):
                shutil.copy(f, target_dir / f"{name}.java")
                break

    def _jars_from_pom(self, pom_path: Path) -> List[str]:
        """Parse pom.xml and find the corresponding jars in .m2."""
        if not pom_path.exists():
            return []
        try:
            content_pom = pom_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        m2 = Path(os.path.expanduser("~")) / ".m2" / "repository"
        jars = []

        # Extract all <groupId>/<artifactId>/<version> triples from dependencies
        dep_pattern = re.compile(
            r"<dependency>\s*"
            r"<groupId>([^<]+)</groupId>\s*"
            r"<artifactId>([^<]+)</artifactId>\s*"
            r"<version>([^<]+)</version>",
            re.DOTALL
        )
        for m in dep_pattern.finditer(content_pom):
            group_id    = m.group(1).strip()
            artifact_id = m.group(2).strip()
            version     = m.group(3).strip()
            group_path  = group_id.replace(".", os.sep)
            jar_path = m2 / group_path / artifact_id / version / f"{artifact_id}-{version}.jar"
            if jar_path.exists():
                jars.append(str(jar_path))

        return jars

    def _find_tool(self, name: str) -> Optional[str]:
        tool = shutil.which(name)
        if tool:
            return tool
        if self.java_home:
            candidate = Path(self.java_home) / "bin" / name
            if candidate.exists():
                return str(candidate)
        return None

    def _find_junit_jar(self) -> Optional[str]:
        """Keep for backwards compat — main jar collection now in _collect_dependency_jars."""
        m2 = Path.home() / ".m2" / "repository"
        standalone = m2 / "org" / "junit" / "platform" / "junit-platform-console-standalone"
        if standalone.exists():
            for version_dir in sorted(standalone.iterdir(), reverse=True):
                for jar in version_dir.glob("junit-platform-console-standalone-*.jar"):
                    if "sources" not in jar.name:
                        return str(jar)
        return None

    def _error_result(self, msg: str) -> dict:
        return {
            "success": False,
            "error": msg,
            "grade": 0.0,
            "requirements_covered": [],
            "requirements_missing": ["R1", "R2", "R3", "R4", "R5", "R6"],
            "requirement_details": {},
            "total_test_methods": 0,
            "requirements_found": 0,
            "coverage_percentage": 0.0,
            "analyzer": "MutationTestAnalyzer-v1",
        }


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rigorous_test_analyzer.py <path/to/CruiseControlTest.java> [student_src_dir]")
        sys.exit(1)

    student_src = sys.argv[2] if len(sys.argv) > 2 else None
    analyzer = MutationTestAnalyzer()
    result = analyzer.analyze(sys.argv[1], student_src)
    print(json.dumps(result, indent=2))
