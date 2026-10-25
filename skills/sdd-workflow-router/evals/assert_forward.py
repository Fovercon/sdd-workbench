#!/usr/bin/env python3
"""Evaluator-only acceptance checks. Do not expose these to a forward-test actor."""
import argparse
import copy
import importlib.util
import itertools
from pathlib import Path
import unittest

STATES = ("queued", "running", "succeeded", "failed", "cancelled")


def evaluate(workspace):
    spec = importlib.util.spec_from_file_location("fixture_jobs", workspace / "jobs.py")
    jobs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jobs)

    class Acceptance(unittest.TestCase):
        def test_retry_failed_only_and_order(self):
            records = [{"id": str(i), "state": state} for i, state in enumerate(("failed", "succeeded", "failed", "cancelled", "running", "queued"))]
            self.assertEqual(jobs.select_retry(records), ["0", "2"])

        def test_retry_empty(self):
            self.assertEqual(jobs.select_retry([]), [])

        def test_retry_preserves_input(self):
            records = [{"id": "a", "state": "failed"}, {"id": "b", "state": "succeeded"}]
            original = copy.deepcopy(records)
            jobs.select_retry(records)
            self.assertEqual(records, original)

        def test_retry_rejects_unknown_even_after_valid_record(self):
            with self.assertRaises(ValueError):
                jobs.select_retry([{"id": "a", "state": "failed"}, {"id": "b", "state": "mystery"}])

        def test_progress_empty_zero(self):
            self.assertEqual(jobs.progress([]), 0)

        def test_progress_all_terminal_states(self):
            self.assertEqual(jobs.progress([{"id": str(i), "state": s} for i, s in enumerate(STATES[2:])]), 100)

        def test_progress_floor(self):
            records = [{"id": "a", "state": "succeeded"}, {"id": "b", "state": "failed"}, {"id": "c", "state": "running"}]
            self.assertEqual(jobs.progress(records), 66)

        def test_progress_state_combinations(self):
            for length in range(4):
                for states in itertools.product(STATES, repeat=length):
                    records = [{"id": str(i), "state": s} for i, s in enumerate(states)]
                    terminal = sum(s in STATES[2:] for s in states)
                    expected = terminal * 100 // length if length else 0
                    with self.subTest(states=states):
                        value = jobs.progress(records)
                        self.assertIs(type(value), int)
                        self.assertEqual(value, expected)
                        if any(s in STATES[:2] for s in states):
                            self.assertLess(value, 100)

        def test_progress_preserves_input(self):
            records = [{"id": "a", "state": "cancelled"}, {"id": "b", "state": "running"}]
            original = copy.deepcopy(records)
            jobs.progress(records)
            self.assertEqual(records, original)

        def test_progress_rejects_unknown(self):
            with self.assertRaises(ValueError):
                jobs.progress([{"id": "a", "state": "succeeded"}, {"id": "b", "state": "mystery"}])

    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if evaluate(args.workspace).wasSuccessful() else 1)
