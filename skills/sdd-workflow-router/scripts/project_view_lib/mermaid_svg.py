"""Render a Mermaid flowchart subset as native SVG inside the CSP-locked board.

Only `flowchart TD|TB|LR` (alias `graph`) with node shapes, labeled arrows and
subgraphs is parsed, so design views stay offline and dependency-free. Anything
else — sequence, state, ER or class diagrams, long-form edge labels, chained `&`
forks, cyclic or oversized graphs, or syntax this parser does not understand —
returns None, and the caller displays the cited source verbatim. A picture the
parser cannot build honestly is never invented.
"""
from collections import defaultdict, deque
import hashlib
import html
import re
import unicodedata

esc = lambda v: html.escape(str(v), quote=True)

ARROW = re.compile(r'-{2,}>|-\.-+>|={2,}>|-{2,}(?!>)')
EDGE_LABEL = re.compile(r'\s*\|([^|]*)\|')
SUBGRAPH = re.compile(r'subgraph\s+(.+)')
HEADER = re.compile(r'(?:flowchart|graph)\s+(TD|TB|LR|RL)', re.I)
SHAPES = (('cyl', '[(', ')]'), ('sub', '[[', ']]'), ('rect', '[', ']'),
          ('circle', '((', '))'), ('round', '(', ')'), ('diamond', '{', '}'))
LIMIT_NODES, LIMIT_EDGES = 18, 24
MAX_ASPECT = 4.5  # wider than this reads as an unreadable strip; rebalance


def _units(text):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)


def _short(text, limit):
    if _units(text) <= limit:
        return text
    out, width = '', 0
    for c in text:
        width += 2 if unicodedata.east_asian_width(c) in 'WF' else 1
        if width > limit - 1:
            return out + '…'
        out += c
    return out


def _node(token):
    token = token.strip()
    if not token:
        return None
    head = re.match(r'[A-Za-z0-9_.\-]*', token)
    nid, rest = head.group(0), token[head.end():].strip()
    label, shape = nid, 'rect'
    if rest:
        for name, open_, close in SHAPES:
            if rest.startswith(open_) and rest.endswith(close) and len(rest) >= len(open_) + len(close) + 1:
                label = rest[len(open_):-len(close)].strip().strip('"')
                shape = name
                break
        else:
            return None
    if not nid:
        if not label:
            return None
        nid = 'n' + hashlib.sha1(label.encode()).hexdigest()[:8]
    return nid, label, shape


def parse(text):
    """Return (nodes, order, edges, horizontal) or None when unsupported."""
    horizontal, stack, nodes, order, edges, seen = None, [], {}, [], [], set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%'):
            continue
        if horizontal is None:
            header = HEADER.fullmatch(line)
            if not header:
                return None
            direction = header.group(1).upper()
            if direction == 'RL':
                return None  # reversed layout is not rendered; show the source
            horizontal = direction == 'LR'
            continue
        if line == 'end':
            if not stack:
                return None
            stack.pop()
            continue
        sub = SUBGRAPH.fullmatch(line)
        if sub:
            title = sub.group(1).strip()
            named = re.fullmatch(r'([A-Za-z0-9_.\-]+)\s*(?:\[(.+)\])?', title)
            label = (named.group(2) or named.group(1) or '分组').strip('"') if named else title
            stack.append(label)
            continue
        # Long-form labeled edges and & forks are common but ambiguous to this
        # parser; refuse them instead of guessing a different graph.
        if '&' in line or re.search(r'\s--\s+\S', line) or re.search(r'\s-\.\s+\S', line):
            return None
        parts, pos = [], 0
        for arrow in ARROW.finditer(line):
            parts.append(line[pos:arrow.start()])
            label = ''
            tagged = EDGE_LABEL.match(line, arrow.end())
            if tagged:
                label = tagged.group(1).strip()
                pos = tagged.end()  # match spans are absolute within the line
            else:
                pos = arrow.end()
            parts.append(('edge', arrow.group(0), label))
        parts.append(line[pos:])
        tokens = []
        for part in parts:
            if isinstance(part, tuple):
                tokens.append(part)
                continue
            node = _node(part)
            if node is None:
                return None
            tokens.append(('node',) + node)
        group = stack[-1] if stack else None
        pending_edge, last_nid = None, None
        for token in tokens:
            if token[0] == 'edge':
                pending_edge = token
                continue
            _, nid, label, shape = token
            if nid not in nodes:
                nodes[nid] = {'label': label, 'shape': shape, 'group': group}
                order.append(nid)
            elif group is not None and not nodes[nid]['group']:
                nodes[nid]['group'] = group
            if pending_edge is not None:
                if last_nid == nid:
                    return None  # a self-loop cannot be laid out honestly here
                if (last_nid, nid) not in seen:
                    seen.add((last_nid, nid))
                    edges.append({'from': last_nid, 'to': nid, 'label': pending_edge[2]})
                pending_edge = None
            last_nid = nid
    if horizontal is None or not nodes or not edges:
        return None
    if len(nodes) > LIMIT_NODES or len(edges) > LIMIT_EDGES:
        return None
    return nodes, order, edges, horizontal


