"""
Generate random strings
"""
import secrets
import json
import hashlib
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def gen_rand_str(n: int = 32):
    """
    Generate random string.

    Default length 32. Only in [A-Za-z0-9].
    """
    return secrets.token_urlsafe(n)


def gen_json_md5_str(item):
    """
    Generate MD5 of JSON style of item.

    item must be jsonify-able.
    """
    return hashlib.md5(json.dumps(item).encode("utf-8")).hexdigest()


def compose_print(l):
    match l:
        case int(a):
            return "".join(f"\033[{x}m" for x in [a])
        case list:
            return "".join(f"\033[{x}m" for x in l)


def add_method(cls):
    """
    Add method to a class
    """

    def decorator(func):
        setattr(cls, func.__name__, func)
        return func

    return decorator


SINGLE_STYLES = ([1, 3, 4, 5, 7, 21, 53] + list(range(30, 37)) + list(range(40, 48)))
COMPOSITE_STYLES = [[1, 3, 4, x] for x in range(40, 47)] + [[1, 4, x] for x in range(40, 47)]

PRINT_STYLES = COMPOSITE_STYLES + SINGLE_STYLES

PRINT_RESUME = compose_print(0)

dummy_print = print


def print(*args, **kwargs):
    style = kwargs.pop("s", None)
    if style is None:
        dummy_print(*args, **kwargs)
    else:
        style %= len(PRINT_STYLES)
        # args[0] = compose_print(PRINT_STYLES[style])+str(args[0])
        dummy_print(compose_print(PRINT_STYLES[style]), *args, PRINT_RESUME, **kwargs)


def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        # 递归转换每个元素
        return {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d
