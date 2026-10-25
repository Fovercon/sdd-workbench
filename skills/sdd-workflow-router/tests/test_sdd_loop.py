import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sdd_loop", SKILL / "scripts/sdd_loop.py")
loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)


class LoopGates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = json.loads((SKILL / "evals/loop-state.example.json").read_text())
        self.state["mission"]["authorization"] = "Test fixture user explicitly authorizes local implementation and technical choices"

    def artifact(self, name, text="recorded evidence"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return {"path": name, "sha256": loop.file_hash(self.root, name)}

    def planned(self):
        for name, basis in (("spec", "AUTHORIZED_DERIVATION"), ("plan", "DELEGATED_TECHNICAL")):
            self.state["contracts"][name] = {**self.artifact(name + ".md"), "basis": basis, "sources": ["explicit fixture request"], "quality_passed": True}
        self.state["source_files"] = ["src.py", "test.py"]
        self.artifact("src.py", "def value(): return 1\n")
        self.artifact("test.py", "assert value() == 1\n")
        self.state["slices"] = [
            {"id": "S1", "depends_on": [], "acceptance": ["AC-1"], "done": False},
            {"id": "S2", "depends_on": ["S1"], "acceptance": ["AC-2"], "done": False},
        ]

    def close_slice(self, index):
        item = self.state["slices"][index]
        item["done"] = True
        item["receipt"] = {"contract": loop.identities(self.state, self.root)["contract"], "report": self.artifact(f"evidence/s{index}.md")}

    def converged(self):
        self.planned()
        self.close_slice(0)
        self.close_slice(1)
        identity = loop.identities(self.state, self.root)
        self.state["verification"] = {"baseline": identity["baseline"], "command": "python3 -m unittest", "exit_code": 0, "covered": ["AC-1", "AC-2"], "report": self.artifact("evidence/verify.md")}
        self.state["review"] = {"baseline": identity["baseline"], "outcome": "CONVERGED", "covered": ["AC-1", "AC-2"], "findings": [], "report": self.artifact("evidence/review.md")}

    def finished(self):
        self.converged()
        identity = loop.identities(self.state, self.root)
        self.state["finish"] = {"baseline": identity["delivery"], "ready": True, "report": self.artifact("evidence/finish.md"), "receipt": {"baseline": identity["delivery"], "verified": True, "report": self.artifact("evidence/delivery.md")}}
        self.state["learning"]["record"] = self.artifact("evidence/learning.md")

    def action(self):
        return loop.route(self.state, self.root)["action"]

    def test_start_routes_requirements_without_inventing_approval(self):
        self.assertEqual(self.action(), "REQUIREMENTS")

    def test_first_and_next_slice_continue_without_new_prompt(self):
        self.planned()
        self.assertEqual(loop.route(self.state, self.root)["slice"], "S1")
        self.close_slice(0)
        result = loop.route(self.state, self.root)
        self.assertEqual((result["action"], result["slice"]), ("IMPLEMENT", "S2"))

    def test_all_slices_do_not_imply_verified_or_converged(self):
        self.planned()
        self.close_slice(0)
        self.close_slice(1)
        self.assertEqual(self.action(), "VERIFY")

    def test_full_local_delivery_closes(self):
        self.finished()
        self.assertEqual(self.action(), "COMPLETE")

    def test_stage_and_delivery_gates_are_distinct(self):
        self.finished()
        self.state["finish"]["receipt"] = None
        self.assertEqual(self.action(), "DELIVER")
        self.state["mission"]["delivery"]["authorized"] = False
        self.assertEqual(self.action(), "STOP_AUTHORITY")

    def test_source_and_test_changes_invalidate_whole_scope_evidence(self):
        for name in ("src.py", "test.py"):
            with self.subTest(name=name):
                self.finished()
                (self.root / name).write_text("changed behavior or oracle")
                self.assertEqual(self.action(), "VERIFY")

    def test_contract_changes_route_impact_not_false_completion(self):
        self.finished()
        (self.root / "spec.md").write_text("different acceptance")
        self.assertEqual(self.action(), "CHANGE_IMPACT")

    def test_receipt_tampering_invalidates_gate(self):
        self.finished()
        (self.root / "evidence/review.md").write_text("modified review")
        self.assertEqual(self.action(), "CONVERGE")

    def test_green_tests_with_missing_acceptance_do_not_close(self):
        self.finished()
        self.state["verification"]["covered"] = ["AC-1"]
        self.assertEqual(self.action(), "VERIFY")

    def test_review_must_cover_every_obligation(self):
        self.finished()
        self.state["review"]["covered"] = ["AC-1"]
        self.assertEqual(self.action(), "CONVERGE")

    def test_findings_route_repairs_even_when_report_claims_converged(self):
        self.finished()
        self.state["review"]["findings"] = [{"id": "F1", "severity": "HIGH", "status": "OPEN", "route": "IMPLEMENT"}]
        self.assertEqual(self.action(), "IMPLEMENT")
        self.state["review"]["findings"][0]["status"] = "ACCEPTED"
        self.assertEqual(self.action(), "STOP_DECISION")

    def test_destination_change_invalidates_finish(self):
        self.finished()
        self.state["mission"]["delivery"]["destination"] = "different destination"
        self.assertEqual(self.action(), "FINISH")

    def test_existing_current_risk_decision_does_not_prompt_again(self):
        self.finished()
        finding = {"id": "F1", "severity": "LOW", "status": "ACCEPTED", "route": "STOP_DECISION", "decision": {"baseline": loop.identities(self.state, self.root)["baseline"], "authority_source": "Explicit fixture human risk decision", "policy_allows": True, "report": self.artifact("evidence/risk.md")}}
        self.state["review"]["findings"] = [finding]
        self.assertEqual(self.action(), "COMPLETE")
        (self.root / "evidence/risk.md").write_text("different decision")
        self.assertEqual(self.action(), "STOP_DECISION")

    def test_business_choice_stops_before_coding(self):
        self.planned()
        self.state["pending_decisions"] = ["What does partial success retain?"]
        self.assertEqual(self.action(), "STOP_DECISION")

    def test_resume_requires_actual_workspace_observation(self):
        self.finished()
        self.state["observed"] = False
        self.assertEqual(self.action(), "RECOVER")

    def test_overlapping_work_blocks_without_reset(self):
        self.finished()
        self.state["conflicts"] = ["unowned changes in src.py"]
        self.assertEqual(self.action(), "STOP_CONFLICT")

    def test_delegation_is_not_self_granted(self):
        self.planned()
        self.state["mission"]["technical_delegation"] = False
        self.assertEqual(self.action(), "STOP_DECISION")

    def test_no_progress_and_step_budgets_bound_work(self):
        for key, value in (("no_progress", 3), ("steps", 40)):
            with self.subTest(key=key):
                self.state["budget"][key] = value
                self.assertEqual(self.action(), "STOP_BUDGET")
                self.state["budget"][key] = 0

    def test_method_changes_require_authority_and_fresh_regression(self):
        self.finished()
        self.state["learning"]["changed_assets"] = ["method.md"]
        self.artifact("method.md", "candidate")
        self.assertEqual(self.action(), "STOP_AUTHORITY")
        self.state["mission"]["maintain_method"] = True
        self.assertEqual(self.action(), "METHOD_REGRESSION")
        self.state["learning"]["regression"] = {"baseline": loop.identities(self.state, self.root)["method"], "passed": True, "report": self.artifact("evidence/regression.md")}
        self.assertEqual(self.action(), "COMPLETE")
        (self.root / "method.md").write_text("new candidate")
        self.assertEqual(self.action(), "METHOD_REGRESSION")

    def test_missing_receipt_cannot_skip_slice(self):
        self.planned()
        self.state["slices"][0]["done"] = True
        self.assertEqual(self.action(), "IMPLEMENT")

    def test_orphan_acceptance_and_cycles_are_rejected(self):
        self.planned()
        self.state["slices"][1]["acceptance"] = ["AC-1"]
        self.assertEqual(self.action(), "PLAN")
        self.state["slices"][0]["depends_on"] = ["S2"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            self.action()

    def test_unsafe_paths_fail_closed(self):
        self.finished()
        self.state["source_files"] = ["../outside.py"]
        with self.assertRaisesRegex(ValueError, "outside"):
            self.action()

    def test_deleted_source_cannot_reuse_successful_evidence(self):
        self.finished()
        (self.root / "src.py").unlink()
        with self.assertRaises(OSError):
            self.action()

    def test_boolean_schema_is_not_a_valid_version(self):
        self.state["schema"] = True
        with self.assertRaises(ValueError):
            self.action()

    def test_malformed_state_and_string_booleans_fail_closed(self):
        self.state["observed"] = "true"
        with self.assertRaises(ValueError):
            self.action()

    def test_cli_reads_example_and_rejects_missing_fields(self):
        checkpoint = self.root / "loop.json"
        checkpoint.write_text(json.dumps(self.state))
        command = [sys.executable, str(SKILL / "scripts/sdd_loop.py"), "status", str(checkpoint), "--root", str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["action"], "REQUIREMENTS")
        checkpoint.write_text("{}")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["action"], "STOP_INVALID_STATE")


if __name__ == "__main__":
    unittest.main()
