import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("audit_write_events.py")


def event(path, *events, directory=False):
    return {"path": path, "events": list(events), "directory": directory}


class WriteEventAuditTests(unittest.TestCase):
    def check_log(self, rows, *options):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "watch.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            before = path.read_bytes()
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), *options],
                                    capture_output=True, check=False, timeout=5)
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(set(Path(tmp).iterdir()), {path})
            return result.returncode, json.loads(result.stdout)

    def test_create_then_remove_is_visible_even_when_nothing_remains(self):
        rows = [event("sandbox-tmp/error log", "CREATE"), event("sandbox-tmp/error log", "DELETE")]
        code, report = self.check_log(rows)
        self.assertEqual(code, 1)
        self.assertEqual(report["findings"], [
            {"row": 1, "path": "sandbox-tmp/error log", "events": ["CREATE"]},
            {"row": 2, "path": "sandbox-tmp/error log", "events": ["DELETE"]}])

    def test_only_named_files_are_covered(self):
        permitted = event("project/evidence/readiness.md", "CLOSE_WRITE")
        opt = ["--allow-file", permitted["path"]]
        code, report = self.check_log([permitted], *opt)
        self.assertEqual((code, report["allowed_files"], report["record_count"]), (0, [permitted["path"]], 1))
        for extra in (event("project/trace.md", "MODIFY"), event("sandbox-tmp/e", "CREATE"),
                      event(permitted["path"], "CREATE", directory=True)):
            code, report = self.check_log([permitted, extra], *opt)
            self.assertEqual((code, report["findings"][0]["row"]), (1, 2))

    def test_absence_is_reported_as_an_observation(self):
        code, report = self.check_log([])
        self.assertEqual((code, report["status"], report["record_count"]), (0, "NO_OUT_OF_SCOPE_EVENTS_RECORDED", 0))
        self.assertEqual(self.check_log([], "--allow-file", "project")[0], 2)

    def test_incomplete_log_preserves_concrete_findings(self):
        for bad in (event(None, "Q_OVERFLOW"), event("project/subdir", "IGNORED"),
                    event("project/../other", "CREATE"), event("project/notes", "UNKNOWN"),
                    {"path": "project/notes", "events": ["MODIFY"]}):
            code, report = self.check_log([event("project/trace.md", "MODIFY"), bad])
            self.assertEqual((code, report["status"]), (2, "INCOMPLETE"))
            self.assertTrue(report["issues"])
            self.assertEqual(report["findings"][0]["path"], "project/trace.md")
