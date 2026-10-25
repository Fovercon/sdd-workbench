"""Exercise durable feedback, stale versions, concurrent edits and the HTTP boundary."""
import copy
import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from feedback_server import FeedbackError, Server, Store


class LiveFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('plan.md', 'module.md'):
            (self.root / name).write_text(name)
        def ref(name):
            return {'path': name, 'sha256': hashlib.sha256((self.root/name).read_bytes()).hexdigest()}
        self.data = {'project_id': 'feedback-test', 'title': '设计图反馈', 'scope': '展示反馈', 'captured_at': '2026-10-22',
            'items': [
                {'id': 'feedback', 'label': '设计图', 'state': 'GAP', 'view': 'progress', 'kind': 'assessment',
                 'sources': [ref('plan.md')], 'decision': {'id': 'D-F', 'kind': 'feedback', 'prompt': '还有哪里需要调整？',
                    'owner': '看板使用者', 'scope': '仅反馈图示。', 'options': [
                        {'id': 'good', 'label': '这版可以', 'description': '图示表达清楚。', 'effect': 'ANSWER'},
                        {'id': 'changes', 'label': '还要调整', 'description': '补充修改意见。', 'effect': 'REQUEST_CHANGES', 'requires_note': True},
                        {'id': 'later', 'label': '先看看', 'description': '暂缓反馈。', 'effect': 'DEFER'}]}},
                {'id': 'child', 'label': '关联图示', 'state': 'GAP', 'view': 'progress', 'kind': 'assessment',
                 'sources': [ref('module.md')], 'decision_ref': 'feedback'},
                {'id': 'approval', 'label': '计划审批', 'state': 'PENDING_HUMAN', 'view': 'progress', 'kind': 'assessment',
                 'sources': [ref('plan.md')], 'decision': {'id': 'D-A', 'kind': 'approval', 'prompt': '是否批准计划？',
                    'owner': '项目所有者', 'scope': '项目审批', 'options': [
                        {'id': 'approve', 'label': '批准', 'description': '批准计划。', 'effect': 'APPROVE'},
                        {'id': 'defer', 'label': '暂缓', 'description': '暂不审批。', 'effect': 'DEFER'}]}}]}
        self.input = self.root / 'input.json'; self.input.write_text(json.dumps(self.data, ensure_ascii=False))
        self.view = self.root / 'view'
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'project_view.py'), 'render', '--root', str(self.root),
                                 '--input', str(self.input), '--output', str(self.view)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.before = {p.name: p.read_bytes() for p in self.view.iterdir()}
        self.store = Store(self.root, self.view, self.root / 'feedback-state')

    def payload(self, **delta):
        return dict({'schema': 'sdd-decision-response/v1', 'project_id': 'feedback-test',
                     'snapshot_sha256': self.store.version, 'item_id': 'feedback', 'decision_id': 'D-F',
                     'answer': 'changes', 'note': '时序图中的失败分支再清楚一点。',
                     'request_id': 'request-00000000001', 'expected_revision': 0}, **delta)

    def count(self):
        with sqlite3.connect(self.store.db_path) as db:
            return db.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]

    def test_feedback_is_durable_scoped_and_does_not_mutate_baseline(self):
        record = self.store.submit(self.payload())
        self.assertEqual(record['status'], '已收到，待调整')
        self.assertEqual(record['authority'], 'feedback_only')
        self.assertEqual(set(record['sources']), {'feedback', 'child'})
        self.assertEqual({p.name: p.read_bytes() for p in self.view.iterdir()}, self.before)
        self.assertEqual((self.root / 'plan.md').read_text(), 'plan.md')
        restarted = Store(self.root, self.view, self.root / 'feedback-state')
        self.assertNotEqual(restarted.token, self.store.token)
        self.assertEqual(restarted.status()['records']['feedback'], record)
        self.assertNotIn(self.store.token, self.store.db_path.read_bytes().decode(errors='ignore'))

    def test_retry_after_lost_response_is_exactly_once(self):
        first = self.store.submit(self.payload())
        # The successful response may have been lost; retry must return the committed receipt.
        (self.root / 'module.md').write_text('changed after commit')
        self.assertEqual(self.store.submit(self.payload()), first)
        self.assertEqual(self.count(), 1)
        with self.assertRaises(FeedbackError) as error:
            self.store.submit(self.payload(note='different'))
        self.assertEqual(error.exception.status, 409)

    def test_edit_preserves_history_and_deferral_is_not_approval(self):
        self.store.submit(self.payload())
        second = self.store.submit(self.payload(answer='good', note='', expected_revision=1, request_id='request-00000000002'))
        third = self.store.submit(self.payload(answer='later', note='', expected_revision=2, request_id='request-00000000003'))
        self.assertEqual(second['status'], '已反馈')
        self.assertEqual(third['status'], '已暂缓反馈')
        self.assertEqual(third['revision'], 3)
        self.assertEqual(self.count(), 3)
        self.assertEqual(self.store.status()['records']['feedback'], third)
        self.assertEqual(self.data['items'][2]['state'], 'PENDING_HUMAN')

    def test_another_tab_cannot_overwrite_unseen_feedback(self):
        self.store.submit(self.payload())
        with self.assertRaises(FeedbackError) as error:
            self.store.submit(self.payload(request_id='request-00000000002'))
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(self.count(), 1)

    def test_parallel_submit_has_one_winner(self):
        barrier = threading.Barrier(2)
        outcomes = []
        def submit(key):
            barrier.wait()
            try:
                outcomes.append(self.store.submit(self.payload(request_id=key))['revision'])
            except FeedbackError as error:
                outcomes.append(error.status)
        threads = [threading.Thread(target=submit, args=(f'parallel-request-{n}',)) for n in (1, 2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertCountEqual(outcomes, [1, 409])
        self.assertEqual(self.count(), 1)

    def test_stale_gate_or_linked_diagram_blocks_writes(self):
        for name in ('plan.md', 'module.md'):
            path = self.root / name; original = path.read_bytes(); path.write_text('changed')
            with self.assertRaises(FeedbackError) as error:
                self.store.submit(self.payload())
            self.assertEqual(error.exception.status, 409)
            self.assertFalse(self.store.status()['current']['feedback'])
            self.assertEqual(self.count(), 0)
            path.write_bytes(original)

    def test_identity_option_required_note_and_version_are_checked(self):
        for delta in ({'project_id': 'other'}, {'snapshot_sha256': '0'*64}, {'item_id': 'child'},
                      {'decision_id': 'wrong'}, {'answer': 'invented'}, {'note': '  '}, {'note': 'x'*12001},
                      {'request_id': '../../bad'}, {'expected_revision': True}):
            with self.subTest(delta=str(delta)[:80]), self.assertRaises(FeedbackError):
                self.store.submit(self.payload(**delta))
        self.assertEqual(self.count(), 0)

    def test_real_approval_cannot_be_submitted_through_feedback_service(self):
        with self.assertRaises(FeedbackError) as error:
            self.store.submit(self.payload(item_id='approval', decision_id='D-A', answer='approve'))
        self.assertEqual(error.exception.status, 403)
        self.assertEqual(self.count(), 0)

    def test_tampered_bundle_and_wrong_root_are_rejected(self):
        (self.view / 'index.html').write_text('tampered')
        with self.assertRaises(ValueError): self.store.status()
        with self.assertRaises(ValueError): Store(self.root, self.view, self.root / 'state2')
        (self.view / 'index.html').write_bytes(self.before['index.html'])
        with self.assertRaises(ValueError): Store(self.view, self.view, self.root / 'state2')

    def test_failed_commit_leaves_no_saved_record(self):
        # Failure during baseline validation rolls the write transaction back.
        with patch.object(self.store, 'baseline', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError): self.store.submit(self.payload())
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.store.submit(self.payload())['revision'], 1)

    def start(self):
        server = Server(self.store, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        return server

    def request(self, server, method, path, value=None, **headers):
        conn = HTTPConnection('127.0.0.1', server.server_port, timeout=10)
        standard = {'Origin': server.origin, 'X-SDD-Token': self.store.token, 'Content-Type': 'application/json'}
        standard.update(headers)
        body = json.dumps(value) if value is not None else None
        conn.request(method, path, body=body, headers=standard)
        response = conn.getresponse(); result = (response.status, dict(response.getheaders()), response.read()); conn.close()
        return result

    def test_http_submit_refresh_and_runtime_token_are_not_written_to_artifact(self):
        server = self.start()
        code, headers, body = self.request(server, 'GET', '/')
        self.assertEqual(code, 200)
        self.assertIn(self.store.token.encode(), body)
        self.assertIn(b"connect-src 'self'", body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        code, _, body = self.request(server, 'POST', '/api/feedback', self.payload())
        self.assertEqual(code, 200); self.assertTrue(json.loads(body)['saved'])
        _, _, body = self.request(server, 'GET', '/api/feedback')
        self.assertEqual(json.loads(body)['records']['feedback']['revision'], 1)
        self.assertEqual({p.name: p.read_bytes() for p in self.view.iterdir()}, self.before)

    def test_http_rejects_cross_origin_missing_token_bad_host_and_arbitrary_paths(self):
        server = self.start()
        for headers in ({'Origin': 'https://other.example'}, {'X-SDD-Token': ''}, {'Host': 'other.example'}):
            code, _, _ = self.request(server, 'POST', '/api/feedback', self.payload(), **headers)
            self.assertEqual(code, 403)
        for path in ('/../plan.md', '/plan.md', '/feedback-state/feedback.sqlite3', '/api/feedback?token=leak'):
            self.assertEqual(self.request(server, 'GET', path)[0], 404)
        self.assertEqual(self.request(server, 'GET', '/api/feedback', **{'X-SDD-Token': ''})[0], 403)
        self.assertEqual(self.count(), 0)

    def test_http_bounds_and_bad_json_never_claim_saved(self):
        server = self.start()
        self.assertEqual(self.request(server, 'POST', '/api/feedback', self.payload(), **{'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request(server, 'POST', '/api/feedback', {'x': 'z'*70000})[0], 413)
        self.assertEqual(self.request(server, 'POST', '/api/feedback', [1, 2])[0], 400)
        self.assertEqual(self.count(), 0)

    def test_history_links_are_verified_and_remain_offline(self):
        next_view = self.root / 'next-view'
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'project_view.py'), 'update', '--root', str(self.root),
                                 '--previous', str(self.view), '--output', str(next_view)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.store = Store(self.root, next_view, self.root / 'feedback-state')
        server = self.start()
        _, _, body = self.request(server, 'GET', '/')
        href = re.search(rb'href="(/history/[0-9a-f]+/index.html)"', body).group(1).decode()
        code, _, history = self.request(server, 'GET', href)
        self.assertEqual(code, 200)
        self.assertNotIn(b'<meta name="sdd-feedback-token"', history)
        self.assertEqual(self.request(server, 'GET', href.replace('index.html', 'view.md'))[0], 200)
        self.assertEqual(self.request(server, 'GET', '/history/' + '0'*64 + '/index.html')[0], 404)
        self.assertEqual({p.name: p.read_bytes() for p in self.view.iterdir()}, self.before)

    def test_artifact_links_are_allowlisted_and_sandboxed(self):
        artifact = self.root / 'diagram.html'; artifact.write_text('<!doctype html><p>Standalone diagram</p>')
        self.data['items'].append({'id': '图示', 'label': '独立图', 'state': 'SATISFIED', 'view': 'diagram', 'kind': 'design',
            'artifact': 'diagram.html', 'sources': [self.data['items'][0]['sources'][0],
                {'path': 'diagram.html', 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]})
        self.input.write_text(json.dumps(self.data))
        next_view = self.root / 'next-view'
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'project_view.py'), 'update', '--root', str(self.root),
                                 '--input', str(self.input), '--previous', str(self.view), '--output', str(next_view),
                                 '--reason', 'Add standalone diagram'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.store = Store(self.root, next_view, self.root / 'feedback-state')
        server = self.start()
        _, _, body = self.request(server, 'GET', '/')
        href = re.search(rb'href="(/artifacts/[^\"]+)"', body).group(1).decode()
        code, headers, content = self.request(server, 'GET', href)
        self.assertEqual(code, 200); self.assertIn(b'Standalone diagram', content)
        self.assertEqual(headers['Content-Security-Policy'], "sandbox allow-scripts; frame-ancestors 'none'")
        artifact.write_text('Changed')
        self.assertEqual(self.request(server, 'GET', href)[0], 404)


if __name__ == '__main__':
    unittest.main()
