import json
from pathlib import Path


def list_jobs(path):
    file = Path(path)
    return json.loads(file.read_text()) if file.exists() else []


def enqueue(path, job_id, payload):
    jobs = list_jobs(path)
    record = {'id': job_id, 'payload': payload}
    jobs.append(record)
    Path(path).write_text(json.dumps(jobs))
    return record
