"""
LLM Request, object for query + forward + event flag
"""

import asyncio
import re
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LLMRequest:
    """
    LLM Request

    Implemented to store query, forward query and receive status.
    """

    def __init__(self, coordinator, **kwargs):
        """Initialize."""
        self.index = kwargs.get("index")
        self.url = kwargs.get("url", "")
        self.msg = kwargs.get("msg", {})
        self.future = kwargs.get("future")
        self.loop = kwargs.get("loop")
        self.coordinator = coordinator
        self.status = 0

    async def forward(self):
        """
        Forward message.

        msg = {"data":data, "params":params-after-`?`}
        """
        thread = asyncio.to_thread(requests.post, self.url, verify=False, **self.msg)
        self.status = 1
        response = await thread
        # response = requests.post(self.url, verify=False, **self.msg)

        self.response_received(response)

    def response_received(self, response: requests.Response):
        """Callback for receiving response."""
        match response.status_code:
            case 200:
                self.status = 0
                self.future.set_result(response)
            case 429:
                rate_err = re.findall(
                    "Please retry after ([0-9]+) seconds.", response.text
                )
                if rate_err == []:
                    print("Response 429 without rate error info.")
                else:
                    print(f"retry after: {rate_err} sec.")
                    tgt_time = time.time() + float(rate_err[0])
                    await_time = tgt_time - self.coordinator.now
                    print(self.coordinator.step_time, await_time, "%%%")
                    self.coordinator.step_time["extra"] = max(
                        self.coordinator.step_time.get(
                            "extra", self.coordinator.step_interval
                        ),
                        await_time,
                    )

                    print(self.coordinator.step_time, await_time, "===")
                    self.status = -1
                    self.coordinator.refresh_cache()

            case _:
                # [HACK] If other errors occur, return them as normal.
                print(
                    "OTHER ERROR:",
                    "\n[Code]:",
                    response.status_code,
                    "\n[Request Index]:",
                    self.index,
                    "\n[Text]",
                    response.text,
                )
                self.status = 0
                self.future.set_result(response)
