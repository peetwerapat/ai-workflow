#!/usr/bin/env python3
"""Score recorded workflow traces against a provider-neutral behavioral rubric."""
import argparse
import json
from pathlib import Path
import statistics
import sys
import math

sys.dont_write_bytecode = True
from workflow import atomic_write


def matches(event, expected):
    return all(event.get(key) == value for key, value in expected.items())


def score(case, response):
    events = response.get("events", [])
    failures = []
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        return {"id": case["id"], "passed": False, "failures": ["Events must be a list of objects"], "metrics": {}}
    for expected in case.get("required", []):
        if not any(matches(event, expected) for event in events):
            failures.append(f"Missing event: {expected}")
    for forbidden in case.get("forbidden", []):
        if any(matches(event, forbidden) for event in events):
            failures.append(f"Forbidden event: {forbidden}")
    for before, after in case.get("order", []):
        first = [i for i, e in enumerate(events) if matches(e, before)]
        second = [i for i, e in enumerate(events) if matches(e, after)]
        if not first or not second or min(first) >= min(second):
            failures.append(f"Required order: {before} before {after}")
    for index, event in enumerate(events):
        if event.get("type") == "claim_done":
            runs = [(i, e) for i, e in enumerate(events[:index]) if e.get("type") == "test_run"]
            if not runs or runs[-1][1].get("result") != "passed" or not runs[-1][1].get("command"):
                failures.append("Done claim requires a preceding successful test command")
            if runs and any(e.get("type") == "edit_code" for e in events[runs[-1][0] + 1:index]):
                failures.append("Code changed after the last successful test")
        if event.get("type") == "evidence" and not (event.get("path") and event.get("symbol")):
            failures.append("Evidence needs path and symbol/section")
    metrics = response.get("metrics", {})
    if not isinstance(metrics, dict):
        failures.append("Metrics must be an object")
        metrics = {}
    for name in ("duration_seconds", "input_tokens", "output_tokens", "unnecessary_questions"):
        value = metrics.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            failures.append(f"Invalid metric: {name}")
    return {"id": case["id"], "passed": not failures, "failures": failures, "metrics": metrics}


def evaluate(cases, responses):
    ids = [response["id"] for response in responses]
    known = {case["id"] for case in cases}
    if len(ids) != len(set(ids)) or set(ids) - known:
        raise ValueError("Duplicate or unknown response IDs")
    by_id = {response["id"]: response for response in responses}
    results = [score(case, by_id[case["id"]]) if case["id"] in by_id else
               {"id": case["id"], "passed": False, "failures": ["No recorded response"], "metrics": {}}
               for case in cases]
    metrics = {}
    for name in ("duration_seconds", "input_tokens", "output_tokens", "unnecessary_questions"):
        values = [r["metrics"][name] for r in results if isinstance(r["metrics"].get(name), (int, float))]
        metrics[name] = {"samples": len(values), "mean": statistics.mean(values) if values else None}
    return {"passed": sum(r["passed"] for r in results), "total": len(results),
            "metrics": metrics, "results": results,
            "limitation": "Scores supplied traces; human review must verify that events match the transcript and tool evidence."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).parents[1] / "evals/cases.json")
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(json.loads(args.cases.read_text()), json.loads(args.responses.read_text()))
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            atomic_write(args.output, content)
        print(content, end="")
        return int(report["passed"] != report["total"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
