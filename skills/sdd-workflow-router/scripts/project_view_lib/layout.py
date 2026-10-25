"""Small DAG diagrams with complete, readable list fallback for complex topology."""
from collections import defaultdict, deque
from .evidence import STATES
import html
from pathlib import Path
from urllib.parse import quote
import unicodedata

esc = lambda v: html.escape(str(v), quote=True)
anchor = lambda v: 'item-' + quote(v, safe='')


def short(value, units):
    result='';width=0
    for c in value:
        width += 2 if unicodedata.east_asian_width(c) in 'WF' else 1
        if width>units:return result+'…'
        result+=c
    return result


def grouped_links(groups, fallback=False):
    parts=['<div class="fallback-map">' if fallback else '<div class="mobile-map">']
    for group,nodes in groups.items():
        parts.append(f'<section class="mobile-group"><h3>{esc(group)}</h3>')
        for n in nodes:
            sub=n.get('sublabel') or (Path(n['sources'][0]['path']).name if n.get('sources') else '')
            if n['kind']=='design':sub='设计 · '+STATES[n['effective_state']]
            node_attr=f' data-node-id="{esc(n["id"])}"' if fallback else ''
            parts.append(f'<a class="select mobile-node"{node_attr} data-select="{esc(n["id"])}" data-kind="{esc(n["kind"])}" data-state="{esc(n["effective_state"])}" href="#{esc(anchor(n["id"]))}"><strong class="module-title">{esc(n["label"])}</strong><small>{esc(sub)}</small><span aria-hidden="true">↗</span></a>')
        parts.append('</section>')
    return ''.join(parts)+'</div>'


def graph(items, namespace=None):
    # Inline SVG IDs share the document namespace, including hidden stage panels.
    # Keep the single-graph legacy ID unless the caller supplies a scoped name.
    marker_id = f'{namespace}-arrow' if namespace else 'arrow'
    nodes=[i for i in items if i['view']=='structure' and 'from' not in i]
    edges=[i for i in items if 'from' in i]
    if not nodes:return '<p class="layout-note">当前没有已记录的模块；请先核对本次观察范围。</p>'
    groups=defaultdict(list)
    for n in nodes:groups[n.get('group') or '项目模块'].append(n)
    group_of={n['id']:g for g,ns in groups.items() for n in ns}
    # Dense/cyclic/cross-group graphs stay explicit without inventing a layout or hiding records.
    fallback=len(nodes)>12 or len(edges)>16 or any(group_of[e['from']]!=group_of[e['to']] for e in edges)
    positions={};frames=[];vertical=set();top=16
    for group,ns in groups.items():
        ids={n['id'] for n in ns};adj=defaultdict(list);degree={i:0 for i in ids};level={i:0 for i in ids}
        for e in edges:
            if e['from'] in ids and e['to'] in ids:adj[e['from']].append(e['to']);degree[e['to']]+=1
        queue=deque(n['id'] for n in ns if degree[n['id']]==0);visited=[]
        while queue:
            node=queue.popleft();visited.append(node)
            for target in adj[node]:
                level[target]=max(level[target],level[node]+1);degree[target]-=1
                if degree[target]==0:queue.append(target)
        if len(visited)!=len(ns):fallback=True
        columns=defaultdict(list)
        for n in ns:columns[level[n['id']]].append(n)
        rows=max(len(col) for col in columns.values());count=max(level.values())+1
        deep=count>3
        if deep and rows>3:fallback=True
        height=54+(count if deep else rows)*108
        frames.append((group,top,height))
        for col,group_nodes in columns.items():
            if deep:
                for j,n in enumerate(group_nodes):
                    positions[n['id']]=(60+(3-len(group_nodes))*135+j*270,top+44+col*108)
                    vertical.add(n['id'])
            else:
                x=60 if count==1 else 60+col*(540/(count-1))
                for j,n in enumerate(group_nodes):
                    positions[n['id']]=(x,top+44+(rows-len(group_nodes))*54+j*108)
        top+=height+16
    if top>760:fallback=True
    if fallback:
        return '<p class="layout-note">关系较多或含跨组/循环连接，按模块分组展示；下方逐条列出关系起点与终点，点击可查看依据。</p>'+grouped_links(groups,True)
    parts=[f'<svg class="overview-graph" viewBox="0 0 900 {top}" role="group" aria-label="当前范围的模块关系">',
           f'<defs><marker id="{esc(marker_id)}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 1 L7 4 L0 7" fill="none" stroke="context-stroke" stroke-width="1.5"/></marker></defs>']
    for group,y,h in frames:
        parts.append(f'<rect class="group-frame" x="22" y="{y}" width="856" height="{h}" rx="14"/><text class="group-label" x="38" y="{y+25}"><title>{esc(group)}</title>{esc(short(group,100))}</text>')
    skip_lanes=defaultdict(int)
    for e in edges:
        x1,y1=positions[e['from']];x2,y2=positions[e['to']]
        if e['from'] in vertical:
            skipped=y2-y1>108
            x1+=120;x2+=120;y1+=82;middle=(y1+y2)/2
            if skipped:
                # Skip edges use separate outer lanes, never a path through intermediate nodes.
                lane=skip_lanes[group_of[e['from']]];skip_lanes[group_of[e['from']]]+=1
                outside=30+4*(lane//2) if lane%2==0 else 870-4*(lane//2)
                d=f'M{x1} {y1} L{x1} {y1+10} L{outside} {y1+10} L{outside} {y2-10} L{x2} {y2-10} L{x2} {y2}'
            else:
                d=f'M{x1} {y1} C{x1} {middle} {x2} {middle} {x2} {y2}'
        else:
            x1+=240;y1+=41;y2+=41;middle=(x1+x2)/2
            d=f'M{x1} {y1} C{middle} {y1} {middle} {y2} {x2} {y2}'
        parts.append(f'<path class="edge" data-edge-id="{esc(e["id"])}" data-from="{esc(e["from"])}" data-to="{esc(e["to"])}" data-state="{esc(e["effective_state"])}" d="{d}" marker-end="url(#{esc(marker_id)})"><title>{esc(e["label"])}</title></path>')
    for n in nodes:
        x,y=positions[n['id']];sub=n.get('sublabel') or (Path(n['sources'][0]['path']).name if n.get('sources') else '')
        if n['kind']=='design':sub='设计 · '+STATES[n['effective_state']]
        parts.append(f'<a class="graph-node select" data-node-id="{esc(n["id"])}" data-select="{esc(n["id"])}" data-kind="{esc(n["kind"])}" data-state="{esc(n["effective_state"])}" href="#{esc(anchor(n["id"]))}" aria-label="查看{esc(n["label"])}的详情与证据"><title>{esc(n["label"])}</title><rect class="node-face" x="{x}" y="{y}" width="240" height="82" rx="10"/><circle class="node-dot" cx="{x+224}" cy="{y+15}" r="3"/><text class="node-label" x="{x+16}" y="{y+34}">{esc(short(n["label"],22))}</text><text class="node-file" x="{x+16}" y="{y+59}">{esc(short(sub,31))}</text></a>')
    return ''.join(parts)+'</svg>'+grouped_links(groups)
