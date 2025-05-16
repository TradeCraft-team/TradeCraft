"""
APP BASE
"""

import os
import asyncio
import dotenv
from flask import Flask


from .config import LOCAL_PATH

dotenv.load_dotenv()

app_ = Flask(__name__)
app_.config["SECRET_KEY"] = "k33p Ur s3cr3t in CivRealm!"


def path_injection(path):
    """Injection"""
    parts = path.split("://")
    assert len(parts) == 2, f"API BASE `{path}` is not valid!"
    assert parts[0] == "https", "`https` server for api base?"
    assert LOCAL_PATH[-1] != "/"

    # return (f"://{LOCAL_PATH}/").join(parts)
    return f"http://{LOCAL_PATH}/{parts[1]}"


def path_recovery(path):
    """Inverse of path_injection."""
    return f"https://{path}"


def dotenv_path_injection():
    """PATH INJECTION"""
    for key, val in os.environ.items():
        if "ENDPOINT" in key:
            print("LLM-Proxy ENV Injection:\n", f"key = {key},\n", f"val = {val}.")
            os.environ[key] = path_injection(val)


def start_background_loop(loop):
    """Used to create a bg loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()
