"""
Generate random strings
"""
import secrets
import json
import hashlib


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
