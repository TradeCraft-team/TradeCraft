from .app import dotenv_path_injection
from .route import proxy_run

from multiprocessing import Process


def run_llm_proxy(host="127.0.0.1", port=8191, quiet=True, debug=False):
    """Run APP"""
    print("RUNNING LLM PROXY\n")
    dotenv_path_injection()
    try:
        server_process = Process(
            target=lambda kwargs: proxy_run(**kwargs),
            args=(
                dict(
                    host=host,
                    port=port,
                    debug=debug,
                    quiet=quiet,
                ),
            ),
        )
        server_process.start()
    except FileNotFoundError as e:
        print("For an HTTPS proxy server, SSL certificates are required.")
        print("You may run:")
        print(
            "`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`"
        )
        print("to generate necessary SSL certificates.")

        print("Original Error Message", e)
