"""Oracle solution for config-precedence (evaluator-owned)."""
import copy
import json
import os
import re as _re

_INT_RE = _re.compile(r'^[+-]?\d+$')
_FLOAT_RE = _re.compile(r'^[+-]?\d+\.\d+$')


class ConfigError(Exception):
    pass


def coerce(value):
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if _INT_RE.match(value):
        return int(value)
    if _FLOAT_RE.match(value):
        return float(value)
    return value


def _deep_merge(base, overlay):
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _env_overlay(defaults, env):
    overlay = {}

    def dig(node, path):
        if not isinstance(node, dict):
            return False
        for part in path[:-1]:
            if part not in node or not isinstance(node[part], dict):
                return False
            node = node[part]
        return path[-1] in node

    def plant(node, path, value):
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = value

    for key, value in env.items():
        if not key.startswith('APP_'):
            continue
        path = [part.lower() for part in key[len('APP_'):].split('__')]
        if not dig(defaults, path):
            continue
        plant(overlay, path, coerce(value))
    return overlay


def merge(defaults, file_path=None, env=None):
    result = copy.deepcopy(defaults)
    if file_path is not None:
        try:
            with open(file_path, encoding='utf-8') as fh:
                loaded = json.load(fh)
        except FileNotFoundError:
            loaded = None
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(str(exc)) from exc
        if loaded is not None:
            if not isinstance(loaded, dict):
                raise ConfigError('config file must contain a JSON object')
            _deep_merge(result, copy.deepcopy(loaded))
    if env is None:
        env = os.environ
    overlay = _env_overlay(result, dict(env))
    _deep_merge(result, overlay)
    return result
