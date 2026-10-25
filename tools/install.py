#!/usr/bin/env python3
"""Install the complete suite, preserve local edits, and recover or roll back upgrades."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode = True
import uuid

from package import ROOT, VERSION, check, digest, load, tree_hashes, valid_name


def target_directories(selected=None, home=None, environ=None):
    """Resolve named targets without touching the user's configuration files."""
    registry = load(ROOT / 'agent-targets.json')['targets']
    aliases = {alias: name for name, entry in registry.items() for alias in entry.get('aliases', [])}
    names = list(dict.fromkeys(aliases.get(name, name) for name in (selected or ['codex'])))
    unknown = set(names) - set(registry) - {'all'}
    if unknown:
        raise ValueError('Unknown agent target: ' + ', '.join(sorted(unknown)))
    if 'all' in names:
        names = [name for name in registry if name != 'shared' or 'shared' in names]
    base = Path(home).expanduser() if home is not None else Path.home()
    env = {} if home is not None else (os.environ if environ is None else environ)
    targets = {}
    for name in names:
        entry = registry[name]
        override = env.get(entry.get('env', ''), '').strip()
        targets[name] = ((Path(override).expanduser() / entry['env_path']) if override
                         else base / entry['path']).resolve()
    return targets


def atomic_json(path, value):
    path = Path(path); temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def exists(path):
    return path.exists() or path.is_symlink()


def fingerprints(path):
    return tree_hashes(path) if exists(path) else None


def valid_tree_record(value):
    return isinstance(value, dict) and all(
        isinstance(path, str) and bool(path) and isinstance(sha, str)
        and re.fullmatch(r'[0-9a-f]{64}', sha) is not None for path, sha in value.items())


def valid_journal(value, destination):
    return (isinstance(value, dict) and value.get('schema') == 1
            and value.get('destination') == str(destination)
            and isinstance(value.get('transaction_id'), str) and value['transaction_id'].isalnum()
            and isinstance(value.get('before_hashes'), dict) and isinstance(value.get('after_hashes'), dict)
            and set(value['before_hashes']) == set(value['after_hashes'])
            and all(valid_name(name) for name in value['before_hashes'])
            and all(v is None or valid_tree_record(v)
                    for records in (value['before_hashes'], value['after_hashes']) for v in records.values())
            and all(key in value and (value[key] is None or isinstance(value[key], dict))
                    for key in ('before_receipt', 'after_receipt')))


def remove_tree(path):
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise ValueError(f'Refusing to replace a non-directory: {path}')
    if path.exists(): shutil.rmtree(path)


