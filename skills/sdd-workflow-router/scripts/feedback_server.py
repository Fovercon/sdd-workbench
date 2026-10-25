#!/usr/bin/env python3
"""Serve one immutable board with durable, version-bound local feedback (stdlib only)."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import threading
from urllib.parse import quote, urlsplit

from project_view import previous_version, sha
from project_view_lib import decisions, evidence

MAX_BODY = 65536
LABELS = {'ANSWER': '已反馈', 'REQUEST_CHANGES': '已收到，待调整', 'DEFER': '已暂缓反馈'}


class FeedbackError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class Store:
    def __init__(self, root, view, state):
        self.root, self.view = Path(root).resolve(), Path(view).resolve()
        data, self.snapshot, self.receipt_sha = previous_version(self.view)
        receipt = json.loads((self.view / 'receipt.json').read_bytes())
        if str(self.root) != receipt['source_root'] or not self.root.is_dir():
            raise ValueError('Use the original receipt source_root; regenerate a relocated board first')
        self.version = sha(data)
        self.bundles = {self.receipt_sha: self.view}
        # Always start from a newly rendered board, rather than patching an old artifact.
        if 'data-live-feedback-ready' not in (self.view / 'index.html').read_text():
            raise ValueError('Regenerate this board with the current renderer before serving feedback')
        state = Path(state).absolute()
        if state.is_symlink():
            raise ValueError('Feedback state directory must not be a symlink')
        state = state.resolve()
        if state == self.root or state == self.view or state.is_relative_to(self.view):
            raise ValueError('Choose a dedicated feedback directory outside the immutable view')
        # A feedback store must never overwrite a cited source or immutable bundle.
        protected = {evidence.source_path(self.root, r['path'])
                     for item in self.snapshot['items'] for r in item.get('sources', [])}
        self.db_path = state / 'feedback.sqlite3'
        if self.db_path in protected or self.db_path.is_symlink():
            raise ValueError('Feedback database conflicts with a source or symlink')
        state.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS feedback (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                version TEXT NOT NULL, item TEXT NOT NULL, request_id TEXT NOT NULL,
                payload_sha TEXT NOT NULL, record TEXT NOT NULL,
                UNIQUE(project, request_id))''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def baseline(self):
        data, snapshot, receipt_sha = previous_version(self.view)
        if sha(data) != self.version or receipt_sha != self.receipt_sha:
            raise FeedbackError(409, '看板版本已变化，请重新打开当前看板。')
        return evidence.inspect(self.root, snapshot)

    def latest(self, db, item):
        row = db.execute('SELECT record FROM feedback WHERE project=? AND version=? AND item=? ORDER BY seq DESC LIMIT 1',
                         (self.snapshot['project_id'], self.version, item)).fetchone()
        return json.loads(row[0]) if row else None

    def status(self):
        items = self.baseline()
        records, current = {}, {}
        with self.connect() as db:
            for item in items:
                if item.get('decision', {}).get('kind') != 'feedback':
                    continue
                related = [item, *(i for i in items if i.get('decision_ref') == item['id'])]
                current[item['id']] = (all(i['freshness'] == 'CURRENT' for i in related)
                                       and item['effective_state'] in ('GAP', 'SATISFIED', 'PENDING_HUMAN'))
                saved = self.latest(db, item['id'])
                if saved:
                    records[item['id']] = saved
        return {'snapshot_sha256': self.version, 'records': records, 'current': current}

    def bundle(self, key):
        path = self.bundles.get(key)
        if path is None:
            raise FeedbackError(404, '看板版本不存在。')
        _data, snapshot, receipt_sha = previous_version(path)
        if receipt_sha != key:
            raise FeedbackError(409, '历史看板的内容已变化。')
        return path, snapshot, json.loads((path / 'receipt.json').read_bytes())

    def document(self, key, live=False):
        path, _snapshot, receipt = self.bundle(key)
        document = (path / 'index.html').read_text()
        if live:
            meta = f'<meta name="sdd-feedback-token" content="{html.escape(self.token, quote=True)}">'
            document = document.replace('<head>', '<head>' + meta, 1)
            document = document.replace("base-uri 'none';", "connect-src 'self'; base-uri 'none';", 1)
        # Register only verified predecessors, never a client-supplied filesystem path.
        previous = receipt.get('previous')
        if previous:
            parent = Path(previous['path']).resolve()
            _data, snapshot, parent_sha = previous_version(parent)
            if parent_sha != previous['receipt_sha256'] or snapshot['project_id'] != self.snapshot['project_id']:
                raise FeedbackError(409, '上一版看板需要重新核对。')
            self.bundles[parent_sha] = parent
            old_href = quote(os.path.relpath(parent / 'index.html', path).replace(os.sep, '/'), safe='/')
            document = document.replace('href="' + html.escape(old_href, quote=True) + '"',
                                        f'href="/history/{parent_sha}/index.html"')
        for item in receipt['items']:
            if 'artifact_href' in item:
                document = document.replace('href="' + html.escape(item['artifact_href'], quote=True) + '"',
                    f'href="/artifacts/{key}/' + quote(item['id'], safe='') + '"')
            for ref in item.get('sources', []):
                source_id = sha(ref['path'].encode('utf-8'))
                document = document.replace('href="' + html.escape(ref['href'], quote=True) + '"',
                                            f'href="/sources/{key}/{source_id}"')
        return document.encode()

    def source(self, key, source_id):
        """Read only a cited, unchanged UTF-8 source; never accept a client path."""
        _path, snapshot, receipt = self.bundle(key)
        refs = [ref for item in snapshot['items'] for ref in item.get('sources', [])
                if sha(ref['path'].encode('utf-8')) == source_id]
        if not refs:
            raise FeedbackError(404, '来源文件不在本版看板的引用范围内。')
        try:
            path = evidence.source_path(Path(receipt['source_root']).resolve(), refs[0]['path'])
            data = path.read_bytes()
        except (ValueError, OSError) as error:
            raise FeedbackError(404, '来源文件不存在或已离开项目范围。') from error
        if any(ref.get('sha256') != sha(data) for ref in refs):
            raise FeedbackError(409, '来源文件已变化，请重新核对并生成新版看板。')
        try:
            data.decode('utf-8')
            if b'\x00' in data:
                raise ValueError('Binary source')
        except (UnicodeError, ValueError) as error:
            raise FeedbackError(415, '此来源不是 UTF-8 文本，请在项目中打开原文件。') from error
        return data

    def submit(self, payload):
        if not isinstance(payload, dict):
            raise FeedbackError(400, '反馈格式不正确。')
        request_id, revision = payload.get('request_id'), payload.get('expected_revision')
        if (not isinstance(request_id, str) or not 16 <= len(request_id) <= 100
                or not all(c.isascii() and (c.isalnum() or c in '-_') for c in request_id)
                or type(revision) is not int or revision < 0):
            raise FeedbackError(400, '反馈缺少提交编号或当前状态，请刷新后再试。')
        digest = sha(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode())
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT payload_sha,record FROM feedback WHERE project=? AND request_id=?',
                                  (self.snapshot['project_id'], request_id)).fetchone()
            if existing:
                if existing[0] != digest:
                    raise FeedbackError(409, '同一个提交编号不能用于不同的反馈。')
                return json.loads(existing[1])
            items = self.baseline()
            try:
                checked = decisions.validate_response(self.snapshot, items, self.version, payload)
            except ValueError as error:
                stale = any(word in str(error) for word in ('version', 'sources', 'baseline'))
                message = ('版本或图示来源已变化，请重新查看后再提交。' if stale else
                           '请说明需要调整的内容。' if 'concrete note' in str(error) else
                           '补充说明须为文字，最多 12000 字。' if 'note must' in str(error) else
                           '请选择当前卡片提供的反馈选项。' if 'options' in str(error) else
                           '反馈入口已变化，请刷新看板后再提交。')
                raise FeedbackError(409 if stale else 400, message) from error
            if checked['kind'] != 'feedback':
                raise FeedbackError(403, '这里仅接收方案反馈；项目审批和业务决定请在对话中处理。')
            old = self.latest(db, checked['item_id'])
            if revision != (old['revision'] if old else 0):
                raise FeedbackError(409, '另一处已经更新了反馈，请刷新查看后再修改。')
            item = next(i for i in items if i['id'] == checked['item_id'])
            option = next(o for o in item['decision']['options'] if o['id'] == checked['answer'])
            related = [i for i in items if i['id'] == item['id'] or i.get('decision_ref') == item['id']]
            record = {'schema': 'sdd-local-feedback/v1', 'project_id': self.snapshot['project_id'],
                      'snapshot_sha256': self.version, 'receipt_sha256': self.receipt_sha,
                      'request_id': request_id, 'item_id': item['id'], 'decision_id': checked['decision_id'],
                      'revision': revision + 1, 'answer': checked['answer'], 'answer_label': option['label'],
                      'note': checked['note'], 'effect': checked['effect'], 'scope': checked['scope'],
                      'status': LABELS[checked['effect']], 'submitted_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                      'origin': 'local_board_submit', 'authority': 'feedback_only',
                      'sources': {i['id']: i['sources'] for i in related}}
            db.execute('INSERT INTO feedback(project,version,item,request_id,payload_sha,record) VALUES(?,?,?,?,?,?)',
                       (record['project_id'], self.version, item['id'], request_id, digest,
                        json.dumps(record, ensure_ascii=False)))
            # The context commits before this result reaches the browser. Failed writes leave no saved claim.
        return record


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store, port):
        self.store = store
        super().__init__(('127.0.0.1', port), Handler)
        self.origin = f'http://127.0.0.1:{self.server_port}'


class Handler(BaseHTTPRequestHandler):
    server_version = 'SDDFeedback/1'

    def log_message(self, *_args):
        pass  # Do not log bodies, notes or session tokens.

    def respond(self, status, value, mime='application/json; charset=utf-8', sandbox=False):
        data = json.dumps(value, ensure_ascii=False).encode() if isinstance(value, dict) else value
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        if sandbox:
            self.send_header('Content-Security-Policy', "sandbox allow-scripts; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def guard(self, write=False, api=False):
        if self.headers.get('Host') != urlsplit(self.server.origin).netloc:
            raise FeedbackError(403, '仅允许从本机看板访问。')
        if write and self.headers.get('Origin') != self.server.origin:
            raise FeedbackError(403, '提交必须来自当前本机看板。')
        if api and not secrets.compare_digest(self.headers.get('X-SDD-Token', ''), self.server.store.token):
            raise FeedbackError(403, '看板连接已过期，请刷新后重试。')

    def handle_error(self, error):
        if isinstance(error, FeedbackError):
            self.respond(error.status, {'error': error.message})
        else:
            self.respond(503, {'error': '本机记录服务暂时不可用，尚未确认保存。请保留内容后重试。'})

    def do_GET(self):
        try:
            self.guard(api=self.path == '/api/feedback')
            store = self.server.store
            if self.path == '/api/feedback':
                self.respond(200, store.status())
            elif self.path in ('/', '/index.html'):
                store.baseline()
                self.respond(200, store.document(store.receipt_sha, live=True), 'text/html; charset=utf-8')
            elif self.path in ('/snapshot.json', '/receipt.json', '/view.md'):
                store.baseline()
                self.respond(200, (store.view / self.path[1:]).read_bytes(),
                             'text/plain; charset=utf-8' if self.path.endswith('.md') else 'application/json; charset=utf-8')
            elif self.path.startswith('/history/'):
                parts = self.path.split('/')
                if len(parts) != 4 or parts[3] not in ('index.html', 'snapshot.json', 'receipt.json', 'view.md'):
                    raise FeedbackError(404, '历史页面不存在。')
                path, _snapshot, _receipt = store.bundle(parts[2])
                data = store.document(parts[2]) if parts[3] == 'index.html' else (path / parts[3]).read_bytes()
                self.respond(200, data, 'text/html; charset=utf-8' if parts[3] == 'index.html' else 'text/plain; charset=utf-8')
            elif self.path.startswith('/artifacts/'):
                parts = self.path.split('/')
                if len(parts) != 4:
                    raise FeedbackError(404, '图示不存在。')
                _path, snapshot, receipt = store.bundle(parts[2])
                root = Path(receipt['source_root']).resolve()
                items = evidence.inspect(root, snapshot)
                item = next((i for i in items if 'artifact' in i and parts[3] == quote(i['id'], safe='')), None)
                if item is None or item['freshness'] != 'CURRENT':
                    raise FeedbackError(404, '图示不存在或来源已变化。')
                self.respond(200, evidence.source_path(root, item['artifact']).read_bytes(),
                             'text/html; charset=utf-8', sandbox=True)
            elif self.path.startswith('/sources/'):
                parts = self.path.split('/')
                if len(parts) != 4:
                    raise FeedbackError(404, '来源文件入口不存在。')
                self.respond(200, store.source(parts[2], parts[3]),
                             'text/plain; charset=utf-8', sandbox=True)
            else:
                raise FeedbackError(404, '页面不存在。')
        except (FeedbackError, ValueError, KeyError, TypeError, OSError, sqlite3.Error) as error:
            self.handle_error(error)

    def do_POST(self):
        try:
            self.guard(write=True, api=True)
            if self.path != '/api/feedback':
                raise FeedbackError(404, '接口不存在。')
            if self.headers.get_content_type() != 'application/json' or self.headers.get('Transfer-Encoding'):
                raise FeedbackError(415, '仅接收 JSON 反馈。')
            try:
                length = int(self.headers.get('Content-Length', '-1'))
            except ValueError:
                length = -1
            if not 0 < length <= MAX_BODY:
                raise FeedbackError(413, '反馈过长或请求不完整。')
            self.connection.settimeout(10)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise FeedbackError(400, '反馈请求不完整。')
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeError) as error:
                raise FeedbackError(400, '反馈格式不正确。') from error
            record = self.server.store.submit(payload)
            self.respond(200, {'saved': True, 'record': record})
        except (FeedbackError, ValueError, KeyError, TypeError, OSError, sqlite3.Error) as error:
            self.handle_error(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--view', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True, help='Dedicated local feedback directory; preserve it across restarts')
    parser.add_argument('--port', type=int, default=0, help='Loopback port; 0 chooses a free port')
    args = parser.parse_args()
    try:
        server = Server(Store(args.root, args.view, args.state), args.port)
        print(json.dumps({'url': server.origin, 'state': str(server.store.db_path)}, ensure_ascii=False), flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
