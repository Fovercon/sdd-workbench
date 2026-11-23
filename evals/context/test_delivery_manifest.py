import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).with_name("check_delivery_manifest.py")
EMPTY = hashlib.sha256(b"").hexdigest()


@unittest.skipUnless(os.name == "posix", "requires POSIX project snapshots")
class DeliveryManifestTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name) / "project"
        self.receipt = self.root / "evidence/SHA256SUMS"
        self.receipt.parent.mkdir(parents=True)

    def run_check(self, rows, *expected):
        self.receipt.write_bytes(rows)
        return subprocess.run([sys.executable, str(CHECKER), str(self.root),
                               "evidence/SHA256SUMS", "--", *expected],
                              capture_output=True, text=True, timeout=5)

    def rejected(self, result, *details):
        self.assertEqual(result.returncode, 1, result.stderr)
        for detail in details:
            self.assertIn(detail, result.stderr)

    def test_binary_bytes_spaces_and_full_relative_paths(self):
        data = b"\x00\xff\r\n"
        (self.root / "evidence/日志 a").write_bytes(data)
        (self.root / "日志 a").touch()
        rows = f"{hashlib.sha256(data).hexdigest()} *./evidence/日志 a\n{EMPTY}  日志 a\n"
        result = self.run_check(rows.encode(), "日志 a", "evidence/日志 a")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_detects_a_signed_file_edited_after_delivery(self):
        (self.root / "trace.md").write_text("final entry\n", encoding="utf-8")
        result = self.run_check(f"{EMPTY}  trace.md\n".encode(), "trace.md")
        self.rejected(result, "digest mismatch", "trace.md")

    def test_coverage_uses_callers_paths_and_rejects_duplicates(self):
        (self.root / "trace.md").touch()
        rows = f"{EMPTY}  trace.md\n"
        self.rejected(self.run_check(rows.encode(), "trace.md", "notes.txt"), "missing", "notes.txt")
        self.rejected(self.run_check(rows.encode(), "logs/trace.md"), "unexpected", "trace.md")
        self.rejected(self.run_check((rows + rows.replace("  ", "  ./")).encode(), "trace.md"),
                      "duplicate", "trace.md")

    def test_rejects_prose_escapes_and_unsafe_names(self):
        for row in ("# note", "", f"\\{EMPTY}  with\\nescape", f"{EMPTY}  ../outside",
                    f"{EMPTY}  /absolute", f"{EMPTY}  a/../b", f"{EMPTY}  x\x00"):
            with self.subTest(row=row):
                self.rejected(self.run_check((row + "\n").encode(), "notes.txt"))
        self.rejected(self.run_check(f"{EMPTY}  trace.md\n".encode(), "../outside"))

    def test_rejects_manifest_itself_even_via_a_hard_link(self):
        self.receipt.touch()
        alias = self.root / "mirror"
        os.link(self.receipt, alias)
        for name in ("./evidence/SHA256SUMS", "mirror"):
            with self.subTest(name=name):
                self.rejected(self.run_check(f"{EMPTY}  {name}\n".encode(), name), "itself")

    def test_rejects_symlinked_target_directory_manifest_and_special_files(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "item").touch()
        (self.root / "alias").symlink_to(outside, target_is_directory=True)
        (self.root / "leaf").symlink_to(outside / "item")
        os.mkfifo(self.root / "pipe")
        for name in ("alias/item", "leaf", "pipe", "evidence"):
            with self.subTest(name=name):
                self.rejected(self.run_check(f"{EMPTY}  {name}\n".encode(), name))
        self.receipt.unlink()
        self.receipt.symlink_to(outside / "sums")
        self.rejected(self.run_check(f"{EMPTY}  x\n".encode(), "x"), "symlink")
