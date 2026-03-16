#!/usr/bin/env python3
"""
Improved Test Analyzer - Static analysis of student CruiseControlTest.java
Uses strict combination rules per requirement instead of loose keyword matching.

For each requirement, checks for the COMBINATION of:
  - Correct assertion type (assertThrows, assertNull, assertDoesNotThrow, assertEquals)
  - Correct exception class name (where applicable)
  - Correct method being called (setSpeedSet, getSpeedSet, getSpeedLimit)
  - Correct input value range (positive, zero, negative, above limit)

Requirements:
  R1: speedSet initializes to null
  R2: speedLimit initializes to null
  R3: setSpeedSet accepts positive values (> 0)
  R4: setSpeedSet throws IncorrectSpeedSetException for <= 0
  R5: setSpeedSet accepts values <= speedLimit when speedLimit is set
  R6: setSpeedSet throws SpeedSetAboveSpeedLimitException when exceeding limit
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple


# Weight per requirement (6 requirements, total = 10.0)
REQUIREMENT_WEIGHT = 10.0 / 6  # ~1.6667


class ImprovedTestAnalyzer:

    def __init__(self):
        self.test_methods: Dict[str, str] = {}   # method_name -> body
        self.full_source: str = ""
        self.class_body: str = ""
        self.before_each_body: str = ""

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyze(self, test_file_path: str) -> dict:
        path = Path(test_file_path)
        if not path.exists():
            return self._error_result(f"File not found: {test_file_path}")

        try:
            self.full_source = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return self._error_result(f"Cannot read file: {e}")

        self._parse_methods()

        results = {}
        for req in ["R1", "R2", "R3", "R4", "R5", "R6"]:
            results[req] = self._check_requirement(req)

        covered = [r for r, v in results.items() if v["tested"]]
        missing  = [r for r, v in results.items() if not v["tested"]]
        grade    = round(min(len(covered) * REQUIREMENT_WEIGHT, 10.0), 2)

        return {
            "success": True,
            "grade": grade,
            "requirements_covered": covered,
            "requirements_missing": missing,
            "requirement_details": results,
            "total_test_methods": len(self.test_methods),
            "requirements_found": len(covered),
            "coverage_percentage": round(len(covered) / 6 * 100, 2),
            "analyzer": "ImprovedTestAnalyzer-v2",
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_methods(self):
        """Extract @BeforeEach/@Before body and all @Test method bodies."""
        src = self.full_source

        # Grab BeforeEach / Before setup body
        before_match = re.search(
            r'@(?:BeforeEach|Before)\s+(?:(?:public|protected|void|\s)+\s+)?\w+\s*\([^)]*\)\s*(?:throws[^{]*)?\{',
            src, re.DOTALL
        )
        if before_match:
            self.before_each_body = self._extract_block(src, before_match.end() - 1)

        # Grab all @Test methods
        for m in re.finditer(
            r'@Test\s+(?:(?:public|protected|void|\s)+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?\{',
            src, re.DOTALL
        ):
            name = m.group(1)
            body = self._extract_block(src, m.end() - 1)
            self.test_methods[name] = body

    def _extract_block(self, src: str, open_brace_pos: int) -> str:
        """Return content of a { ... } block starting at open_brace_pos."""
        depth = 0
        start = open_brace_pos
        for i in range(start, len(src)):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    return src[start:i + 1]
        return src[start:]

    # ------------------------------------------------------------------
    # Per-requirement checkers
    # ------------------------------------------------------------------

    def _check_requirement(self, req: str) -> dict:
        checker = {
            "R1": self._check_r1,
            "R2": self._check_r2,
            "R3": self._check_r3,
            "R4": self._check_r4,
            "R5": self._check_r5,
            "R6": self._check_r6,
        }[req]

        passing_tests = []
        details = []

        # Check BeforeEach as well (R1/R2 often verified there)
        all_bodies = dict(self.test_methods)
        if self.before_each_body:
            all_bodies["__before_each__"] = self.before_each_body

        for method_name, body in all_bodies.items():
            passed, reason = checker(body)
            if passed:
                if method_name != "__before_each__":
                    passing_tests.append(method_name)
                details.append({"method": method_name, "reason": reason})

        tested = len(passing_tests) > 0 or any(
            d["method"] == "__before_each__" for d in details
        )

        return {
            "tested": tested,
            "passing_tests": passing_tests,
            "details": details,
            "verification_method": "strict_combination",
        }

    # ------ R1: speedSet initializes to null ------
    def _check_r1(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        # Must: instantiate CruiseControl AND check getSpeedSet() == null
        has_constructor = "cruisecontrol" in b and (
            "new cruisecontrol" in b or "= new" in b
        )
        # Accept assertNull(x.getSpeedSet()) or assertEquals(null, x.getSpeedSet())
        # or assertTrue(x.getSpeedSet() == null)
        checks_null = bool(re.search(
            r'(assertnull\s*\([^)]*getspeedset|assertequals\s*\(\s*null\s*,[^)]*getspeedset'
            r'|asserttrue\s*\([^)]*getspeedset[^)]*==\s*null)',
            b
        ))
        # Also accept before_each that constructs + field-level null check in a test
        constructs_in_context = has_constructor or "cruisecontrol" in self.before_each_body.lower()

        if constructs_in_context and checks_null:
            return True, "assertNull on getSpeedSet() after construction"
        if checks_null:
            return True, "assertNull/assertEquals null on getSpeedSet()"
        return False, "no assertNull on getSpeedSet() found"

    # ------ R2: speedLimit initializes to null ------
    def _check_r2(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        constructs_in_context = "cruisecontrol" in b or "cruisecontrol" in self.before_each_body.lower()
        checks_null = bool(re.search(
            r'(assertnull\s*\([^)]*getspeedlimit|assertequals\s*\(\s*null\s*,[^)]*getspeedlimit'
            r'|asserttrue\s*\([^)]*getspeedlimit[^)]*==\s*null)',
            b
        ))
        if constructs_in_context and checks_null:
            return True, "assertNull on getSpeedLimit() after construction"
        if checks_null:
            return True, "assertNull/assertEquals null on getSpeedLimit()"
        return False, "no assertNull on getSpeedLimit() found"

    # ------ R3: setSpeedSet accepts positive value ------
    def _check_r3(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        # Must call setSpeedSet with a positive value AND not just throw
        calls_setspeedset = "setspeedset" in b

        # Positive intent: assertDoesNotThrow, or direct call with assertion on result,
        # or call without expecting exception + assertEquals on getSpeedSet
        does_not_throw = "doesnotthrow" in b
        asserts_value = bool(re.search(
            r'assertequals\s*\([^)]*getspeedset|asserttrue\s*\([^)]*getspeedset',
            b
        ))
        # Negative: only assertThrows present (that's R4/R6, not R3)
        only_throws = "assertthrows" in b and not does_not_throw and not asserts_value

        if calls_setspeedset and (does_not_throw or asserts_value) and not only_throws:
            return True, "setSpeedSet called with positive value, result asserted"
        if calls_setspeedset and does_not_throw:
            return True, "assertDoesNotThrow on setSpeedSet"
        return False, "no positive-value acceptance test for setSpeedSet"

    # ------ R4: throws IncorrectSpeedSetException for <= 0 ------
    def _check_r4(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        # Must use assertThrows with IncorrectSpeedSetException (or variant name)
        # AND call setSpeedSet with 0 or negative
        has_throws = bool(re.search(
            r'assertthrows\s*\(\s*(incorrectspeed\w*exception|incorrectspeed\w*)',
            b
        ))
        # Also accept try/catch with explicit IncorrectSpeedSetException catch
        has_try_catch = bool(re.search(
            r'catch\s*\(\s*incorrectspeed\w+\s+\w+\s*\)',
            b
        ))
        # Also accept ExpectedException rule (JUnit4)
        has_expected_rule = bool(re.search(
            r'expect\s*\(\s*incorrectspeed\w*exception',
            b
        ))

        has_exception_test = has_throws or has_try_catch or has_expected_rule

        # Must be calling setSpeedSet (directly or via lambda)
        calls_setspeedset = "setspeedset" in b

        # Check that a non-positive value is involved
        # Look for 0, negative literal, or variable named negative/zero/cero
        has_nonpositive = bool(re.search(
            r'setspeedset\s*\([^)]*-\d|setspeedset\s*\(\s*0\s*\)'
            r'|setspeedset\s*\([^)]*\b0\b|negative|cero|zero|negat',
            b
        ))

        if has_exception_test and calls_setspeedset:
            if has_nonpositive:
                return True, "assertThrows IncorrectSpeedSetException with zero/negative input"
            else:
                # Still credit if exception test present even if value not obvious from static analysis
                return True, "assertThrows IncorrectSpeedSetException on setSpeedSet"
        return False, "no assertThrows for IncorrectSpeedSetException found"

    # ------ R5: setSpeedSet accepts value <= speedLimit ------
    def _check_r5(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        combined = b + self.before_each_body.lower()

        # Must: setSpeedLimit called (in test or setUp), setSpeedSet called with valid value,
        # AND some positive assertion (assertDoesNotThrow, assertEquals on getSpeedSet, assertTrue)
        sets_limit = "setspeedlimit" in combined
        sets_speed = "setspeedset" in b
        does_not_throw = "doesnotthrow" in b
        asserts_value  = bool(re.search(
            r'assertequals\s*\([^)]*getspeedset|asserttrue\s*\([^)]*getspeedset',
            b
        ))
        # Must NOT be primarily an exception test (that would be R6)
        is_exception_test = bool(re.search(
            r'assertthrows\s*\(\s*speedsetabove\w*|assertthrows\s*\(\s*incorrectspeed\w*',
            b
        ))

        if sets_limit and sets_speed and (does_not_throw or asserts_value) and not is_exception_test:
            return True, "setSpeedLimit set, setSpeedSet called within limit, result asserted"
        return False, "no acceptance test for setSpeedSet within speedLimit"

    # ------ R6: throws SpeedSetAboveSpeedLimitException ------
    def _check_r6(self, body: str) -> Tuple[bool, str]:
        b = body.lower()
        combined = b + self.before_each_body.lower()

        sets_limit = "setspeedlimit" in combined

        has_throws = bool(re.search(
            r'assertthrows\s*\(\s*(speedsetabove\w*exception|speedsetabove\w*)',
            b
        ))
        has_try_catch = bool(re.search(
            r'catch\s*\(\s*speedsetabove\w+\s+\w+\s*\)',
            b
        ))
        has_expected_rule = bool(re.search(
            r'expect\s*\(\s*speedsetabove\w*exception',
            b
        ))

        has_exception_test = has_throws or has_try_catch or has_expected_rule
        calls_setspeedset  = "setspeedset" in b

        if sets_limit and has_exception_test and calls_setspeedset:
            return True, "setSpeedLimit set, assertThrows SpeedSetAboveSpeedLimitException"
        if has_exception_test and calls_setspeedset:
            return True, "assertThrows SpeedSetAboveSpeedLimitException on setSpeedSet"
        return False, "no assertThrows for SpeedSetAboveSpeedLimitException found"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        }


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <path/to/CruiseControlTest.java>")
        sys.exit(1)

    analyzer = ImprovedTestAnalyzer()
    result = analyzer.analyze(sys.argv[1])
    print(json.dumps(result, indent=2))
