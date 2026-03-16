#!/usr/bin/env python3
"""
generate_summary.py — Regenerates grading_summary.json for the dashboard.

Reads the original per-student JSON files (StudentName_YYYYMMDD.json) from
grader/results/ — ignores _pattern_ and _rigorous_ files entirely.
Uses only the LATEST file per student.

Run from grader/ directory:   python generate_summary.py
"""
import json, re, argparse
from pathlib import Path
from datetime import datetime


def generate_summary(results_dir):
    # Collect only original-format files (ignore _pattern_, _rigorous_, grading_summary)
    students = {}
    for f in sorted(results_dir.glob("*.json")):
        name = f.name
        if any(x in name for x in ["_pattern_", "_rigorous_", "grading_summary"]):
            continue
        # student_id = filename minus trailing _YYYYMMDD
        student_id = re.sub(r'_\d{8}$', '', f.stem)
        # Keep latest file per student
        if student_id not in students or name > students[student_id].name:
            students[student_id] = f

    print(f"Found {len(students)} student(s)...")
    results = []

    for student_id in sorted(students):
        path = students[student_id]
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            print(f"  WARNING: {path.name}: {e}")
            continue

        # Ensure student_id is set correctly
        data["student_id"] = student_id

        # Inject mutation fields (not in old files — mark as not used)
        ta = data.get("test_analysis")
        if isinstance(ta, dict):
            ta.setdefault("mutation_used", False)
            ta.setdefault("mutation_grade", None)

        results.append(data)
        print(f"  {student_id}: test={data.get('test_coverage_grade', 0):.2f}  "
              f"impl={data.get('implementation_grade', 0):.2f}  "
              f"combined={data.get('combined_grade', 0):.2f}")

    successful = [r for r in results if r.get("success")]
    n = len(successful)
    summary = {
        "generated": datetime.now().isoformat(),
        "total_students": len(results),
        "successful_students": n,
        "averages": {
            "test_coverage_grade":  round(sum(r.get("test_coverage_grade",  0) for r in successful) / n, 2) if n else 0,
            "implementation_grade": round(sum(r.get("implementation_grade", 0) for r in successful) / n, 2) if n else 0,
            "combined_grade":       round(sum(r.get("combined_grade",       0) for r in successful) / n, 2) if n else 0,
        },
        "results": results,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()

    results_dir = Path(args.results)
    if not results_dir.exists():
        results_dir = Path(__file__).parent / "results"
    if not results_dir.exists():
        print(f"ERROR: Not found: {results_dir}")
        return

    print(f"Reading from: {results_dir.resolve()}")
    summary = generate_summary(results_dir)

    out = results_dir / "grading_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    avg = summary["averages"]
    print(f"Avg test: {avg['test_coverage_grade']}  "
          f"avg impl: {avg['implementation_grade']}  "
          f"avg combined: {avg['combined_grade']}")


if __name__ == "__main__":
    main()
