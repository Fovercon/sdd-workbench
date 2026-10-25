"""Synthetic local record browser; stdlib only, never uses real user data."""
import argparse
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class InvalidState(ValueError):
    pass


def decode(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidState('Conflicting persistent state')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


class Ledger:
    def __init__(self, path):
        self.path = Path(path)

    def records(self):
        try:
            value = decode(self.path.read_text(encoding='utf-8'))
            records = value['records']
            if not isinstance(records, list):
                raise InvalidState('Invalid records')
            for row in records:
                if not isinstance(row['id'], str) or not row['id']:
                    raise InvalidState('Invalid identity')
                date.fromisoformat(row['date'])
            if len({row['id'] for row in records}) != len(records):
                raise InvalidState('Duplicate record identity')
            return records
        except (ValueError, KeyError, TypeError, OSError) as error:
            raise InvalidState('Cannot trust persistent state') from error

    def append(self, row):
        records = self.records()
        if not isinstance(row, dict):
            raise ValueError('Record must be an object')
        if not isinstance(row.get('id'), str) or not row['id']:
            raise ValueError('Record identity required')
        date.fromisoformat(row['date'])
        if any(old['id'] == row['id'] for old in records):
            raise ValueError('Record already exists')
        records.append({'id': row['id'], 'date': row['date']})
        self.path.write_text(json.dumps({'records': records}) + '\n', encoding='utf-8')
        return records


def filtered(records, start='', end=''):
    if start: date.fromisoformat(start)
    if end: date.fromisoformat(end)
    if start and end and start > end:
        raise ValueError('Start must not follow end')
    return [row for row in records if (not start or row['date'] >= start) and
            (not end or row['date'] <= end)]


def server(state, port=0):
    ledger = Ledger(state)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, status, value):
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == '/':
                body = Path(__file__).with_name('index.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
                return
            if url.path != '/api/records':
                self.respond(404, {'error': 'Not found'}); return
            try:
                query = parse_qs(url.query)
                self.respond(200, {'records': filtered(ledger.records(),
                    query.get('start', [''])[0], query.get('end', [''])[0])})
            except InvalidState as error:
                self.respond(409, {'error': str(error)})
            except ValueError as error:
                self.respond(400, {'error': str(error)})

        def do_POST(self):
            if self.path != '/api/records':
                self.respond(404, {'error': 'Not found'}); return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size > 4096: raise ValueError('Input too large')
                row = json.loads(self.rfile.read(size))
                self.respond(201, {'records': ledger.append(row)})
            except InvalidState as error:
                self.respond(409, {'error': str(error)})
            except (ValueError, KeyError, TypeError) as error:
                self.respond(400, {'error': str(error)})
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--port', type=int, default=0); args = parser.parse_args()
    http = server(args.state, args.port)
    print(json.dumps({'url': f'http://127.0.0.1:{http.server_port}'}), flush=True)
    try: http.serve_forever()
    finally: http.server_close()
