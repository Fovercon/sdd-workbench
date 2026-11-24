import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MEASURE = Path(__file__).with_name("measure.py")
REFERENCE = "First line\n交付阶段需要就绪证据。"


def reply(*calls):
    return {"type": "message_end", "message": {"role": "assistant", "content": [
        {"type": "toolCall", "id": call} for call in calls]}}


def start(call, tool="read"):
    return {"type": "tool_execution_start", "toolCallId": call, "toolName": tool, "args": {}}


def end(call, *texts, tool="read", error=False):
    return {"type": "tool_execution_end", "toolCallId": call, "toolName": tool, "isError": error,
            "result": {"content": [{"type": "text", "text": text} for text in texts]}}


class ReferenceTimingTests(unittest.TestCase):
    def run_cli(self, events, reference=REFERENCE + "\n", host="pi", extra_args=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, stream, output = (root / name for name in ("source.md", "events.jsonl", "metrics.json"))
            options = list(extra_args)
            if reference is not None:
                source.write_bytes(reference.encode())
                options.extend(["--reference-text", str(source)])
            stream.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
            run = subprocess.run([sys.executable, "-B", str(MEASURE), "--host", host, "--events", str(stream),
                                  "--output", str(output), *options], capture_output=True)
            return run, json.loads(output.read_bytes()) if output.exists() else None

    def test_first_whole_text_links_to_the_request_that_selected_the_call(self):
        events = [reply("other", "selected"), start("other"), end("other", "excerpt"),
                  start("selected", "bash"), end("selected", "prefix\n" + REFERENCE, tool="bash"),
                  end("selected", REFERENCE, tool="bash"), reply("again"), start("again"), end("again", REFERENCE)]
        run, result = self.run_cli(events)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = result["pi_reference_text"]
        self.assertEqual(data["matched_calls"], 2)
        self.assertEqual(data["first_return"], {"request": 1, "assistant_end_line": 1,
                                                "start_line": 4, "end_line": 5, "tool": "bash"})
        self.assertEqual(data["matched_text_utf8_bytes"], len(REFERENCE.encode()))
        self.assertNotIn("交付", json.dumps(result, ensure_ascii=False))

    def test_unsupported_or_partial_evidence_produces_no_match(self):
        events = [reply("failed", "parts", "mismatch"), end("missing", REFERENCE),
                  start("failed"), end("failed", REFERENCE, error=True), start("parts"),
                  end("parts", *REFERENCE.splitlines()), start("mismatch", "edit"), end("mismatch", REFERENCE),
                  {"type": "message_end", "message": {"role": "toolResult", "content": [
                      {"type": "text", "text": REFERENCE}]}}, {"type": "agent_end"}]
        run, result = self.run_cli(events)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(result["pi_reference_text"]["matched_calls"], 0)
        self.assertIsNone(result["pi_reference_text"]["first_return"])

    def test_missing_issuer_is_unknown_and_source_bytes_are_preserved(self):
        text = "A\r\nB\r\n"
        run, result = self.run_cli([start("a"), end("a", "A\nB"), start("b"), end("b", "A\r\nB")], text)
        self.assertEqual(run.returncode, 0, run.stderr)
        first = result["pi_reference_text"]["first_return"]
        self.assertIsNone(first["request"])
        self.assertIsNone(first["assistant_end_line"])
        self.assertEqual(first["end_line"], 4)

    def test_overlapping_ids_and_duplicate_declarations_cannot_establish_timing(self):
        events = [reply("ambiguous"), start("ambiguous"), start("ambiguous"), end("ambiguous", REFERENCE),
                  end("ambiguous", REFERENCE), reply("two-issuers"), reply("two-issuers"),
                  start("two-issuers"), end("two-issuers", REFERENCE)]
        run, result = self.run_cli(events)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = result["pi_reference_text"]
        self.assertEqual(data["matched_calls"], 1)
        self.assertEqual(data["first_return"]["end_line"], 9)
        self.assertIsNone(data["first_return"]["request"])

    def test_unissued_older_declaration_or_wrong_tool_cannot_identify_the_request(self):
        wrong_tool = reply("x")
        wrong_tool["message"]["content"][0]["name"] = "edit"
        for head in ([reply("x"), reply("other")], [wrong_tool]):
            run, result = self.run_cli([*head, start("x"), end("x", REFERENCE)])
            self.assertEqual(run.returncode, 0, run.stderr)
            match = result["pi_reference_text"]["first_return"]
            self.assertIsNotNone(match)
            self.assertIsNone(match["request"])
            self.assertIsNone(match["assistant_end_line"])

    def test_id_can_be_reused_after_all_overlapping_calls_return(self):
        events = [reply("x"), start("x"), start("x"), end("x", REFERENCE), end("x", REFERENCE),
                  reply("x"), start("x"), end("x", REFERENCE)]
        run, result = self.run_cli(events)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = result["pi_reference_text"]
        self.assertEqual(data["matched_calls"], 1)
        self.assertEqual((data["first_return"]["request"], data["first_return"]["end_line"]), (2, 8))

    def test_empty_text_and_incompatible_host_are_explicit_errors(self):
        for host, source in (("pi", "\n"), ("codex", REFERENCE)):
            run, result = self.run_cli([], source, host)
            self.assertEqual(run.returncode, 2)
            self.assertIsNone(result)

    def test_opt_in_stage_tool_counts_returned_body_alongside_builtin_reads(self):
        events = [reply("bad", "stage", "other"), start("bad", "open_stage"),
                  end("bad", REFERENCE, tool="open_stage", error=True),
                  start("stage", "open_stage"), end("stage", REFERENCE, tool="open_stage"),
                  start("other", "write"), end("other", REFERENCE, tool="write"),
                  reply("read"), start("read"), end("read", REFERENCE)]
        run, original = self.run_cli(events)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(original["pi_reference_text"]["matched_calls"], 1)
        run, result = self.run_cli(events, extra_args=["--reference-tool", "open_stage"])
        self.assertEqual(run.returncode, 0, run.stderr)
        measured = result["pi_reference_text"]
        self.assertEqual(measured["matched_calls"], 2)
        self.assertEqual(measured["tools_considered"], ["bash", "open_stage", "read"])
        self.assertEqual(measured["first_return"], {"request": 1, "assistant_end_line": 1,
                                                   "start_line": 4, "end_line": 5, "tool": "open_stage"})
        self.assertEqual(original["delivered_tool_text_utf8_bytes"], result["delivered_tool_text_utf8_bytes"])

    def test_extra_result_channel_requires_a_reference(self):
        run, result = self.run_cli([], reference=None, extra_args=["--reference-tool", "open_stage"])
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"requires --reference-text", run.stderr)
        self.assertIsNone(result)
