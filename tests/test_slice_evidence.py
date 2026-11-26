import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sdd-implement-slice/scripts/evidence.py'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        (self.root / 'design').mkdir()
        self.doc = self.root / 'design/tasks.md'
        self.doc.write_text('# Tasks\n', encoding='utf-8')
        self.log = self.root / 'my trace.md'
        self.log.write_text('# Existing trace\n', encoding='utf-8')
        self.src = self.root / 'jobs.py'
        self.src.write_text('a = 1\n', encoding='utf-8')
        (self.root / 'test_jobs.py').write_text('# tests\n', encoding='utf-8')

    def args(self, ident='s01-red-v1', code="print('ok')", options=()):
        return [sys.executable, '-B', str(SCRIPT), 'record', '--root', str(self.root),
                '--log', self.log.name, '--id', ident, '--source', 'jobs.py',
                '--source', 'test_jobs.py', '--from', 'design/tasks.md', *options,
                '--', sys.executable, '-B', '-c', code]

    def invoke(self, args, rc=0):
        p = subprocess.run(args, capture_output=True, timeout=12)
        self.assertEqual(p.returncode, rc, (p.stdout, p.stderr))
        self.assertTrue(p.stdout, (p.stdout, p.stderr))
        return json.loads(p.stdout)

    def record(self, ident='s01-red-v1', code="print('ok')", options=(), rc=0):
        return self.invoke(self.args(ident, code, options), rc)

    def verify(self, rc=0, *, summary=False):
        return self.invoke([sys.executable, '-B', str(SCRIPT), 'verify', '--root',
                            str(self.root), '--document', 'design/tasks.md',
                            *(['--summary'] if summary else [])], rc)

    def add_link(self, result):
        with self.doc.open('a', encoding='utf-8') as f:
            f.write(result['link'] + '\n')

    def test_real_exits_binary_output_and_current_drift(self):
        bad = self.record(code="import os,sys; os.write(1,b'## sdd-check-trick\\n```\\n\\xff'); os.write(2,b'err\\xfe'); sys.exit(7)")
        self.assertEqual((bad['status'], bad['command_exit']), ('RECORDED', 7))
        self.assertIn('../my%20trace.md#sdd-check-s01-red-v1', bad['link'])
        self.add_link(bad)
        self.add_link(self.record('s01-green-v1'))
        data = [json.loads(line) for line in self.log.read_text('utf-8').splitlines() if line.startswith('{')]
        for stream, expected in [('stdout', b'## sdd-check-trick\n```\n\xff'), ('stderr', b'err\xfe')]:
            parts = [x['data'].encode('utf-8', 'surrogateescape') for x in data if x.get('type') == stream]
            self.assertIn(expected, b''.join(parts))
        links = self.verify()['links']
        self.assertEqual([x['command_exit'] for x in links], [7, 0])
        self.assertTrue(all(x['history'] == 'RECORDED' for x in links))
        self.assertEqual(links[0]['sources']['jobs.py'], 'MATCH')
        self.src.write_text('a = 2\n', encoding='utf-8')
        (self.root / 'test_jobs.py').unlink()
        links = self.verify()['links']
        self.assertEqual(links[0]['sources'], {'jobs.py':'CHANGED','test_jobs.py':'MISSING'})
        self.assertEqual(links[0]['history'], 'RECORDED')

    def test_bounded_output_tails_preserve_full_log_and_child_exit(self):
        out = b'initial stdout:' + b'A' * 21000 + b'out\xc3\xa9'
        err = b'initial stderr:' + b'B' * 9000 + b'err\xfe'
        child = ("import os,sys; os.write(1,b'initial stdout:'+b'A'*21000+b'out\\xc3\\xa9'); "
                 "os.write(2,b'initial stderr:'+b'B'*9000+b'err\\xfe'); sys.exit(23)")
        result = self.record(code=child)
        self.assertEqual(result['command_exit'], 23)
        rows = [json.loads(row) for row in self.log.read_text('utf-8').splitlines() if row.startswith('{')]
        for kind, data in [('stdout',out),('stderr',err)]:
            self.assertEqual(result[kind+'_tail'].encode('utf-8','surrogateescape'), data[-4096:])
            self.assertEqual(b''.join(row['data'].encode('utf-8','surrogateescape')
                                     for row in rows if row.get('type') == kind), data)

    def test_summary_keeps_each_record_target_and_actual_exit_without_writes(self):
        red = self.record(code='raise SystemExit(7)')
        green = self.record('s01-green-v1')
        self.add_link(red)
        self.add_link(red)
        self.add_link(green)
        with self.doc.open('a', encoding='utf-8') as stream:
            stream.write('[trace](../my%20trace.md#existing-trace)\n')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        full = self.verify()
        result = self.verify(summary=True)
        self.assertEqual(set(full), {'status', 'links'})
        self.assertEqual(len(full['links']), 4)
        self.assertEqual({key:result[key] for key in ('status','links_checked','links')},
                         {'status':'VERIFIED', 'links_checked':4, 'links':[
            {'target':'../my%20trace.md#sdd-check-s01-red-v1', 'history':'RECORDED', 'command_exit':7},
            {'target':'../my%20trace.md#sdd-check-s01-red-v1', 'history':'RECORDED', 'command_exit':7},
            {'target':'../my%20trace.md#sdd-check-s01-green-v1', 'history':'RECORDED', 'command_exit':0}]})
        self.assertEqual({p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}, before)

    def test_summary_distribution_counts_omitted_and_duplicate_reference_occurrences(self):
        red = self.record(code='raise SystemExit(7)')
        self.add_link(red)
        self.add_link(red)
        self.add_link(self.record('s01-green-v1'))
        with self.doc.open('a', encoding='utf-8') as stream:
            stream.write('[trace](../my%20trace.md#existing-trace)\n'
                         '[again](../my%20trace.md#existing-trace)\n'
                         '[missing](../my%20trace.md#missing)\n')
        full = self.verify(2)
        result = self.verify(2, summary=True)
        self.assertIn('history_counts', result)
        self.assertEqual(result['history_counts'], {'RECORDED':3,'LINK_OK':2,'MISSING_ANCHOR':1})
        self.assertEqual(result['links_checked'], 6)
        self.assertEqual(sum(result['history_counts'].values()), result['links_checked'])
        self.assertEqual(len(result['links']), 4)
        self.assertEqual([(row['target'],row['command_exit']) for row in result['links']
                          if row['history']=='RECORDED'],
                         [('../my%20trace.md#sdd-check-s01-red-v1',7),
                          ('../my%20trace.md#sdd-check-s01-red-v1',7),
                          ('../my%20trace.md#sdd-check-s01-green-v1',0)])
        self.assertIn('omissions', result)
        self.assertEqual(result['omissions'], {
            'LINK_OK':{'whole_rows':2},
            'RECORDED':{'whole_rows':0, 'field_only_references':3,
                        'fields':['source_changes','sources']}})
        self.assertEqual(set(full['links'][0]) - set(result['links'][0]),
                         set(result['omissions']['RECORDED']['fields']))

    def test_summary_all_ordinary_links_remain_distinct_from_no_local_references(self):
        self.doc.write_text('[trace](../my%20trace.md#existing-trace)\n'
                            '[again](../my%20trace.md#existing-trace)\n', encoding='utf-8')
        result = self.verify(summary=True)
        self.assertIn('history_counts', result)
        self.assertEqual(result['history_counts'], {'LINK_OK':2})
        self.assertEqual(result['status'], 'VERIFIED')
        self.assertEqual(result['links_checked'], 2)
        self.assertEqual(result['links'], [])
        self.assertIn('omissions', result)
        self.assertEqual(result['omissions'], {
            'LINK_OK':{'whole_rows':2},
            'RECORDED':{'whole_rows':0, 'field_only_references':0, 'fields':[]}})

    def test_summary_keeps_execution_changes_even_after_current_source_is_restored(self):
        self.add_link(self.record(code="from pathlib import Path; Path('jobs.py').write_text('altered')"))
        self.src.write_text('a = 1\n', encoding='utf-8')
        result = self.verify(summary=True)
        item = result['links'][0]
        self.assertEqual(item['command_exit'], 0)
        self.assertEqual(item['sources'], {'jobs.py':'MATCH', 'test_jobs.py':'MATCH'})
        self.assertEqual(item['source_changes'], ['jobs.py'])
        self.assertIn('omissions', result)
        self.assertEqual(result['omissions']['RECORDED'],
                         {'whole_rows':0, 'field_only_references':0, 'fields':[]})

    def test_summary_keeps_current_drift_when_recorded_sources_did_not_change(self):
        self.add_link(self.record())
        self.src.write_text('a = 2\n', encoding='utf-8')
        (self.root/'test_jobs.py').unlink()
        result = self.verify(summary=True)
        self.assertEqual(result['status'], 'VERIFIED')
        self.assertEqual(result['links'][0]['source_changes'], [])
        self.assertEqual(result['links'][0]['sources'], {'jobs.py':'CHANGED', 'test_jobs.py':'MISSING'})
        self.assertEqual(result['links'][0]['history'], 'RECORDED')
        self.assertIn('omissions', result)
        self.assertEqual(result['omissions']['RECORDED'],
                         {'whole_rows':0, 'field_only_references':0, 'fields':[]})

    def test_summary_does_not_hide_broken_or_incomplete_evidence(self):
        self.add_link(self.record(code="print('original-value')"))
        self.add_link(self.record('interrupted', code='import time; time.sleep(10)',
                                  options=['--timeout','0.1'], rc=2))
        self.log.write_bytes(self.log.read_bytes().replace(b'original-value', b'tampered-value'))
        with self.doc.open('a', encoding='utf-8') as stream:
            stream.write('[missing](../my%20trace.md#missing)\n'
                         '[unsupported](\nmissing.md)\n'
                         '[trace](../my%20trace.md#existing-trace)\n')
        full = self.verify(2)
        result = self.verify(2, summary=True)
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertEqual(result['links_checked'], 5)
        self.assertEqual({row['history'] for row in result['links']},
                         {'INVALID','INCOMPLETE','MISSING_ANCHOR','UNSUPPORTED'})
        self.assertIn('digest mismatch', next(row['error'] for row in result['links']
                                            if row['history']=='INVALID'))
        self.assertEqual(result['links'], [row for row in full['links'] if row['history']!='LINK_OK'])
        self.assertIn('history_counts', result)
        self.assertEqual(result['history_counts'], {'UNSUPPORTED':1,'INVALID':1,'INCOMPLETE':1,
                                                   'MISSING_ANCHOR':1,'LINK_OK':1})

    def test_summary_empty_document_and_top_level_errors_keep_failure_exit(self):
        result = self.verify(2, summary=True)
        self.assertEqual({key:result[key] for key in ('status','links_checked','links')},
                         {'status':'NO_LOCAL_REFERENCES', 'links_checked':0, 'links':[]})
        self.assertIn('history_counts', result)
        self.assertEqual(result['history_counts'], {})
        self.assertIn('omissions', result)
        self.assertEqual(result['omissions'], {
            'LINK_OK':{'whole_rows':0},
            'RECORDED':{'whole_rows':0, 'field_only_references':0, 'fields':[]}})
        self.doc.unlink()
        error = self.verify(2, summary=True)
        self.assertEqual(error['status'], 'ERROR')
        self.assertIn('error', error)
        self.assertNotIn('links', error)
        self.assertNotIn('history_counts', error)
        self.assertNotIn('omissions', error)

    def test_duplicate_id_never_reruns_and_digest_tampering_is_visible(self):
        self.add_link(self.record(code="print('original-value')"))
        prior = self.log.read_bytes()
        self.record(code="open('forbidden','w').close()", rc=2)
        self.assertEqual(self.log.read_bytes(), prior)
        self.assertFalse((self.root / 'forbidden').exists())
        self.log.write_bytes(prior.replace(b'original-value', b'tampered-value'))
        self.assertEqual(self.verify(2)['links'][0]['history'], 'INVALID')

    def test_actual_links_duplicate_missing_fences_and_external(self):
        self.add_link(self.record())
        with self.log.open('a',encoding='utf-8') as f:
            f.write('\n## sdd-check-s01-red-v1\n')
        with self.doc.open('a',encoding='utf-8') as f:
            f.write('[missing](../my%20trace.md#missing)\n[gone](gone.md)\n'
                    '[plain](../my%20trace.md#existing-trace)\n'
                    '`[example](ignored.md)`\n~~~\n[fake](ignored.md)\n~~~\n[web](https://example.org)\n')
        links = self.verify(2)['links']
        self.assertEqual([x['history'] for x in links], ['AMBIGUOUS','MISSING_ANCHOR','MISSING_FILE','LINK_OK'])

    def test_nested_receipt_continuation_reports_missing_anchor(self):
        good = '[log](../my%20trace.md#existing-trace)'
        failed = '[post-repair](../my%20trace.md#bad-repair)'
        self.doc.write_text(f'{good}\n\n- Repair\n  - Observed exit 0. Raw record:\n'
                            f'    {failed}\n', encoding='utf-8')
        self.assertEqual([link['history'] for link in self.verify(2)['links']],
                         ['LINK_OK', 'MISSING_ANCHOR'])

    def test_code_formatted_link_labels_are_checked(self):
        good = '[log](../my%20trace.md#existing-trace)'
        for label in ('`sdd-check-s01`', '``sdd-check-s01``', '`[raw label]`'):
            with self.subTest(label=label):
                self.doc.write_text(f'{good}\n[{label}](../my%20trace.md#missing)\n'
                                    '`[literal example](absent.md)`\n', encoding='utf-8')
                self.assertEqual([link['history'] for link in self.verify(2)['links']],
                                 ['LINK_OK', 'MISSING_ANCHOR'])

    def test_code_labels_keep_reference_identity(self):
        self.doc.write_text('[log](../my%20trace.md#existing-trace)\n'
                            '[`missing`][target]\n[`shortcut`]\n'
                            '[target]: ../my%20trace.md#missing\n'
                            '[`shortcut`]: ../my%20trace.md#missing-too\n', encoding='utf-8')
        self.assertEqual([link['history'] for link in self.verify(2)['links']],
                         ['LINK_OK', 'MISSING_ANCHOR', 'MISSING_ANCHOR'])

    def test_link_titles_and_empty_labels_do_not_hide_missing_targets(self):
        for citation in ("[check](../my%20trace.md#missing 'receipt')",
                         '[check](../my%20trace.md#missing (receipt))',
                         '[](../my%20trace.md#missing)'):
            with self.subTest(citation=citation):
                self.doc.write_text('[log](../my%20trace.md#existing-trace)\n'+citation,
                                    encoding='utf-8')
                self.assertEqual([link['history'] for link in self.verify(2)['links']],
                                 ['LINK_OK', 'MISSING_ANCHOR'])

    def test_unsupported_multiline_link_prevents_verified_status(self):
        self.doc.write_text('[log](../my%20trace.md#existing-trace)\n'
                            '[check](\n../my%20trace.md#missing)\n', encoding='utf-8')
        result = self.verify(2)
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertIn('UNSUPPORTED', [link['history'] for link in result['links']])

    def test_escaped_backticks_do_not_hide_a_live_link(self):
        for count in (1, 2, 3):
            with self.subTest(backslashes=count):
                escape = '\\' * count
                self.doc.write_text('[log](../my%20trace.md#existing-trace)\n'
                                    f'{escape}`[check](../my%20trace.md#missing){escape}`\n',
                                    encoding='utf-8')
                histories = [link['history'] for link in self.verify(2 if count % 2 else 0)['links']]
                self.assertEqual(histories, ['LINK_OK', 'MISSING_ANCHOR'] if count % 2 else ['LINK_OK'])

    def test_list_containers_exclude_real_code_and_keep_ordered_continuations(self):
        good = '[log](../my%20trace.md#existing-trace)'
        code = '[literal example](not-a-real-document.md)'
        text = (f'    {code}\n\n'
                f'10. Stage\n    * Receipt\n      {good}\n'
                f'      `{code}`\n\n          {code}\n\n'
                f'      ```md\n      {code}\n      ```\n'
                f'    + Another check\n      {good}\n\n'
                f'Next section.\n\n    {code}\n\n{good}\n')
        self.doc.write_text(text, encoding='utf-8')
        self.assertEqual([link['history'] for link in self.verify()['links']], ['LINK_OK'] * 3)

    def test_indented_paragraph_and_quoted_fences(self):
        good = '[log](../my%20trace.md#existing-trace)'
        code = '[example](missing.md)'
        self.doc.write_text(f'Raw record follows on the next line:\n    {good}\n\n'
                            f'> - In a quote\n>   - Nested receipt\n>     {good}\n'
                            f'>     ~~~md\n>     {code}\n>     ~~~\n\n'
                            f'> ~~~\n> {code}\n\n{good}\n', encoding='utf-8')
        self.assertEqual([link['history'] for link in self.verify()['links']], ['LINK_OK'] * 3)

    def test_source_changed_during_check(self):
        note = self.record(code="from pathlib import Path; Path('jobs.py').write_text('altered')")
        self.assertEqual(note['source_changes'], ['jobs.py'])
        self.add_link(note)
        fact = self.verify()['links'][0]
        self.assertEqual(fact['source_changes'], ['jobs.py'])
        self.assertEqual(fact['sources']['jobs.py'], 'CHANGED')

    def test_timeout_is_incomplete_and_retry_uses_new_id(self):
        bad = self.record(code="import time; print('started',flush=True); time.sleep(20)", options=['--timeout','0.3'], rc=2)
        self.assertEqual(bad['status'], 'INCOMPLETE')
        self.add_link(bad)
        self.assertEqual(self.verify(2)['links'][0]['history'], 'INCOMPLETE')
        self.record(rc=2)
        self.add_link(self.record('next'))
        self.assertEqual(self.verify(2)['links'][1]['history'], 'RECORDED')

    def test_open_ordinary_markdown_fence_refuses_before_execution(self):
        self.log.write_bytes(b'Existing text\n  ````python\n  ```\n')
        prior = self.log.read_bytes()
        self.record(code="open('forbidden','w').close()",rc=2)
        self.assertEqual(prior,self.log.read_bytes())
        self.assertFalse((self.root/'forbidden').exists())

    def test_concurrent_lock_and_abrupt_termination(self):
        # No child process is left alive when the helper itself is killed.
        script = "import pathlib,time; pathlib.Path('ready').touch(); p=pathlib.Path('release');\nwhile not p.exists(): time.sleep(.02)"
        child = subprocess.Popen(self.args(code=script),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+6
            # Windows byte-range locks reject reads of the locked log as well.
            while not (self.root/'ready').exists() and time.monotonic()<deadline:
                if child.poll() is not None: break
                time.sleep(.03)
            self.assertIsNone(child.poll())
            self.assertTrue((self.root/'ready').exists())
            self.record('other', code="open('forbidden','w').close()",rc=2)
            self.assertFalse((self.root/'forbidden').exists())
            child.kill()
            child.communicate(timeout=4)
        finally:
            (self.root/'release').touch()
            if child.poll() is None: child.kill()
            child.communicate(timeout=4)
        self.record(rc=2)
        next_note=self.record('resumed')
        self.doc.write_text('[original](../my%20trace.md#sdd-check-s01-red-v1)\n'+next_note['link'],encoding='utf-8')
        self.assertEqual([x['history'] for x in self.verify(2)['links']],['INCOMPLETE','RECORDED'])

    def test_paths_do_not_escape_or_follow_symlinks(self):
        outside = self.root.parent/'outside.md'
        outside.write_text('private',encoding='utf-8')
        for option,value in [('--log','../outside.md'),('--source','../outside.md'),('--from','../outside.md')]:
            args=self.args(code="open('forbidden','w').close()")
            args[args.index(option)+1]=value
            self.invoke(args,2)
        self.assertFalse((self.root/'forbidden').exists())
        self.assertEqual(outside.read_bytes(),b'private')
        self.doc.write_text('[outside](../../outside.md#private)',encoding='utf-8')
        self.assertEqual(self.verify(2)['links'][0]['history'],'INVALID')
        try: (self.root/'linked.md').symlink_to(outside)
        except OSError: self.skipTest('symlinks unavailable')
        for option in ['--log','--source']:
            args=self.args();args[args.index(option)+1]='linked.md';self.invoke(args,2)
        self.assertEqual(outside.read_bytes(),b'private')

    def test_reference_links_and_shortcuts_resolve_from_definitions(self):
        self.add_link(self.record())
        with self.doc.open('a',encoding='utf-8') as f:
            f.write('[bad link][my BUG]\n[alias][]\n[shortcut]\n'
                    '[my bug]: ../wrong.md#missing\n'
                    '[alias]: <../my%20trace.md#existing-trace>\n'
                    '[shortcut]: ../my%20trace.md#sdd-check-s01-red-v1 "old proof"\n')
        items=self.verify(2)['links']
        self.assertEqual([x['history'] for x in items], ['RECORDED','MISSING_FILE','LINK_OK','RECORDED'])

    def test_source_replaced_by_symlink_keeps_historical_evidence(self):
        self.add_link(self.record())
        self.src.unlink()
        try: self.src.symlink_to(self.root.parent/'not-in-project')
        except OSError: self.skipTest('symlinks unavailable')
        item=self.verify()['links'][0]
        self.assertEqual(item['history'],'RECORDED')
        self.assertEqual(item['sources']['jobs.py'],'CHANGED')
        self.assertEqual(self.verify(summary=True)['links'][0], item)
        self.assertIn('jobs.py', item['source_errors'])

    @unittest.skipUnless(os.name=='posix','Signal handling applies to POSIX termination')
    def test_sigterm_cleans_up_direct_child(self):
        code = "import time; from pathlib import Path; print('ready',flush=True); time.sleep(.70); Path('late').touch()"
        child = subprocess.Popen(self.args(code=code),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+4
            while b'"stdout"' not in self.log.read_bytes() and time.monotonic()<deadline:
                time.sleep(.02)
            self.assertIn(b'"stdout"',self.log.read_bytes())
            child.terminate()
            output,errors=child.communicate(timeout=3)
            self.assertEqual(child.returncode,2,(output,errors))
            self.assertEqual(json.loads(output)['status'],'INCOMPLETE')
            time.sleep(.72)
            self.assertFalse((self.root/'late').exists())
        finally:
            if child.poll() is None: child.kill()
            child.communicate(timeout=3)

    def test_crlf_markdown_transfer_preserves_escaped_native_bytes(self):
        self.add_link(self.record(code="import os; os.write(1,b'line\\r\\nend')"))
        self.log.write_bytes(self.log.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        self.assertEqual(self.verify()['links'][0]['history'],'RECORDED')

    def test_ordinary_closure_can_be_followed_without_helper_links(self):
        self.doc.write_text('[slice closure](../my%20trace.md#existing-trace)',encoding='utf-8')
        self.assertEqual(self.verify()['links'][0]['history'],'LINK_OK')
        self.doc.write_text('[external](https://example.org)',encoding='utf-8')
        self.assertEqual(self.verify(2)['status'],'NO_LOCAL_REFERENCES')

    def test_resigned_malformed_metadata_is_invalid(self):
        self.add_link(self.record())
        template = self.log.read_text(encoding='utf-8').splitlines(keepends=True)
        start, end = (next(i for i,line in enumerate(template) if line.startswith('{"type":"'+kind+'"'))
                      for kind in ('start','end'))
        def line(obj):
            return json.dumps(obj,separators=(',',':'),ensure_ascii=True)+'\n'
        for which,field,value in [(start,'schema',True),(start,'argv','python'),
                                  (start,'argv',[42]),(start,'id','s01_bad'),
                                  (start,'started_at',True),(end,'ended_at',42)]:
            with self.subTest(field=field,value=value):
                lines=template.copy()
                metadata=json.loads(lines[which])
                metadata[field]=value
                lines[which]=line(metadata)
                if field=='id':
                    lines=[r.replace('## sdd-check-s01-red-v1','## sdd-check-s01_bad') for r in lines]
                    self.doc.write_text('[x](../my%20trace.md#sdd-check-s01_bad)',encoding='utf-8')
                else:
                    self.doc.write_text('[x](../my%20trace.md#sdd-check-s01-red-v1)',encoding='utf-8')
                footer=json.loads(lines[end])
                del footer['sha256']
                footer['sha256']=hashlib.sha256((''.join(lines[start:end])+line(footer)).encode()).hexdigest()
                lines[end]=line(footer)
                self.log.write_text(''.join(lines),encoding='utf-8')
                self.assertEqual(self.verify(2)['links'][0]['history'],'INVALID')

    def test_uncreated_sources_and_link_origin(self):
        self.src.unlink()
        self.doc.unlink()
        red = self.record(code="import sys; sys.exit(1)")
        self.assertFalse(self.doc.exists())
        self.add_link(red)
        first = self.verify()['links'][0]
        self.assertEqual(first['sources']['jobs.py'], 'MISSING')
        self.src.write_text('implemented',encoding='utf-8')
        self.assertEqual(self.verify()['links'][0]['sources']['jobs.py'],'CHANGED')
        self.assertEqual(self.verify()['links'][0]['history'],'RECORDED')

    def test_ordinary_heading_aliases_and_no_markdown_links_in_code(self):
        self.add_link(self.record())
        with self.log.open('a',encoding='utf-8') as f:
            f.write('\n## Notes\n\n## Notes\n\nOverview\n--------\n')
        with self.doc.open('a',encoding='utf-8') as f:
            f.write('[second](../my%20trace.md#notes-1)\n[first](../my%20trace.md#notes)\n'
                    '[setext](../my%20trace.md#overview)\n')
        self.assertEqual([x['history'] for x in self.verify()['links']],
                         ['RECORDED','LINK_OK','LINK_OK','LINK_OK'])

    def test_external_in_place_edit_is_not_successfully_sealed(self):
        code = "with open('my trace.md','a') as f: f.write('manual concurrent note\\n')"
        result = self.record(code=code, rc=2)
        self.assertIn('manual concurrent note',self.log.read_text())
        self.assertIn('modifi',result['error'].lower())

    def test_start_failure_and_ordinary_dangling_links_preserved(self):
        args = self.args()
        del args[args.index('--')+1:]
        args.append(str(self.root/'missing-program'))
        hit = self.invoke(args,2)
        self.assertEqual(hit['status'],'INCOMPLETE')
        self.add_link(hit)
        self.assertEqual(self.verify(2)['links'][0]['history'],'INCOMPLETE')

    @unittest.skipUnless(os.name=='posix','Unix permits renaming an open locked file')
    def test_replaced_log_reports_conflict_and_preserves_replacement(self):
        code = "from pathlib import Path; p=Path('my trace.md'); p.rename('retained.md'); p.write_text('replacement')"
        result=self.record(code=code,rc=2)
        self.assertIn('replac',result['error'].lower())
        self.assertEqual(self.log.read_text(), 'replacement')
        self.assertNotIn('"type":"end"',(self.root/'retained.md').read_text())
