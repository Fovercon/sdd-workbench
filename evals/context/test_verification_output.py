"""Pi unittest output is a delivery metric with a deliberately narrow grammar."""
import json
from pathlib import Path
import tempfile
import unittest

from measure import measure


ROWS = (
    "test_秘密 (sample.Case.test_秘密) ... ok\n"
    "test_b (sample.Case.test_b) ... ok\n"
)
FOOTER = "\n" + "-" * 70 + "\nRan 2 tests in 0.024s\n\nOK\n"
OUTPUT = ROWS + FOOTER


def start(identifier, tool="bash", command="cat log"):
    return {"type": "tool_execution_start", "toolCallId": identifier,
            "toolName": tool, "args": {"command": command}}


def end(identifier, output=OUTPUT, tool="bash", **extra):
    return {"type": "tool_execution_end", "toolCallId": identifier, "toolName": tool,
            "result": {"content": [{"type": "text", "text": output}]}, **extra}


def metric(events, host="pi"):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
        result = measure(host, path)
    return result.get("pi_unittest_verbose_lists")


class VerificationOutputTests(unittest.TestCase):
    def test_repeated_rows_count_actual_utf8_delivery_across_calls(self):
        observed = metric([start("a", command="python -m unittest -v"),
                           end("a", "before\n" + OUTPUT + "exit=0\n"), start("b"),
                           end("b", OUTPUT.replace("0.024s", "1.115s"))])
        self.assertIsNotNone(observed)
        size = len(ROWS.encode("utf-8"))
        self.assertEqual(observed["complete_lists"], 2)
        self.assertEqual(observed["list_utf8_bytes"], 2 * size)
        self.assertEqual(observed["repeated_lists"], 1)
        self.assertEqual(observed["repeated_list_utf8_bytes"], size)
        self.assertEqual(observed["witnesses"], [
            {"first_end_line": 2, "repeat_end_line": 4, "tests": 2, "utf8_bytes": size}])
        for secret in ("秘密", "sample", "cat log"):
            self.assertNotIn(secret, json.dumps(observed, ensure_ascii=False))

    def test_parallel_completion_order_and_two_lists_in_one_result(self):
        second = OUTPUT.replace("sample.Case", "other.Case")
        observed = metric([start("a"), start("b"), end("b", OUTPUT + second + OUTPUT),
                           end("a", second + OUTPUT + "independent probe failed\n", isError=True)])
        self.assertIsNotNone(observed)
        self.assertEqual(observed["complete_lists"], 5)
        self.assertEqual(observed["repeated_lists"], 2)
        self.assertEqual([(w["first_end_line"], w["repeat_end_line"]) for w in observed["witnesses"]],
                         [(3, 4), (3, 4)])

    def test_original_order_and_line_endings_distinguish_lists(self):
        windows = OUTPUT.replace("\n", "\r\n")
        swapped = "".join(reversed(ROWS.splitlines(keepends=True))) + FOOTER
        outputs = [OUTPUT, windows, swapped, windows]
        observed = metric([e for i, output in enumerate(outputs)
                           for e in (start(str(i)), end(str(i), output))])
        self.assertIsNotNone(observed)
        self.assertEqual(observed["complete_lists"], 4)
        self.assertEqual(observed["repeated_lists"], 1)
        self.assertEqual(observed["repeated_list_utf8_bytes"], len(ROWS.encode("utf-8")) + 2)

    def test_accepts_only_complete_successful_lists_with_matching_counts(self):
        for label, output in {
                "one": ROWS.splitlines(keepends=True)[0] + FOOTER.replace("2 tests", "1 test"),
                "tail": ROWS.splitlines(keepends=True)[-1] + FOOTER,
                "skip": OUTPUT.replace(" ... ok", " ... skipped 'disabled'", 1),
                "count": OUTPUT.replace("Ran 2", "Ran 3"),
                "separator": OUTPUT.replace("-" * 70, "-" * 5),
                "failure": OUTPUT.replace("\nOK", "\nFAILED (failures=1)"),
                "skip suffix": OUTPUT.replace("\nOK", "\nOK (skipped=1)"),
                "incomplete": OUTPUT.split("OK")[0],
        }.items():
            with self.subTest(label=label):
                observed = metric([start("a"), end("a", output)])
                self.assertIsNotNone(observed)
                self.assertEqual(observed["complete_lists"], 0)

    def test_only_first_matched_bash_result_counts(self):
        events = [end("orphan"), start("a"), end("a"), end("a"),
                  start("read", tool="read"), end("read"),
                  start("other"), end("other", tool="read"),
                  start(""), end(""), start(None), end(None),
                  {"type": "message_end", "message": {"role": "toolResult",
                                                       "content": end("a")["result"]["content"]}}]
        observed = metric(events)
        self.assertIsNotNone(observed)
        self.assertEqual(observed["complete_lists"], 1)
        self.assertEqual(observed["repeated_lists"], 0)
        self.assertIsNone(metric(events, host="codex"))

    def test_keeps_only_first_eight_repeat_witnesses(self):
        events = [e for i in range(15) for e in (start(str(i)), end(str(i)))]
        observed = metric(events)
        self.assertIsNotNone(observed)
        self.assertEqual(observed["repeated_lists"], 14)
        self.assertEqual(len(observed["witnesses"]), 8)
        self.assertEqual(observed["witnesses"][-1]["repeat_end_line"], 18)
