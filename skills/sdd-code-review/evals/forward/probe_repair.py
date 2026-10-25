#!/usr/bin/env python3
"""Evaluator-only public behavior checks for a completed local repair."""
import importlib.util
import json
from pathlib import Path
import sys


def observe(project):
    spec=importlib.util.spec_from_file_location('evaluated_labels',project/'labels.py')
    labels=importlib.util.module_from_spec(spec);spec.loader.exec_module(labels)
    def rejects(action):
        try: action()
        except ValueError: return True
        return False
    return {
        'blank_rejected':all(rejects(lambda value=value: labels.normalize_label(value)) for value in ('',' ','\t\n')),
        'trim_preserved':labels.normalize_label(' One ')=='One',
        'stable_case_insensitive_unique':labels.unique_labels([' One ','one','TWO','two','three'])==['One','TWO','three'],
        'invalid_collection_rejected':rejects(lambda: labels.unique_labels(['One','  '])),
        'empty_collection':labels.unique_labels([])==[],
    }


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path)
    args=parser.parse_args();checks=observe(args.project)
    print(json.dumps({'checks':checks,'passed':all(checks.values())},sort_keys=True,indent=2))
    sys.exit(0 if all(checks.values()) else 1)
