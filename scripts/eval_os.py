#!/usr/bin/env python3
"""Score structured Engineering OS behavior results (Python 3.9+, stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RESULT_FIELDS = {
    "id",
    "selected_skills",
    "disposition",
    "repository_mutation",
    "approval_requested",
    "signals",
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {path}: {exc}") from exc


def validate_cases(cases: object) -> List[str]:
    errors: List[str] = []
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty JSON array"]
    seen = set()
    for index, case in enumerate(cases):
        label = f"case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{label} has no valid id")
        elif case_id in seen:
            errors.append(f"duplicate case id: {case_id}")
        else:
            seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case.get("prompt", "").strip():
            errors.append(f"{case_id or label}: prompt must be non-empty")
        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{case_id or label}: expected must be an object")
            continue
        for field in ("skills", "required_signals"):
            if not isinstance(expected.get(field), list):
                errors.append(f"{case_id or label}: expected.{field} must be an array")
        if expected.get("disposition") not in {"ask", "proceed", "review", "advise"}:
            errors.append(f"{case_id or label}: invalid expected.disposition")
        for field in ("repository_mutation", "approval_requested"):
            if not isinstance(expected.get(field), bool):
                errors.append(f"{case_id or label}: expected.{field} must be boolean")
    return errors


def score(cases: Sequence[dict], results: object) -> List[str]:
    failures: List[str] = []
    if not isinstance(results, list):
        return ["results must be a JSON array"]
    indexed: Dict[str, dict] = {}
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            failures.append(f"result[{index}] must be an object")
            continue
        missing = REQUIRED_RESULT_FIELDS - result.keys()
        if missing:
            failures.append(f"result[{index}] missing fields: {', '.join(sorted(missing))}")
            continue
        result_id = result.get("id")
        if result_id in indexed:
            failures.append(f"duplicate result id: {result_id}")
        indexed[result_id] = result
    case_ids = {case["id"] for case in cases}
    for unknown in sorted(set(indexed) - case_ids):
        failures.append(f"unknown result id: {unknown}")
    for case in cases:
        case_id = case["id"]
        result = indexed.get(case_id)
        if result is None:
            failures.append(f"{case_id}: result missing")
            continue
        expected = case["expected"]
        for field in ("disposition", "repository_mutation", "approval_requested"):
            if result.get(field) != expected[field]:
                failures.append(
                    f"{case_id}: {field}={result.get(field)!r}; expected {expected[field]!r}"
                )
        actual_skills = set(result.get("selected_skills", []))
        for skill in expected["skills"]:
            if skill not in actual_skills:
                failures.append(f"{case_id}: missing selected skill {skill!r}")
        actual_signals = set(result.get("signals", []))
        for signal in expected["required_signals"]:
            if signal not in actual_signals:
                failures.append(f"{case_id}: missing signal {signal!r}")
    return failures


def failed_case_ids(cases: Sequence[dict], results: object) -> set:
    return {failure.split(":", 1)[0] for failure in score(cases, results)} & {
        case["id"] for case in cases
    }


def structural_problems(cases: Sequence[dict], results: object) -> List[str]:
    """Problems with the results file itself, as opposed to a case simply failing."""
    ids = {case["id"] for case in cases}
    return [
        failure
        for failure in score(cases, results)
        if failure.split(":", 1)[0] not in ids or failure.endswith(": result missing")
    ]


def compare(cases: Sequence[dict], results: object, baseline: object) -> List[str]:
    """Compare behavior with the OS versus the same prompts without it.

    Skill selection is ignored: a project without the OS has no skills to select,
    so counting it would turn uplift into "the OS exists".
    """
    problems = [f"results: {item}" for item in structural_problems(cases, results)]
    problems += [f"baseline: {item}" for item in structural_problems(cases, baseline)]
    if not problems:
        for label, data in (("results", results), ("baseline", baseline)):
            unfilled = [
                str(result["id"])
                for result in data
                if not isinstance(result.get("evidence"), str) or not result["evidence"].strip()
            ]
            if unfilled:
                problems.append(f"{label}: no evidence recorded for " + ", ".join(unfilled))
    if problems:
        raise RuntimeError("Cannot compare: " + "; ".join(problems))
    behavior = [dict(c, expected=dict(c["expected"], skills=[])) for c in cases]
    failed, base_failed = failed_case_ids(behavior, results), failed_case_ids(behavior, baseline)
    total = len(cases)
    lines = []
    for case in cases:
        case_id = case["id"]
        note = ""
        if case_id not in base_failed:
            note = "  (passes without the OS: does not test it)"
        lines.append(
            f"{case_id}: with OS {'FAIL' if case_id in failed else 'pass'}, "
            f"baseline {'FAIL' if case_id in base_failed else 'pass'}{note}"
        )
    with_os, without = total - len(failed), total - len(base_failed)
    lines.append(f"With OS {with_os}/{total}; baseline {without}/{total}; uplift {with_os - without} case(s)")
    return lines


def skeleton(cases: Sequence[dict]) -> List[dict]:
    return [
        {
            "id": case["id"],
            "selected_skills": [],
            "disposition": "advise",
            "repository_mutation": False,
            "approval_requested": False,
            "signals": [],
            "evidence": "",
        }
        for case in cases
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals/cases.json")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--results", type=Path, help="structured results to score")
    group.add_argument("--init-results", type=Path, help="write an empty result capture file")
    parser.add_argument(
        "--baseline",
        type=Path,
        help="with --results: results for the same prompts run without the OS, to report uplift",
    )
    args = parser.parse_args(argv)
    if args.baseline and not args.results:
        parser.error("--baseline requires --results")
    try:
        cases = load_json(args.cases)
        errors = validate_cases(cases)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 2
        if args.init_results:
            if args.init_results.exists():
                raise RuntimeError(f"Refusing to overwrite: {args.init_results}")
            args.init_results.parent.mkdir(parents=True, exist_ok=True)
            args.init_results.write_text(
                json.dumps(skeleton(cases), indent=2) + "\n", encoding="utf-8"
            )
            print(f"Created result skeleton: {args.init_results}")
            return 0
        results = load_json(args.results)
        failures = score(cases, results)
        for failure in failures:
            print(f"FAIL: {failure}")
        passed = len(cases) - len({failure.split(":", 1)[0] for failure in failures})
        print(f"Behavior eval: {passed}/{len(cases)} case(s) passed")
        if args.baseline:
            for line in compare(cases, results, load_json(args.baseline)):
                print(line)
        return 1 if failures else 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
