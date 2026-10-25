#!/usr/bin/env python3
"""Validate, version and reproducibly package SDD Workbench with the stdlib."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?')
ROOT_FILES = ('plugin.json', 'suite.json', 'README.md', 'CHANGELOG.md', 'AGENTS.md', 'THIRD_PARTY_NOTICES.md',
              'package.json', 'package-lock.json', 'CONTRIBUTING.md', 'SECURITY.md')
MULTI_FILES = ('agent-targets.json', 'marketplace.json', 'cordis.patch.yml', '.npmignore')
TREES = ('skills', 'tools', 'tests', 'docs', 'adapters', '.codex-plugin', '.agents/plugins', '.zcode-plugin')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def valid_name(name):
    return isinstance(name, str) and re.fullmatch(r'sdd-[a-z0-9]+(?:-[a-z0-9]+)*', name) is not None


def tree_hashes(root):
    root = Path(root)
    if root.is_symlink():
        raise ValueError(f'Symlinks are not installable: {root}')
    if not root.is_dir():
        raise ValueError(f'Skill directory is missing: {root}')
    result = {}
    for path in sorted(root.rglob('*')):
        if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo') or path.name == '.DS_Store':
            continue
        if path.is_symlink():
            raise ValueError(f'Symlinks are not installable: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return result


def bundle_files(root=ROOT):
    paths = [root / name for name in ROOT_FILES]
    paths += [root / name for name in MULTI_FILES if (root / name).exists()]
    for name in TREES:
        base = root / name
        paths += sorted(base.rglob('*'))
    result = {}
    for path in paths:
        relative = path.relative_to(root)
        if relative.parts[:2] in (('docs', 'optimization'), ('docs', 'releases')):
            continue
        if any(part in ('__pycache__', 'node_modules', '.git') for part in path.parts) or path.suffix in ('.pyc', '.pyo') or path.name == '.DS_Store':
            continue
        if path.is_symlink():
            raise ValueError(f'Package cannot contain symlinks: {path}')
        if path.is_file():
            if path.suffix in ('.sqlite3', '.db', '.pem', '.log') or path.name == '.env':
                raise ValueError(f'Runtime/private state in package: {path}')
            data = path.read_bytes()
            if path.name.lower().endswith(('.sdd-review.json', '.sdd-review-candidate.json')):
                raise ValueError(f'Runtime review data in package: {path}')
            # Runtime reports can be renamed or use JSON's supported encodings.
            # Inspect the known format marker rather than trusting the extension.
            try: value = json.loads(data)
            except (ValueError, UnicodeError, RecursionError): value = None
            if isinstance(value, dict) and value.get('kind') in ('sdd-review-report', 'sdd-review-candidate'):
                raise ValueError(f'Runtime review data in package: {path}')
            result[relative.as_posix()] = data
    for name in ROOT_FILES:
        if name not in result:
            raise ValueError(f'Missing package file: {name}')
    return dict(sorted(result.items()))


def check_adapters(root, plugin):
    """Adapter metadata projects the same suite; no platform owns a skill copy."""
    zcode = load(root / '.zcode-plugin/plugin.json')
    for field in ('name', 'version', 'description', 'author', 'repository'):
        if zcode.get(field) != plugin.get(field):
            raise ValueError(f'ZCode manifest drift: {field}')
    if zcode.get('skills') != './skills/':
        raise ValueError('ZCode must load the shared skills tree')
    marketplace = load(root / 'marketplace.json')
    if marketplace != load(root / '.zcode-plugin/marketplace.json'):
        raise ValueError('ZCode marketplace projections differ')
    entries = marketplace.get('plugins', [])
    if (marketplace.get('name') != plugin['name'] or len(entries) != 1
            or entries[0].get('name') != plugin['name'] or entries[0].get('source') != './'
            or entries[0].get('version') != plugin['version']):
        raise ValueError('Marketplace must identify this complete versioned suite')
    node, lock = load(root / 'package.json'), load(root / 'package-lock.json')
    if (node.get('name') != plugin['name'] or node.get('version') != plugin['version']
            or lock.get('name') != node['name'] or lock.get('version') != node['version']
            or lock.get('packages', {}).get('', {}).get('version') != node['version']):
        raise ValueError('Node package version/name projection drift')
    if node.get('pi', {}).get('skills') != ['./skills']:
        raise ValueError('Pi must load the shared skills tree')
    if (node.get('main') != './adapters/deepseek.mjs'
            or node.get('exports', {}).get('.') != './adapters/deepseek.mjs'
            or node.get('dsh', {}).get('bundle', {}).get('patch') != './cordis.patch.yml'
            or not (root / 'adapters/deepseek.mjs').is_file()
            or (root / 'cordis.patch.yml').read_text(encoding='utf-8') !=
                '- insert:\n    - id: sdd-workbench-skills\n      name: sdd-workbench\n'):
        raise ValueError('DeepSeek bundle/entrypoint drift')
    registry = load(root / 'agent-targets.json')
    if registry.get('schema') != 1 or set(registry.get('targets', {})) != {
            'codex', 'hermes', 'zcode', 'deepseek', 'opencode', 'pi', 'shared'}:
        raise ValueError('Expected six agent targets and the shared target')
    aliases = set(registry['targets']) | {'all'}
    for target in registry['targets'].values():
        if 'reads_shared' in target and not isinstance(target['reads_shared'], bool):
            raise ValueError('Shared discovery capability must be boolean')
        if 'command' in target and (not isinstance(target['command'], str)
                or not re.fullmatch(r'[a-z][a-z0-9-]*', target['command'])):
            raise ValueError('Agent command must be a plain executable name')
        if 'path' not in target or ('env' in target) != ('env_path' in target):
            raise ValueError('Agent target needs a path and paired environment override')
        for key in ('path', 'env_path'):
            if key in target:
                value = target[key]
                if not isinstance(value, str) or '\\' in value or ':' in value:
                    raise ValueError('Agent skill paths must use home-relative POSIX syntax')
                path = PurePosixPath(value)
                if path.is_absolute() or '..' in path.parts or not path.parts:
                    raise ValueError('Agent skill paths must be safe home-relative paths')
        for alias in target.get('aliases', []):
            if alias in aliases:
                raise ValueError('Duplicate agent target alias')
            aliases.add(alias)


def bump_version(version, root=ROOT):
    if not VERSION.fullmatch(version):
        raise ValueError('Invalid semantic version')
    root = Path(root)
    for name in ('plugin.json', '.codex-plugin/plugin.json', '.zcode-plugin/plugin.json', 'package.json'):
        path = root / name
        if path.exists():
            value = load(path); value['version'] = version
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    path = root / 'package-lock.json'
    value = load(path); value['version'] = version; value['packages']['']['version'] = version
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name in ('marketplace.json', '.zcode-plugin/marketplace.json'):
        path = root / name
        if path.exists():
            value = load(path); value['plugins'][0]['version'] = version
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check(root=ROOT):
    root = Path(root).resolve()
    plugin, suite = load(root / 'plugin.json'), load(root / 'suite.json')
    compatibility = load(root / '.codex-plugin/plugin.json')
    if plugin['name'] != 'sdd-workbench' or suite['name'] != plugin['name'] or suite.get('schema') != 1:
        raise ValueError('Inconsistent suite identity')
    if not VERSION.fullmatch(plugin['version']):
        raise ValueError('Use a semantic version such as 0.1.0')
    for field in ('name', 'version', 'description', 'author', 'repository'):
        if compatibility.get(field) != plugin.get(field):
            raise ValueError(f'Compatibility manifest drift: {field}')
    if compatibility.get('skills') != './skills/' or compatibility.get('interface') != plugin['extensions']['com.openai']['interface']:
        raise ValueError('Compatibility components or presentation drift')
    if tuple(map(int, plugin['version'].split('-')[0].split('.'))) >= (0, 2, 0):
        check_adapters(root, plugin)
    names = suite['skills']
    if not isinstance(names, list) or not names or any(not valid_name(name) for name in names) or len(names) != len(set(names)):
        raise ValueError('Suite needs unique, safe skill names')
    actual = {p.name for p in (root / 'skills').iterdir() if p.is_dir() and p.name != '__pycache__'}
    if set(names) != actual or suite['primary_skill'] not in names:
        raise ValueError('Suite catalog differs from packaged skill directories')
    for name in names:
        tree_hashes(root / 'skills' / name)
        text = (root / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8')
        front = text.split('---', 2)
        if len(front) != 3 or front[0].strip():
            raise ValueError(f'Missing frontmatter: {name}')
        match = re.search(r'^name:\s*[\'\"]?([a-z0-9-]+)[\'\"]?\s*$', front[1], re.M)
        if not match or match[1] != name or not re.search(r'^description:\s*\S', front[1], re.M):
            raise ValueError(f'Invalid skill metadata: {name}')
    market = load(root / '.agents/plugins/marketplace.json')
    entry = market['plugins']
    if market['name'] != plugin['name'] or len(entry) != 1 or entry[0]['name'] != plugin['name'] or entry[0]['source'] != {'source': 'local', 'path': './'}:
        raise ValueError('Marketplace must expose exactly this complete suite')
    vendor = root / 'skills/sdd-workflow-router/scripts/project_view_lib/vendor'
    provenance = load(vendor / 'provenance.json')
    if digest(gzip.decompress((vendor / 'mermaid-12.2.0.min.js.gz').read_bytes())) != provenance['sha256']:
        raise ValueError('Bundled Mermaid differs from its upstream identity')
    files = bundle_files(root)
    if (root / 'package-manifest.json').exists():
        manifest = load(root / 'package-manifest.json')
        if (manifest.get('schema') != 1 or manifest.get('name') != plugin['name']
                or manifest.get('version') != plugin['version'] or manifest.get('skills') != names
                or manifest['files'] != {name: digest(data) for name, data in files.items()}):
            raise ValueError('Extracted package differs from its release manifest')
    return plugin, suite, files


def build(root=ROOT, output=None):
    plugin, suite, files = check(root)
    manifest = {'schema': 1, 'name': plugin['name'], 'version': plugin['version'],
                'skills': suite['skills'], 'files': {name: digest(data) for name, data in files.items()}}
    raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    output = Path(output or root / 'dist'); output.mkdir(parents=True, exist_ok=True)
    stem = f'{plugin["name"]}-v{plugin["version"]}'
    archive = output / (stem + '.zip')
    metadata = output / (stem + '.manifest.json')
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED, compresslevel=9) as zipped:
        for name, data in sorted(dict(files, **{'package-manifest.json': raw}).items()):
            entry = ZipInfo(plugin['name'] + '/' + name, date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED; entry.external_attr = 0o100644 << 16
            zipped.writestr(entry, data, compresslevel=9)
    metadata.write_bytes(raw)
    (output / 'SHA256SUMS').write_text(''.join(f'{digest(p.read_bytes())}  {p.name}\n' for p in (archive, metadata)), encoding='utf-8')
    verify(archive)
    return archive


def verify(archive):
    with ZipFile(archive) as zipped:
        names = zipped.namelist()
        if (len(names) != len(set(names)) or any(not name.startswith('sdd-workbench/') or '\\' in name
                or '..' in PurePosixPath(name).parts for name in names)
                or any((entry.external_attr >> 16) & 0o170000 == 0o120000 for entry in zipped.infolist())):
            raise ValueError('Invalid or duplicate archive paths')
        if sum(i.file_size for i in zipped.infolist()) > 128 * 1024 * 1024:
            raise ValueError('Archive is unexpectedly large')
        manifest = json.loads(zipped.read('sdd-workbench/package-manifest.json'))
        actual = {name.removeprefix('sdd-workbench/'): digest(zipped.read(name)) for name in names
                  if name != 'sdd-workbench/package-manifest.json'}
        if manifest['files'] != actual:
            raise ValueError('Release file hashes differ from the manifest')
        plugin = json.loads(zipped.read('sdd-workbench/plugin.json'))
        if manifest['name'] != plugin['name'] or manifest['version'] != plugin['version']:
            raise ValueError('Release version identity differs')
        return manifest


def release_notes(root=ROOT):
    version = load(root / 'plugin.json')['version']
    text = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    match = re.search(r'^## \[' + re.escape(version) + r'\][^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if not match or not match[1].strip():
        raise ValueError(f'Write CHANGELOG.md notes for {version} first')
    return match[1].strip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    p = sub.add_parser('build'); p.add_argument('--output', type=Path)
    p = sub.add_parser('verify'); p.add_argument('archive', type=Path)
    p = sub.add_parser('bump'); p.add_argument('version')
    p = sub.add_parser('notes'); p.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'bump':
            bump_version(args.version)
            print(args.version)
        elif args.command == 'notes':
            notes = release_notes()
            if args.output: args.output.write_text(notes, encoding='utf-8')
            else: print(notes, end='')
        elif args.command == 'verify':
            print(json.dumps({'verified': str(args.archive), 'version': verify(args.archive)['version']}))
        elif args.command == 'build':
            print(build(output=args.output))
        else:
            plugin, suite, files = check()
            print(json.dumps({'name': plugin['name'], 'version': plugin['version'], 'skills': len(suite['skills']), 'files': len(files)}))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
