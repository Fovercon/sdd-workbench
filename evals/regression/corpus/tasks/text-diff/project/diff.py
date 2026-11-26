"""词级文本比较工具(待实现,见 docs/PRD.md)。"""


def tokenize(text):
    raise NotImplementedError


def word_diff(old, new, ignore_case=False):
    raise NotImplementedError


def render(ops):
    raise NotImplementedError
