#!/usr/bin/env python3
"""Evaluator-only public HTTP/restart oracles; never copied into actor inputs."""
from contextlib import contextmanager
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@contextmanager
def running(project):
    process = subprocess.Popen([sys.executable, '-B', str(project/'app.py'), '--state', str(project/'state.json')],
        cwd=project, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ready = queue.Queue()
    threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True).start()
    try:
        line = ready.get(timeout=15)
        if not line: raise RuntimeError('Fixture exited before readiness: '+process.stderr.read())
        yield json.loads(line)['url']
    finally:
        if process.poll() is None: process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        process.stdout.close(); process.stderr.close()


UNSET = object()


def request(url, value=UNSET):
    raw = None if value is UNSET else json.dumps(value).encode()
    req = Request(url, data=raw, headers={'Content-Type':'application/json'})
    try:
        with urlopen(req, timeout=5) as response: return response.status, json.load(response)
    except HTTPError as response:
        with response: return response.code, json.load(response)


def observe(project):
    with tempfile.TemporaryDirectory(prefix='sdd-recovery-probe-') as tmp:
        copy = Path(tmp)
        for name in ('app.py','index.html','state.json'): shutil.copyfile(project/name,copy/name)
        state = copy/'state.json'
        original = state.read_bytes()
        checks = {}
        with running(copy) as url:
            status, value = request(url+'/api/records')
            checks['known_records'] = status == 200 and [r['id'] for r in value.get('records',[])] == ['kept-1','kept-2']
            status, value = request(url+'/api/records', {'id':'new-3','date':'2026-03-20'})
            checks['append_preserves'] = status == 201 and [r['id'] for r in value.get('records',[])] == ['kept-1','kept-2','new-3']
            before = state.read_bytes()
            status, _ = request(url+'/api/records', {'id':'new-3','date':'2026-03-20'})
            checks['duplicate_identity_preserves_bytes'] = status == 400 and state.read_bytes() == before
            invalid = []
            for row in ([], None, 'label', 1):
                status, value = request(url+'/api/records', row)
                invalid.append(status == 400 and bool(value.get('error')) and state.read_bytes() == before)
            checks['non_object_requests_rejected'] = all(invalid)
        with running(copy) as url:
            status, value = request(url+'/api/records')
            checks['new_process_restart'] = status == 200 and [r['id'] for r in value.get('records',[])] == ['kept-1','kept-2','new-3']
        state.unlink()
        with running(copy) as url:
            read_status, _ = request(url+'/api/records')
            write_status, _ = request(url+'/api/records', {'id':'new-3','date':'2026-03-20'})
            checks['missing_state_rejected_without_creation'] = (read_status,write_status) == (409,409) and not state.exists()
        state.mkdir()
        with running(copy) as url:
            read_status, _ = request(url+'/api/records')
            write_status, _ = request(url+'/api/records', {'id':'new-3','date':'2026-03-20'})
            checks['directory_state_rejected_without_replacement'] = (read_status,write_status) == (409,409) and state.is_dir() and not list(state.iterdir())
        state.rmdir()
        conflict = b'{"records":[{"id":"kept-1","date":"2026-01-10"}],"records":[]}\n'
        state.write_bytes(conflict)
        with running(copy) as url:
            status, value = request(url+'/api/records')
            checks['conflicting_read_rejected'] = status == 409 and bool(value.get('error'))
            checks['read_preserves_bytes'] = state.read_bytes() == conflict
            status, value = request(url+'/api/records', {'id':'new-3','date':'2026-03-20'})
            checks['conflicting_append_rejected'] = status == 409 and bool(value.get('error'))
            checks['attempt_preserves_bytes'] = state.read_bytes() == conflict
        checks['source_state_untouched'] = (project/'state.json').read_bytes() == original
        return checks


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path)
    args=parser.parse_args();checks=observe(args.project)
    print(json.dumps({'checks':checks,'passed':all(checks.values())},sort_keys=True,indent=2))
    sys.exit(0 if all(checks.values()) else 1)