class Installation:
    def __init__(self, destination, state=None):
        self.dest = Path(destination).expanduser().resolve()
        requested = Path(state).expanduser() if state else self.dest.parent / '.sdd-workbench'
        if requested.is_symlink(): raise ValueError('State directory cannot be a symlink')
        self.state = requested.resolve()
        if self.state == self.dest or self.state.is_relative_to(self.dest) or self.dest.is_relative_to(self.state):
            raise ValueError('Use separate, non-overlapping skill and state directories')
        self.receipt_path = self.state / 'receipt.json'
        self.journal_path = self.state / 'pending.json'

    @contextmanager
    def locked(self):
        self.state.mkdir(parents=True, exist_ok=True)
        path = self.state / 'install.lock'
        if path.is_symlink(): raise ValueError('Install lock cannot be a symlink')
        with path.open('a+b') as stream:
            stream.seek(0, 2)
            if stream.tell() == 0: stream.write(b'0'); stream.flush()
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as error: raise ValueError('Another suite operation is running') from error
            else:
                import fcntl
                try: fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error: raise ValueError('Another suite operation is running') from error
            try: yield
            finally:
                if os.name == 'nt':
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else: fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def receipt(self):
        if self.receipt_path.is_symlink(): raise ValueError('Receipt cannot be a symlink')
        if not self.receipt_path.exists(): return None
        value = load(self.receipt_path)
        if (not isinstance(value, dict) or value.get('schema') != 1
                or value.get('destination') != str(self.dest) or not isinstance(value.get('skills'), dict)
                or value.get('name') != 'sdd-workbench' or not isinstance(value.get('version'), str)
                or not VERSION.fullmatch(value['version'])):
            raise ValueError('Installation receipt belongs to another destination or schema')
        if any(not valid_name(name) for name in value['skills']):
            raise ValueError('Invalid skill ownership in receipt')
        if not all(valid_tree_record(record) for record in value['skills'].values()):
            raise ValueError('Invalid skill fingerprints in receipt')
        if not isinstance(value.get('transaction_id'), str) or not value['transaction_id'].isalnum():
            raise ValueError('Invalid backup identity in receipt')
        return value

    def clean(self, receipt, force=False):
        if not receipt: return
        changed = [name for name, expected in receipt['skills'].items() if fingerprints(self.dest / name) != expected]
        if changed and not force:
            raise ValueError('Locally modified managed skills; preserve or explicitly --force with a backup: ' + ', '.join(changed))

    def ensure_idle(self):
        if exists(self.journal_path):
            raise ValueError('An interrupted operation exists; run recover before installing or rolling back')

    def status(self):
        value = self.receipt()
        return {'installed': bool(value), 'version': value['version'] if value else None,
                'destination': str(self.dest), 'state': str(self.state),
                'pending_recovery': exists(self.journal_path),
                'changed': [name for name, expected in value['skills'].items()
                            if fingerprints(self.dest / name) != expected] if value else []}

    def restore(self, journal, tx):
        for name, before in journal['before_hashes'].items():
            saved = tx / 'before' / name
            if fingerprints(saved) != before:
                raise ValueError(f'Backup changed; original retained at {saved}')
        for name, before in journal['before_hashes'].items():
            remove_tree(self.dest / name)
            if before is not None: shutil.copytree(tx / 'before' / name, self.dest / name)
        self.commit_receipt(journal['before_receipt'])

    def commit_receipt(self, receipt):
        if receipt is None: self.receipt_path.unlink(missing_ok=True)
        else: atomic_json(self.receipt_path, receipt)

    def transaction(self, targets, after_receipt, before_receipt, expected_targets=None):
        self.dest.mkdir(parents=True, exist_ok=True)
        tx_id = uuid.uuid4().hex
        tx = self.state / 'transactions' / tx_id; tx.mkdir(parents=True)
        before_hashes, after_hashes = {}, {}
        # Copy and hash everything before the first destination mutation.
        for name, source in targets.items():
            before_hashes[name] = fingerprints(self.dest / name)
            if before_hashes[name] is not None:
                shutil.copytree(self.dest / name, tx / 'before' / name)
                if fingerprints(tx / 'before' / name) != before_hashes[name]:
                    raise ValueError(f'Skill changed while backing up: {name}')
            if source is not None:
                expected = tree_hashes(source)
                shutil.copytree(source, tx / 'after' / name)
                if fingerprints(tx / 'after' / name) != expected:
                    raise ValueError(f'Source changed while staging: {name}')
                after_hashes[name] = expected
            else: after_hashes[name] = None
        if expected_targets is not None and after_hashes != expected_targets:
            raise ValueError('Release source changed while staging; no skills were replaced')
        if after_receipt is not None:
            after_receipt = dict(after_receipt, transaction_id=tx_id)
        journal = {'schema': 1, 'destination': str(self.dest), 'transaction_id': tx_id,
                   'before_hashes': before_hashes, 'after_hashes': after_hashes,
                   'before_receipt': before_receipt, 'after_receipt': after_receipt}
        atomic_json(tx / 'transaction.json', journal)
        atomic_json(self.journal_path, journal)
        try:
            for name in targets:
                # An editor may have changed a file after backup: do not overwrite that work.
                if fingerprints(self.dest / name) != before_hashes[name]:
                    raise ValueError(f'Skill changed during installation: {name}; run recover')
                remove_tree(self.dest / name)
                if after_hashes[name] is not None: shutil.copytree(tx / 'after' / name, self.dest / name)
            for name, expected in after_hashes.items():
                if fingerprints(self.dest / name) != expected: raise ValueError(f'Incomplete install: {name}')
            self.commit_receipt(after_receipt)
        except Exception:
            # Retain the journal on failure; recover checks every tree before restoring it.
            raise
        self.journal_path.unlink()
        return {'version': after_receipt['version'] if after_receipt else None,
                'skills': len(after_receipt['skills']) if after_receipt else 0,
                'backup': str(tx), 'transaction_id': tx_id}

    def install(self, source=ROOT, adopt=False, force=False):
        with self.locked():
            plugin, source, before, expected = self.preflight(source, adopt, force)
            if before and before['version'] == plugin['version']:
                if not self.status()['changed']: return dict(self.status(), unchanged=True)
            names = sorted(set(expected) | set(before['skills'] if before else []))
            targets = {name: source / 'skills' / name if name in expected else None for name in names}
            receipt = {'schema': 1, 'destination': str(self.dest), 'name': plugin['name'],
                       'version': plugin['version'], 'skills': expected,
                       'installed_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
            return self.transaction(targets, receipt, before, {name: expected.get(name) for name in names})

    def preflight(self, source=ROOT, adopt=False, force=False):
        plugin, suite, _files = check(Path(source))
        source = Path(source).resolve()
        if self.dest.is_relative_to(source) or self.state.is_relative_to(source):
            raise ValueError('Keep installation/state outside the release source')
        self.ensure_idle(); before = self.receipt(); self.clean(before, force)
        expected = {name: tree_hashes(source / 'skills' / name) for name in suite['skills']}
        if before and before['version'] == plugin['version'] and before['skills'] != expected:
            raise ValueError('This version already identifies different contents; publish a new version')
        unmanaged = [name for name in expected if exists(self.dest / name) and (not before or name not in before['skills'])
                     and fingerprints(self.dest / name) != expected[name]]
        if unmanaged and not adopt:
            raise ValueError('Existing skills differ; use --adopt to back up and migrate them: ' + ', '.join(unmanaged))
        return plugin, source, before, expected

    def preview(self, source=ROOT, adopt=False, force=False):
        """Observe the same preflight and actual trees without a lock or any writes."""
        plugin, suite, _files = check(Path(source))
        before = self.receipt()
        expected = {name: tree_hashes(Path(source)/'skills'/name) for name in suite['skills']}
        blocked = None
        try: self.preflight(source, adopt, force)
        except (OSError, ValueError, KeyError, TypeError) as error: blocked = str(error)
        recorded = before['skills'] if before else {}
        current, errors = {}, {}
        for name in sorted(set(expected) | set(recorded)):
            try: current[name] = fingerprints(self.dest/name)
            except (OSError, ValueError) as error:
                current[name] = None; errors[name] = str(error)
        requires = (not before or before['version'] != plugin['version'] or recorded != expected
                    or bool(errors) or any(current[n] != expected[n] for n in expected))
        rows = []
        for name, actual in current.items():
            wanted = expected.get(name)
            owned = name in recorded
            if name in errors: action = 'UNREADABLE'
            elif not requires: action = 'UNCHANGED'
            elif wanted is None: action = 'REMOVE'
            elif actual is None: action = 'INSTALL'
            elif not owned: action = 'ADOPT_IDENTICAL' if actual == wanted else 'ADOPT'
            elif actual == wanted: action = 'REINSTALL'
            else: action = 'REPLACE'
            actual_files, wanted_files = actual or {}, wanted or {}
            rows.append({'name':name, 'path':str(self.dest/name), 'action':action,
                         'managed_before':owned, 'locally_modified':owned and actual != recorded[name],
                         'current_sha256':digest(json.dumps(actual,sort_keys=True).encode()) if actual is not None else None,
                         'source_sha256':digest(json.dumps(wanted,sort_keys=True).encode()) if wanted is not None else None,
                         'files':None if name in errors else {
                             'added':sorted(set(wanted_files)-set(actual_files)),
                             'removed':sorted(set(actual_files)-set(wanted_files)),
                             'changed':sorted(n for n in set(actual_files)&set(wanted_files) if actual_files[n] != wanted_files[n])},
                         'inspection_error':errors.get(name)})
        return {'eligible':blocked is None and not errors, 'destination':str(self.dest), 'state':str(self.state),
                'current_version':before['version'] if before else None, 'target_version':plugin['version'],
                'requires_transaction':bool(requires), 'options':{'force':force,'adopt':adopt},
                'blocked_reason':blocked or ('Unreadable skill directories' if errors else None), 'skills':rows}

    def recover(self):
        with self.locked():
            if self.journal_path.is_symlink(): raise ValueError('Journal cannot be a symlink')
            if not self.journal_path.exists(): return {'recovered': False}
            journal = load(self.journal_path)
            if not valid_journal(journal, self.dest):
                raise ValueError('Invalid recovery journal')
            tx = self.state / 'transactions' / journal['transaction_id']
            if load(tx / 'transaction.json') != journal:
                raise ValueError('Recovery journal differs from the transaction backup')
            # A crash after receipt commit does not turn a completed upgrade into a rollback.
            if self.receipt() == journal['after_receipt']:
                if all(fingerprints(self.dest / name) == expected for name, expected in journal['after_hashes'].items()):
                    self.journal_path.unlink(); return {'recovered': True, 'committed': True}
            for name, before in journal['before_hashes'].items():
                actual = fingerprints(self.dest / name)
                after = journal['after_hashes'][name]
                partial = actual is not None and after is not None and actual.items() <= after.items()
                if actual is not None and actual not in (before, after) and not partial:
                    raise ValueError(f'New local edits found in {name}; preserve them before recovery')
            self.restore(journal, tx)
            self.journal_path.unlink()
            return {'recovered': True, 'committed': False}

    def rollback(self, force=False):
        with self.locked():
            self.ensure_idle(); before = self.receipt()
            if not before: raise ValueError('No managed installation to roll back')
            self.clean(before, force)
            tx = self.state / 'transactions' / before['transaction_id']
            journal = load(tx / 'transaction.json')
            if (not valid_journal(journal, self.dest) or journal['transaction_id'] != before['transaction_id']
                    or journal['after_receipt'] != before):
                raise ValueError('Invalid or changed rollback transaction')
            targets = {}
            for name, expected in journal['before_hashes'].items():
                source = tx / 'before' / name
                if fingerprints(source) != expected: raise ValueError(f'Backup changed: {name}')
                targets[name] = source if expected is not None else None
            return self.transaction(targets, journal['before_receipt'], before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('install', 'status', 'rollback', 'recover'):
        p = sub.add_parser(command)
        p.add_argument('--agent', nargs='+', help='codex (default), hermes, zcode, deepseek, opencode, pi, shared, or all')
        p.add_argument('--home', type=Path, help='Explicit home/profile base; ignores agent environment overrides')
        p.add_argument('--dest', type=Path, help='Explicit skill directory (one target only)')
        p.add_argument('--state', type=Path, help='Persistent ownership/backup directory; defaults to a sibling .sdd-workbench')
        if command == 'install':
            p.add_argument('--source', type=Path, default=ROOT)
            p.add_argument('--adopt', action='store_true', help='Back up and migrate pre-existing different skills')
            p.add_argument('--dry-run', action='store_true', help='Read-only per-target/skill preview; creates no lock or backup')
        if command in ('install', 'rollback'):
            p.add_argument('--force', action='store_true', help='Back up and replace locally modified managed skills')
    args = parser.parse_args()
    try:
        targets = target_directories(args.agent, args.home)
        if (args.dest or args.state) and len(targets) != 1:
            raise ValueError('--dest/--state requires exactly one agent target')
        if args.command == 'install' and args.dry_run:
            plugin, _suite, files = check(args.source)
            plans = {}
            for name, dest in targets.items():
                try:
                    plans[name] = Installation(args.dest or dest, args.state).preview(args.source,args.adopt,args.force)
                except (OSError, ValueError, KeyError, TypeError) as error:
                    plans[name] = {'eligible':False, 'destination':str(args.dest or dest),
                                   'blocked_reason':str(error), 'skills':[]}
            eligible = all(p['eligible'] for p in plans.values())
            print(json.dumps({'schema':1, 'operation':'INSTALL_PREVIEW', 'read_only':True,
                              'advisory':True, 'eligible':eligible, 'source':{
                                  'path':str(args.source.resolve()), 'declared_version':plugin['version'],
                                  'package_sha256':digest(json.dumps({n:digest(d) for n,d in files.items()},sort_keys=True).encode())},
                              'agents':plans},ensure_ascii=True,indent=2))
            return 0 if eligible else 1
        installations = [(name, Installation(args.dest or dest, args.state)) for name, dest in targets.items()]
        if args.command == 'install':
            # Detect known conflicts across all selected targets before the first
            # write. Each destination still has its own recoverable transaction.
            for _name, installation in installations:
                installation.preflight(args.source, args.adopt, args.force)
        completed = {}
        for name, installation in installations:
            try:
                if args.command == 'install': value = installation.install(args.source, args.adopt, args.force)
                elif args.command == 'rollback': value = installation.rollback(args.force)
                elif args.command == 'recover': value = installation.recover()
                else: value = installation.status()
            except (OSError, ValueError, KeyError, TypeError) as error:
                if completed:
                    print(json.dumps({'completed': completed, 'failed_agent': name, 'error': str(error)}, ensure_ascii=True))
                raise
            completed[name] = value
        result = next(iter(completed.values())) if args.agent is None else {'agents': completed}
        print(json.dumps(result, ensure_ascii=True, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
