#!/usr/bin/env python3
"""Generate or update an immutable offline project view using Python 3.10+ only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote
from project_view_lib import evidence, renderer, lifecycle, decisions, workstream, stage_details

HERE=Path(__file__).resolve().parent
FILES={'index.html','view.md','snapshot.json'}

def sha(data):return hashlib.sha256(data).hexdigest()

def validate(snapshot):
    if not isinstance(snapshot,dict):raise ValueError('Snapshot must be an object')
    for key in ('project_id','title','scope','captured_at'):
        if not isinstance(snapshot.get(key),str) or not snapshot[key].strip():raise ValueError(f'{key} must be a nonempty string')
    if not isinstance(snapshot.get('items'),list):raise ValueError('items must be a list')
    for item in snapshot['items']:
        if not isinstance(item,dict):raise ValueError('Each item must be an object')
        for key in ('id','label','state','view','kind'):
            if not isinstance(item.get(key),str) or not item[key]:raise ValueError(f'Item {key} must be a nonempty string')
        for key in ('note','next','next_label','group','sublabel','from','to','file','artifact','mermaid','technical_mermaid','review_note'):
            if key in item and not isinstance(item[key],str):raise ValueError(f'Item {key} must be a string')
        if 'implementation_ids' in item and (not isinstance(item['implementation_ids'],list)
                or any(not isinstance(value,str) for value in item['implementation_ids'])):
            raise ValueError('implementation_ids must be a list of IDs')
        if 'related_ids' in item and (not isinstance(item['related_ids'],list)
                or any(not isinstance(value,str) for value in item['related_ids'])):
            raise ValueError('related_ids must be a list of IDs')
        if not isinstance(item.get('sources',[]),list) or any(not isinstance(r,dict) for r in item.get('sources',[])):
            raise ValueError('Item sources must be a list of objects')
    if 'next_id' in snapshot:
        choice=next((i for i in snapshot['items'] if i['id']==snapshot['next_id']),None)
        if choice is None or not choice.get('next','').strip():
            raise ValueError('next_id must identify an existing item with a concrete next action')
    lifecycle.validate(snapshot)
    decisions.validate(snapshot)
    workstream.validate(snapshot)
    stage_details.validate(snapshot)
    return snapshot


def previous_version(path):
    raw=(path/'receipt.json').read_bytes();receipt=json.loads(raw)
    if not isinstance(receipt,dict) or receipt.get('schema')!=1 or not isinstance(receipt.get('files'),dict) or set(receipt['files'])!=FILES:
        raise ValueError('Previous version has no supported complete receipt')
    for name,digest in receipt['files'].items():
        target=path/name
        if target.is_symlink() or not target.is_file() or sha(target.read_bytes())!=digest:
            raise ValueError(f'Previous version changed: {name}')
    data=(path/'snapshot.json').read_bytes();snapshot=validate(json.loads(data))
    if snapshot['project_id']!=receipt.get('project_id'):raise ValueError('Previous project identity differs from receipt')
    return data,snapshot,sha(raw)


def changes(old,new,items):
    before={i['id']:i for i in old.get('items',[])};after={i['id']:i for i in new['items']}
    return {'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),
            'modified':sorted(i for i in before.keys()&after.keys() if before[i]!=after[i]),
            'source_invalidated':sorted(i['id'] for i in items if i['freshness']!='CURRENT')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','render','update'])
    parser.add_argument('--root',type=Path,required=True,help='Source trust boundary; all source paths are relative to this existing directory')
    parser.add_argument('--input',type=Path,help='Observation JSON; update without input only rechecks the previous observations')
    parser.add_argument('--output',type=Path,help='New version directory; existing paths are never overwritten')
    parser.add_argument('--previous',type=Path,help='Complete preceding version directory (update only)')
    parser.add_argument('--reason',help='Reason for new observations or a relocated source root during update')
    args=parser.parse_args()
    try:
        root=args.root.resolve()
        if not root.is_dir():raise ValueError('Source root must be an existing directory')
        old={};previous=None
        if args.command=='update':
            if args.previous is None:raise ValueError('update requires --previous')
            parent=args.previous.resolve();old_bytes,old,parent_hash=previous_version(parent)
            data=args.input.read_bytes() if args.input else old_bytes
            snapshot=validate(json.loads(data))
            if snapshot['project_id']!=old['project_id']:raise ValueError('Update must retain project_id; create a new view for a different project')
            old_root=json.loads((parent/'receipt.json').read_bytes())['source_root']
            if (data!=old_bytes or str(root)!=old_root) and not (args.reason or '').strip():
                raise ValueError('Changed observations or source root require --reason; never silently refresh fingerprints')
            previous={'path':str(parent),'receipt_sha256':parent_hash}
        else:
            if args.previous is not None:raise ValueError('--previous is valid only for update')
            if args.input is None:raise ValueError('check/render requires --input')
            data=args.input.read_bytes();snapshot=validate(json.loads(data))
        items=evidence.inspect(root,snapshot)
        code=0 if all(i['freshness']=='CURRENT' for i in items) else 2
        if args.command=='check':
            print(json.dumps(items,ensure_ascii=False,indent=2));return code
        if args.output is None:raise ValueError('render/update requires --output version directory')
        if args.output.exists() or args.output.is_symlink():raise ValueError('Output exists; choose a fresh version directory')
        output=args.output.resolve()
        if previous and output.is_relative_to(parent):raise ValueError('New version must be outside previous version directory')
        for item in items:
            if 'artifact' in item:
                item['artifact_href']=quote(os.path.relpath(evidence.source_path(root,item['artifact']),output).replace(os.sep,'/'),safe='/')
        stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
        display=dict(snapshot,checked_at=stamp,input_sha256=sha(data))
        previous_href=quote(os.path.relpath(parent/'index.html',output).replace(os.sep,'/'),safe='/') if previous else None
        document,plain=renderer.render(display,items,previous_href)
        files={'index.html':document.encode('utf-8'),'view.md':plain.encode('utf-8'),'snapshot.json':data}
        generator=[Path(__file__).resolve(),*sorted(p for p in (HERE/'project_view_lib').rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts
                   and (p.suffix in ('.py','.css','.js','.json','.gz') or p.parent.name == 'vendor'))]
        receipt={'schema':1,'project_id':snapshot['project_id'],'generated_at':stamp,'source_root':str(root),
                 'input_sha256':sha(data),'files':{name:sha(value) for name,value in files.items()},
                 'generator':{str(f.relative_to(HERE)):sha(f.read_bytes()) for f in generator},
                 'previous':previous,'reason':args.reason or ('仅重新核对来源；原判断未重评' if previous else '首次生成'),
                 'changes':changes(old,snapshot,items),'items':items,'exit_code':code}
        # Reserve a new directory without replacement; a receipt written last marks a complete version.
        output.mkdir(parents=True,exist_ok=False)
        for name,value in files.items():
            with (output/name).open('xb') as f:f.write(value)
        with (output/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({'output':str(output/'index.html'),'receipt':str(output/'receipt.json'),'sources_current':code==0,'changes':receipt['changes']},ensure_ascii=False,indent=2))
        return code
    except (ValueError,KeyError,TypeError,OSError) as error:
        print(str(error),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
