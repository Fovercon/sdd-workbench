"""Slot manifests with resume support and a bounded worker pool."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class Slots:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self.data = {'slots': []}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding='utf-8'))

    def add(self, slot):
        with self._lock:
            if any(s['id'] == slot['id'] for s in self.data['slots']):
                return False
            self.data['slots'].append(dict(slot, status='pending'))
            self._flush()
            return True

    def pending(self):
        with self._lock:
            return [s for s in self.data['slots'] if s['status'] == 'pending']

    def mark(self, slot_id, status, detail=None):
        with self._lock:
            for s in self.data['slots']:
                if s['id'] == slot_id:
                    s['status'] = status
                    if detail is not None:
                        s['detail'] = str(detail)[:500]
            self._flush()

    def all(self):
        with self._lock:
            return list(self.data['slots'])

    def _flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # default=str keeps PosixPath fields serializable; consumers wrap with Path()
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2, default=str),
                             encoding='utf-8')


def run_parallel(slots, worker, max_workers=3):
    """Run every pending slot; the worker marks its own status, unexpected
    exceptions are recorded as slot errors so a rerun can resume."""
    pend = slots.pending()
    if not pend:
        return

    def guarded(slot):
        try:
            worker(slot)
        except Exception as exc:  # noqa: BLE001 - keep the batch alive
            slots.mark(slot['id'], 'error', repr(exc))

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        list(pool.map(guarded, pend))
