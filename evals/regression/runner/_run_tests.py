#!/usr/bin/env python3
"""Evaluator-side test runner (never shipped to an actor workspace).

Loads every test_*.py under a directory as a module and prints one JSON line:
{"total", "passed", "failures", "errors", "skipped", "detail": [...]}. Used for
both hidden tests and the actor's own visible tests.
"""
import importlib.util
import importlib
import hashlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

# The wrapper's own directory must never shadow project modules (a task may
# legitimately define report.py etc.), so drop it from sys.path and prefer cwd.
_here = str(Path(__file__).resolve().parent)
sys.path[:] = [p for p in sys.path if Path(p or '.').resolve().as_posix() != Path(_here).resolve().as_posix()]
sys.path.insert(0, os.getcwd())


def load_suite(tests_dir, selected=None):
    suite = unittest.TestSuite()
    paths = selected if selected is not None else Path(tests_dir).glob('test_*.py')
    for path in sorted(Path(path) for path in paths):
        suffix = hashlib.sha256(str(path).encode('utf-8')).hexdigest()[:12]
        name = 'eval_tests_' + path.stem + '_' + suffix
        try:
            relative = path.resolve().relative_to(Path.cwd())
        except ValueError:
            relative = None
        if relative and all(part.isidentifier() for part in relative.with_suffix('').parts):
            parents = list(relative.parent.parts)
            if parents and all((Path(*parents[:i]) / '__init__.py').is_file()
                               for i in range(1, len(parents) + 1)):
                importlib.import_module('.'.join(parents))
                name = '.'.join(relative.with_suffix('').parts)
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    return suite


def main(tests_dir, selected=None):
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=0)
    result = runner.run(load_suite(tests_dir, selected))
    detail = []
    for test, _ in list(result.failures) + list(result.errors):
        detail.append(str(test))
    payload = {'total': result.testsRun,
               'failures': len(result.failures),
               'errors': len(result.errors),
               'skipped': len(result.skipped),
               'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
               'detail': detail}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or None)
