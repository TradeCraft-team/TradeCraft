"""
Main model
"""

import asyncio
import time
from collections import deque, OrderedDict

from .llm_request import LLMRequest
from ..app.config import TOKEN_LIMIT, REQUEST_LIMIT, MINUTE, STEP_INTERVAL


class DequeModel:
    """
    Use double Deque to maintain message requests

    Use ordered dict?
    """

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__()

        self._reqeust_limit = kwargs.get("request_limit", REQUEST_LIMIT)
        self._token_limit = kwargs.get("token_limit", TOKEN_LIMIT)
        self._pending_requests = deque([])
        self._forwarded_requests = OrderedDict([])
        self.refresh_lock = False

        self.step_interval = kwargs.get("step_interval", STEP_INTERVAL)
        self.step_time = {}
        self.now = time.time()
        self.next_stamp = 0

        self.futures = {}
        self.forward_operation_lock = False
        self.loop = kwargs.get("event_loop", None)
        self.loop_flag = False
        # format ()
        self.incoming_stamp = []
        self.incoming_token = []
        # self.outgoing_stamp = []
        # self.outgoing_token = []
        #
        self.quiet = kwargs.get("quiet", False)

    @staticmethod
    def index_gen():
        """Generate id."""
        cnt = 0
        while True:
            yield cnt
            cnt += 1

    def set_loop(self, loop=None):
        """Get running loop"""
        if not self.loop_flag:
            self.loop = loop or asyncio.get_running_loop()
            self.loop.create_task(self.simple_event_loop())
            self.loop_flag = True

    def new_client_request(self, url, msg):
        """
        Activity with new request from client

        [TODO] here suppose requests are added one by one.
        """
        llm_request = LLMRequest(
            self,
            loop=self.loop,
            index=self.index_gen(),
            url=url,
            msg=msg,
            future=self.loop.create_future(),
        )
        self._pending_requests.append(llm_request)
        return llm_request

    def next_request(self):
        """
        Get next instack request
        """
        try:
            while (req := self._pending_requests.popleft()).future.done():
                pass
            if not self.quiet:
                print(req.index, "is pop out.--------")
            self._forwarded_requests[req.index] = req
            if not self.quiet:
                print(len(self._forwarded_requests), len(self._pending_requests))
            return req
        except IndexError as e:
            raise e

    def refresh_cache(self):
        """
        As rate exceeding API limit (not limit here), the requests to llm
        have to be reasked.
        """
        if self.refresh_lock:
            return
        self.refresh_lock = True
        for _, v in self._forwarded_requests.items():
            self._pending_requests.appendleft(v)

        self._forwarded_requests = OrderedDict([])
        self.refresh_lock = False

    def check_rates(self):
        """
        True for rate under limit, False for above.
        Time interval for calculation is the recent minute.
        """
        return self.check_request_rates() and self.check_token_rates()

    def check_token_rates(self):
        """
        [HACK] Supposed to be called after check_request_rates.
        So the statistics has already been updated!
        """
        return (
            sum(self.incoming_token)  # + sum(self.outgoing_token)
            < self._token_limit
        )

    def check_request_rates(self):
        """Check request amount in last minute."""
        # It is tested that for single-sided queue, list > deque
        while True:
            if not self.incoming_stamp:
                break
            if (self.now - self.incoming_stamp[0]) < MINUTE:
                break
            self.incoming_stamp.pop()
            self.incoming_token.pop()
        # while (now - self.outgoing_stamp[0]) > MINUTE:
        #     self.outgoing_stamp.pop()
        #     self.outgoing_stamp.pop()
        return (
            len(self.incoming_token)  # + len(self.outgoing_token)
            < self._reqeust_limit
        )

    async def process(self, url, msg) -> str:
        """
        Main entry for applications

        This function is NOT running in the event loop
        created by Flask view function. So it must be called
        using asyncio.run_coroutine_threadsafe.
        """
        llm_request = self.new_client_request(url, msg)

        # with ThreadPoolExecutor() as pool:
        #     response = await self.loop.run_in_executor(pool,
        #                                                llm_request.future)

        response = await llm_request.future

        res_json = response.json()
        print("lllllllllllllllllllllllll",res_json)
        self.incoming_stamp.append(time.time())
        self.incoming_token.append(res_json["usage"]["total_tokens"])
        self._forwarded_requests.pop(llm_request.index, None)

        return response.text

    # ASYNC methods
    async def simple_event_loop(self):
        """Ever running method maintaining the requests struture."""
        tasks = {}
        while True:
            if not self.quiet:
                print("===============", self.now, self.step_time)
            await asyncio.sleep(self.step_time.pop("extra", self.step_interval))
            self.now = time.time()

            if not self.quiet:
                print(
                    "Forward",
                    len(self._forwarded_requests),
                    "Pending",
                    len(self._pending_requests),
                    sum(self.incoming_token),
                    len(self.incoming_stamp),
                )
            if len(self._pending_requests) == 0:
                continue
            if self.check_rates():
                try:
                    # filtered the status before returning to req.
                    req = self.next_request()
                except IndexError:
                    continue

                # moved by refresh but not failed, can use old task.
                if req.status <= 0:
                    tasks[req.index] = self.loop.create_task(req.forward())
                # self.outgoing_stamp.append(time.time())
                # self.outgoing_token.append(0)
