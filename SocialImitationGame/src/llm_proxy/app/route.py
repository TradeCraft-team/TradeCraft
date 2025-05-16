"""
Routing rules of proxy.
"""

import asyncio
from flask import request, Flask
from threading import Thread

from .app import path_recovery, start_background_loop


from ..limiter import DequeModel


def proxy_run(
    host="127.0.0.1",
    port=8191,
    debug=False,
    quiet=True,
):
    side_loop = asyncio.new_event_loop()

    deque_model = DequeModel(event_loop=side_loop, quiet=quiet)
    deque_model.set_loop(side_loop)

    t = Thread(target=start_background_loop, args=(side_loop,))
    t.start()

    global app_

    app_ = Flask(__name__)
    app_.config["SECRET_KEY"] = "k33p Ur s3cr3t in CivRealm!"

    @app_.route("/<path:path>", methods=["GET", "POST"])
    @app_.route("/", defaults={"path": ""}, methods=["GET", "POST"])
    async def proxy(path):
        """
        Answer to all urls.
        """

        url = path_recovery(path)
        data = request.get_json()
        headers = dict(request.headers)
        headers["Host"] = path.split("/")[0]
        msg = {"params": request.args, "headers": headers, "json": data}

        c_fut = asyncio.run_coroutine_threadsafe(
            deque_model.process(url, msg), side_loop
        )

        response_json = c_fut.result()

        return response_json

    app_.run(
        host=host,
        debug=debug,
        port=port,
    )
