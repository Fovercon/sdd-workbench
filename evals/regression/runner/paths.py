"""Shared filesystem locations for the regression harness."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repository root
HARNESS = ROOT / 'evals' / 'regression'
CORPUS = HARNESS / 'corpus'
CONFIG = HARNESS / 'config'


def runs_root() -> Path:
    """Trial roots default OUTSIDE the repository: an actor working inside the
    repo could otherwise reach the suite source, the corpus and hidden tests.
    Override with SDD_REGRESSION_ARTIFACTS."""
    override = os.environ.get('SDD_REGRESSION_ARTIFACTS')
    if override:
        return Path(override) / 'runs'
    return Path.home() / '.sdd-regression' / 'runs'


def suite_skills() -> list:
    import json
    suite = json.loads((ROOT / 'suite.json').read_text(encoding='utf-8'))
    return list(suite['skills'])