def _levels(order, edges):
    indeg = {nid: 0 for nid in order}
    adj = defaultdict(list)
    for edge in edges:
        adj[edge['from']].append(edge['to'])
        indeg[edge['to']] += 1
    level = {nid: 0 for nid in order}
    queue = deque(nid for nid in order if indeg[nid] == 0)
    visited = 0
    while queue:
        nid = queue.popleft()
        visited += 1
        for target in adj[nid]:
            level[target] = max(level[target], level[nid] + 1)
            indeg[target] -= 1
            if indeg[target] == 0:
                queue.append(target)
    if visited != len(order):
        return None  # cycles stay unverifiable in this layout; show the source
    return level


def _layout(nodes, order, edges, horizontal):
    """Place each level along the main axis, members centered on the cross axis.

    Node boxes keep their natural measured size; edges anchor on real box
    borders, so the picture never depends on hardcoded geometry.
    """
    level = _levels(order, edges)
    if level is None:
        return None
    bands = defaultdict(list)
    for nid in order:
        bands[level[nid]].append(nid)
    for nid in order:
        nodes[nid]['w'] = min(300, max(116, _units(_short(nodes[nid]['label'], 26)) * 10 + 36))
        nodes[nid]['h'] = 54
    main_gap, cross_gap, pad = 62, 16, 22
    for nid in order:
        nodes[nid].pop('pos', None)
    band_geometry, total_main = {}, pad
    for depth in sorted(bands):
        band = bands[depth]
        band_main = max(nodes[nid]['w'] if horizontal else nodes[nid]['h'] for nid in band)
        band_cross = sum(nodes[nid]['h'] if horizontal else nodes[nid]['w'] for nid in band) + cross_gap * (len(band) - 1)
        band_geometry[depth] = (total_main, band_main, band_cross)
        total_main += band_main + main_gap
    total_main += pad - main_gap
    max_cross = max(geometry[2] for geometry in band_geometry.values()) + pad * 2
    for depth, (main0, band_main, _band_cross) in band_geometry.items():
        cross = pad
        for nid in bands[depth]:
            if horizontal:
                nodes[nid]['pos'] = (main0 + (band_main - nodes[nid]['w']) // 2, cross)
                cross += nodes[nid]['h'] + cross_gap
            else:
                nodes[nid]['pos'] = (cross, main0 + (band_main - nodes[nid]['h']) // 2)
                cross += nodes[nid]['w'] + cross_gap
    return (total_main, max_cross) if horizontal else (max_cross, total_main)


def _anchors(node, horizontal):
    x, y = node['pos']
    w, h = node['w'], node['h']
    if horizontal:
        return (x + w, y + h / 2), (x, y + h / 2)
    return (x + w / 2, y + h), (x + w / 2, y)


def _shape_svg(nid, node):
    x, y = node['pos']
    w, h = node['w'], node['h']
    cx, cy = x + w / 2, y + h / 2
    kind = node['shape']
    if kind == 'diamond':
        body = f'<polygon class="node-face" points="{cx},{y + 3} {x + w - 6},{cy} {cx},{y + h - 3} {x + 6},{cy}"/>'
        limit = 8
    else:
        radius = {'rect': 10, 'round': 22, 'circle': 24, 'sub': 4, 'cyl': 8}[kind]
        body = f'<rect class="node-face" x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}"/>'
        if kind == 'cyl':
            body += (f'<line x1="{x + 7}" y1="{y + 12}" x2="{x + w - 7}" y2="{y + 12}" class="cyl-line"/>'
                     f'<line x1="{x + 7}" y1="{y + h - 12}" x2="{x + w - 7}" y2="{y + h - 12}" class="cyl-line"/>')
        if kind == 'sub':
            body += f'<rect class="node-face sub-inner" x="{x + 4}" y="{y + 4}" width="{w - 8}" height="{h - 8}" rx="3"/>'
        limit = 18 if kind != 'circle' else 12
    label = _short(node['label'], limit)
    return (f'<g class="graph-node" data-kind="design"><title>{esc(node["label"])}</title>{body}'
            f'<text class="node-label" x="{cx}" y="{cy + 6}" text-anchor="middle">{esc(label)}</text></g>')


def _edge_svg(edge, nodes, horizontal, marker):
    (sx, sy), (ex, ey) = (_anchors(nodes[edge['from']], horizontal)[0],
                          _anchors(nodes[edge['to']], horizontal)[1])
    if horizontal:
        mid_x = (sx + ex) / 2
        path = f'M{sx} {sy} C{mid_x} {sy} {mid_x} {ey} {ex} {ey}'
        lx, ly = mid_x, (sy + ey) / 2 - 8
    else:
        mid_y = (sy + ey) / 2
        path = f'M{sx} {sy} C{sx} {mid_y} {ex} {mid_y} {ex} {ey}'
        lx, ly = (sx + ex) / 2, mid_y - 8
    label = ''
    if edge['label']:
        label = (f'<text class="edge-label" x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle"'
                 ' style="paint-order:stroke;stroke:#fff;stroke-width:4px">' + esc(_short(edge['label'], 20)) + '</text>')
    return f'<path class="edge" d="{path}" marker-end="url(#{esc(marker)})">{label}</path>'


def render(mermaid, unique=''):
    """Return an SVG string, or None when the source must be shown verbatim."""
    parsed = parse(mermaid)
    if parsed is None:
        return None
    nodes, order, edges, horizontal = parsed
    size = _layout(nodes, order, edges, horizontal)
    if size is None:
        return None
    width, height = size
    if horizontal and width > MAX_ASPECT * max(height, 1):
        # A near-linear left-to-right chain squeezes into an unreadable strip;
        # rebalance top-down. Topology, labels and arrows stay identical.
        size = _layout(nodes, order, edges, False)
        if size is not None:
            width, height = size
            horizontal = False
    groups = defaultdict(list)
    for nid in order:
        if nodes[nid]['group']:
            groups[nodes[nid]['group']].append(nid)
    frames = []
    for title, members in groups.items():
        left = min(nodes[nid]['pos'][0] for nid in members) - 14
        top = min(nodes[nid]['pos'][1] for nid in members) - 14
        right = max(nodes[nid]['pos'][0] + nodes[nid]['w'] for nid in members) + 14
        bottom = max(nodes[nid]['pos'][1] + nodes[nid]['h'] for nid in members) + 14
        frames.append(f'<rect class="group-frame" x="{left}" y="{top}" width="{right - left}"'
                      f' height="{bottom - top}" rx="14"/><text class="group-label" x="{left + 14}"'
                      f' y="{top + 22}">{esc(_short(title, 24))}</text>')
    width, height = max(width, 200), max(height, 120)
    marker = 'design-arrow-' + re.sub(r'[^A-Za-z0-9]', '-', unique or 'view')
    body = ''.join(_edge_svg(e, nodes, horizontal, marker) for e in edges)
    body += ''.join(_shape_svg(nid, nodes[nid]) for nid in order)
    return (f'<svg class="overview-graph" viewBox="0 0 {width:.0f} {height:.0f}" role="img"'
            f' aria-label="设计视图结构图"><defs><marker id="{esc(marker)}" markerWidth="8" markerHeight="8"'
            ' refX="7" refY="4" orient="auto"><path d="M0 1 L7 4 L0 7" fill="none"'
            ' stroke="context-stroke" stroke-width="1.5"/></marker></defs>'
            + ''.join(frames) + body + '</svg>')
