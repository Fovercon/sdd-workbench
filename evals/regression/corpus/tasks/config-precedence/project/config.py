"""配置优先级合并(待实现,见 docs/PRD.md)。"""


class ConfigError(Exception):
    pass


def coerce(value):
    raise NotImplementedError


def merge(defaults, file_path=None, env=None):
    raise NotImplementedError
