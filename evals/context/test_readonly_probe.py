import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROBE = Path(__file__).with_name("run_readonly_probe.py")


class ReadOnlyProbeTests(unittest.TestCase):
    def test_missing_sandbox_never_falls_back_to_the_command(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, "-B", str(PROBE), directory, "--", sys.executable,
                       "-c", "from pathlib import Path; Path('marker').touch()"]
            result = subprocess.run(command, env={**os.environ, "PATH": ""}, cwd=directory, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"Bubblewrap", result.stderr)
            self.assertFalse((Path(directory) / "marker").exists())

    @unittest.skipUnless(sys.platform == "linux" and shutil.which("bwrap"), "Linux Bubblewrap required")
    def test_nonregular_fixture_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            os.mkfifo(Path(directory) / "pipe")
            result = subprocess.run([sys.executable, "-B", str(PROBE), directory, "--", "/bin/true"],
                                    capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"static fixture", result.stderr)

    @unittest.skipUnless(sys.platform == "linux" and shutil.which("bwrap"), "Linux Bubblewrap required")
    def test_actual_command_streams_exit_and_read_only_mounts(self):
        capability = subprocess.run(["bwrap", "--unshare-all", "--unshare-user", "--disable-userns",
                                     "--ro-bind", "/", "/", "--", "/bin/true"], capture_output=True)
        if capability.returncode:
            self.skipTest("sandbox user namespaces unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example project"
            project.mkdir()
            (project / "input").write_bytes(b"known input")
            secret = Path(tmp) / "sibling.txt"
            secret.touch()
            child = """import errno, json, os, sys
from pathlib import Path
assert not Path(sys.argv[1]).exists()
assert os.getenv('PARENT_MARKER') is None
errors = []
for path in ('input', '/tmp/scratch', '/outside'):
    try:
        Path(path).write_text('unexpected')
    except OSError as exc:
        errors.append(exc.errno)
assert errors == [errno.EROFS] * 3, errors
print(json.dumps([Path.cwd().as_posix(), Path('input').read_text()]))
print('probe stderr', file=sys.stderr)
sys.exit(7)
"""
            result = subprocess.run([sys.executable, "-B", str(PROBE), str(project), "--",
                                     "/usr/bin/python3", "-B", "-c", child, str(secret)],
                                    env={**os.environ, "PARENT_MARKER": "present"},
                                    capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertEqual(json.loads(result.stdout), ["/project", "known input"])
            self.assertEqual(result.stderr, b"probe stderr\n")
            self.assertEqual((project / "input").read_bytes(), b"known input")
