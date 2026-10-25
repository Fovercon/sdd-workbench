"""A file-backed structure view. Only explicit, simple chains become arrow diagrams."""
from collections import defaultdict
import html
import posixpath
from pathlib import PurePosixPath
from urllib.parse import quote
from .evidence import STATES

esc=lambda value:html.escape(str(value),quote=True)


def link(item, body, cls, **attrs):
    attrs={'data-select':item['id'],'data-state':item['effective_state'],**attrs}
    extra=''.join(f' {esc(k)}="{esc(v)}"' for k,v in attrs.items())
    return f'<a class="select {cls}" href="#item-{esc(quote(item["id"],safe=""))}"{extra}>{body}</a>'


def card(item):
    state=item['effective_state']
    badge=f'<small class="file-status">{esc(STATES[state])}</small>' if state!='SATISFIED' else ''
    return link(item,f'<span class="file-name">{esc(PurePosixPath(item["file"]).name)}</span>'
                f'<strong>{esc(item["label"])}</strong><span class="file-purpose">{esc(item.get("note",""))}</span>{badge}',
                'file-card',**{'data-node-id':item['id']})


def chain(nodes, edges):
    """Return a single directed path, or None. Branches/cycles are never flattened."""
    if not edges:
        return None
    incoming=defaultdict(int);outgoing={}
    for edge in edges:
        if edge['from'] in outgoing:
            return None
        outgoing[edge['from']]=edge;incoming[edge['to']]+=1
    if max(incoming.values())>1:
        return None
    connected={e[k] for e in edges for k in ('from','to')}
    starts=connected-incoming.keys()
    if len(starts)!=1 or len(connected)>4:
        return None
    ordered=[];seen=set();key=next(iter(starts))
    while key not in seen:
        seen.add(key);ordered.append(nodes[key])
        if key not in outgoing:break
        ordered.append(outgoing[key]);key=outgoing[key]['to']
    return ordered if seen==connected and len(ordered)==len(connected)+len(edges) else None


def render(items):
    files=[i for i in items if i['view']=='structure' and 'from' not in i]
    # Legacy conceptual maps keep their explicit old layout; do not guess file ownership.
    if not files or any('file' not in item for item in files):
        return None
    by_id={i['id']:i for i in files};edges=[i for i in items if 'from' in i]
    ordered=chain(by_id,edges)
    if ordered:
        parts=[]
        for item in ordered:
            if 'from' not in item:parts.append(card(item));continue
            parts.append(link(item,f'<span>{esc(item["label"])}</span><b aria-hidden="true">→</b>',
                'file-edge',**{'data-edge-id':item['id'],'data-from':item['from'],'data-to':item['to']}))
        flow='<div class="file-flow">'+''.join(parts)+'</div>'
    else:
        # A relationship index preserves all branch/cycle semantics without crossing wires.
        flow='<div class="file-cards">'+''.join(card(i) for i in files if any(i['id'] in (e['from'],e['to']) for e in edges))+'</div>'
        flow+='<div class="file-connections">'+''.join(link(e,
            f'<code>{esc(PurePosixPath(by_id[e["from"]]["file"]).name)}</code><span>{esc(e["label"])} →</span>'
            f'<code>{esc(PurePosixPath(by_id[e["to"]]["file"]).name)}</code>','file-connection',
            **{'data-edge-id':e['id'],'data-from':e['from'],'data-to':e['to']}) for e in edges)+'</div>'
    root=posixpath.commonpath([str(PurePosixPath(i['file']).parent) for i in files])
    connected={e[k] for e in edges for k in ('from','to')}
    tree={}
    for item in files:
        parts=PurePosixPath(posixpath.relpath(item['file'],root or '.')).parts
        node=tree
        for part in parts[:-1]:node=node.setdefault(part,{})
        node[parts[-1]]=item
    def is_file(node):
        return isinstance(node.get('file'),str)
    def leaf(name,value):
        attrs={'data-node-id':value['id']} if value['id'] not in connected else {}
        state=value['effective_state']
        warning=f'<small class="file-status">{esc(STATES[state])}</small>' if state!='SATISFIED' else ''
        return link(value,f'<span class="tree-file">{esc(name)}</span><span class="tree-role">{esc(value["label"])}</span>'+warning,'tree-link',**attrs)
    def branches(node):
        parts=[]
        for name,value in sorted(node.items()):
            if is_file(value):parts.append('<li>'+leaf(name,value)+'</li>')
            else:parts.append(f'<li><details open><summary>{esc(name)}/</summary>{branches(value)}</details></li>')
        return '<ul>'+''.join(parts)+'</ul>'
    root_files=''.join(leaf(name,value) for name,value in sorted(tree.items()) if is_file(value))
    folders=([f'<section class="repo-folder repo-root"><h4>项目根目录</h4>{root_files}</section>'] if root_files else [])
    for name,value in sorted(tree.items()):
        if is_file(value):continue
        labels=list(dict.fromkeys(i.get('group','') for i in files if PurePosixPath(posixpath.relpath(i['file'],root or '.')).parts[0]==name))
        purpose=' / '.join(label for label in labels if label)
        folders.append(f'<details class="repo-folder" open><summary><code>{esc(name)}/</code><span>{esc(purpose)}</span></summary>{branches(value)}</details>')
    return ('<div class="repository-map"><div class="repository-heading"><span>当前仓库</span>'
        f'<code>{esc(root or ".")}/</code></div>'
        +('<div class="repo-call-heading"><h3>主要文件怎样协作</h3><p>点文件了解职责，点箭头查看这条联系的依据。</p></div>'+flow if edges else '')
        +'<section class="repo-tree"><h3>这些文件在什么位置</h3><p>按实际目录整理；这里只列本次涉及的文件。</p>'
        +'<div class="repo-folders">'+''.join(folders)+'</div></section></div>')
