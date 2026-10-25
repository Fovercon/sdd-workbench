"""Graph readability regressions, including a five-node DAG with a skip edge."""
import re
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from project_view_lib.layout import graph


def items(names, pairs, groups=None):
    nodes = [
        {'id': name, 'label': name, 'view': 'structure', 'kind': 'code_observation',
         'effective_state': 'SATISFIED', 'group': (groups or {}).get(name, 'Modules')}
        for name in names
    ]
    return nodes + [
        dict(nodes[0], id=f'edge-{i}', **{'from': start, 'to': end})
        for i, (start, end) in enumerate(pairs)
    ]


def path_points(path):
    """Sample the SVG's line/cubic segments independently of layout generation."""
    tokens = iter(re.findall(r'[MLC]|-?\d+(?:\.\d+)?', path))
    point = None
    for command in tokens:
        values = [float(next(tokens)) for _ in range(6 if command == 'C' else 2)]
        if command == 'M':
            point = tuple(values)
            yield point
            continue
        for i in range(1, 101):
            t = i / 100
            if command == 'L':
                yield tuple((1-t)*point[j] + t*values[j] for j in range(2))
            else:
                yield tuple((1-t)**3*point[j] + 3*(1-t)**2*t*values[j]
                            + 3*(1-t)*t*t*values[j+2] + t**3*values[j+4] for j in range(2))
        point = tuple(values[-2:])


class ProjectViewLayoutTests(unittest.TestCase):
    def test_default_graph_keeps_legacy_marker_identity(self):
        svg, _, paths = self.diagram(items('ab', [('a', 'b')]))
        self.assertEqual(svg.find('.//marker').attrib['id'], 'arrow')
        self.assertTrue(all(path.attrib['marker-end'] == 'url(#arrow)' for path in paths))

    def diagram(self, data):
        rendered = graph(data)
        match = re.search(r'<svg\b.*?</svg>', rendered)
        self.assertIsNotNone(match, 'A bounded small DAG must display its relationships')
        svg = ET.fromstring(match.group())
        boxes = {}
        for node in svg.findall('a'):
            rect = node.find('rect')
            boxes[node.attrib['data-node-id']] = tuple(
                float(rect.attrib[key]) for key in ('x', 'y', 'width', 'height'))
        paths = svg.findall("path[@class='edge']")
        edges = [item for item in data if 'from' in item]
        self.assertEqual(set(boxes), {item['id'] for item in data if 'from' not in item})
        self.assertEqual({p.attrib['data-edge-id'] for p in paths}, {e['id'] for e in edges})
        expected_edges = {e['id']: (e['from'], e['to']) for e in edges}
        for path in paths:
            start, end = expected_edges[path.attrib['data-edge-id']]
            self.assertEqual((path.attrib['data-from'], path.attrib['data-to']), (start, end))
            points = list(path_points(path.attrib['d']))
            for point, key in [(points[0], start), (points[-1], end)]:
                x, y, width, height = boxes[key]
                px, py = point
                self.assertTrue(x <= px <= x+width and y <= py <= y+height
                                and (px in (x, x+width) or py in (y, y+height)),
                                f'Edge must meet the boundary of its actual endpoint {key}')
            for px, py in points:
                for key, (x, y, width, height) in boxes.items():
                    self.assertFalse(x+.1 < px < x+width-.1 and y+.1 < py < y+height-.1,
                                     f'{path.attrib["data-edge-id"]} crosses node {key}')
        return svg, boxes, paths

    def test_five_node_deep_dag_keeps_skip_relation_clear_of_intermediate_node(self):
        data = items(['a', 'b', 'e', 'd', 'c'],
                     [('a', 'b'), ('b', 'd'), ('d', 'e'), ('b', 'c'), ('c', 'd')])
        svg, boxes, paths = self.diagram(data)
        self.assertLessEqual(float(svg.attrib['viewBox'].split()[-1]), 760)
        for start, end in [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')]:
            self.assertLess(boxes[start][1] + boxes[start][3], boxes[end][1])

    def test_deep_branch_and_six_level_chain_remain_readable(self):
        for data in [
            items('abcdefg', [('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'e'),
                              ('c', 'e'), ('d', 'e'), ('e', 'f'), ('f', 'g'), ('a', 'e')]),
            items('abcdef', [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e'), ('e', 'f')]),
        ]:
            with self.subTest(nodes=len([i for i in data if 'from' not in i])):
                self.diagram(data)

    def test_shallow_graph_keeps_horizontal_direction(self):
        _, boxes, _ = self.diagram(items('abc', [('a', 'b'), ('b', 'c')]))
        self.assertEqual(boxes['a'][1], boxes['c'][1])
        self.assertLess(boxes['a'][0] + boxes['a'][2], boxes['b'][0])
        self.assertLess(boxes['b'][0] + boxes['b'][2], boxes['c'][0])

    def test_complex_or_oversized_graphs_preserve_grouped_fallback(self):
        scenarios = {
            'cycle': items('ab', [('a', 'b'), ('b', 'a')]),
            'cross-group': items('ab', [('a', 'b')], {'a': 'A', 'b': 'B'}),
            'large': items([f'n{i}' for i in range(13)], []),
            'too-tall': items('abcdefg', list(zip('abcdef', 'bcdefg'))),
            'wide-deep': items('abcdefgh', [('a', 'b'), ('a', 'c'), ('a', 'd'), ('a', 'e'),
                                               ('b', 'f'), ('f', 'g'), ('g', 'h')]),
        }
        for name, data in scenarios.items():
            with self.subTest(name=name):
                rendered = graph(data)
                self.assertNotIn('<svg', rendered)
                self.assertIn('fallback-map', rendered)
                for item in data:
                    if 'from' not in item:
                        self.assertIn(f'data-node-id="{item["id"]}"', rendered)


if __name__ == '__main__':
    unittest.main()
