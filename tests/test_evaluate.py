import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/tools"))
import evaluate


class EvaluationTest(unittest.TestCase):
    def test_required_forbidden_and_order_reject_incorrect_workflow(self):
        case = json.loads((ROOT / "ai/evals/cases.json").read_text())[0]
        result = evaluate.score(case, {"events": [{"type": "edit_code", "path": "app.py"},
            {"type": "inspect", "path": "app.py"}, {"type": "create_spec"}]})
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["failures"]), 2)

    def test_false_done_and_stale_pass_are_rejected(self):
        case = {"id": "test"}
        for events in ([{"type": "claim_done"}], [
            {"type": "test_run", "command": "python3 -m unittest", "result": "failed"}, {"type": "claim_done"}], [
            {"type": "test_run", "command": "python3 -m unittest", "result": "passed"},
            {"type": "edit_code"}, {"type": "claim_done"}]):
            self.assertFalse(evaluate.score(case, {"events": events})["passed"])

    def test_actual_success_and_missing_metric_samples(self):
        report = evaluate.evaluate([{"id": "test"}, {"id": "missing"}], [{"id": "test", "events": [
            {"type": "test_run", "command": "python3 -m unittest", "result": "passed"}, {"type": "claim_done"}],
            "metrics": {"input_tokens": 100}}])
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["metrics"]["input_tokens"], {"samples": 1, "mean": 100})
        self.assertIsNone(report["metrics"]["duration_seconds"]["mean"])

    def test_rubrics_are_satisfiable_without_contradictions(self):
        # This verifies rubric consistency; it is deliberately not a live model evaluation.
        cases = json.loads((ROOT / "ai/evals/cases.json").read_text())
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            self.assertTrue(evaluate.score(case, {"events": case["required"]})["passed"], case["id"])

    def test_duplicate_responses_are_not_silently_overwritten(self):
        with self.assertRaises(ValueError):
            evaluate.evaluate([{"id": "test"}], [{"id": "test"}, {"id": "test"}])


if __name__ == "__main__":
    unittest.main()
