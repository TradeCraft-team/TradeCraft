"""
"""

import json
from abc import ABC
from .utils.prompt_loader import PromptHandler
from .sig_config import SIGConfig


class BaseHeadmate(ABC):
    """
    [TODO] Think about how to make itself a tool.
    """

    def __init__(self, haddr, htype, scheduler, debug=False, *args, **kwargs):
        """
        Headmate init
        haddr: str, the unique ID for headmate in the system
        htype: str, the headmate type
        """
        self.haddr = haddr
        self.htype = htype
        self.description = kwargs.get("description", "")
        self.workers = None

        self.scheduler = scheduler
        self.cache = []
        self.time_step = 0

        self.debug = debug

    @property
    def description(self):
        """
        Generate what a headmate is designed for or supposed to do.
        """
        return self._description

    @description.setter
    def description(self, value):
        """
        Setter for the description property.
        Allows setting the description.
        """
        self._description = value

    def active_and_process(self, msg):
        """
        Carry out its specific function.
        """
        response = None
        target = None

        return response, target

    def send_msg(self, msg, targets: list, headmate_list: dict):
        """
        Sending your current message to targets.
        """
        for target in targets:
            request_dic = {
                'source': self.haddr,
                'target': target,
                'msg': msg,
                'time_stamp': self.time_step
            }
            self.scheduler.get_requests(request_dic)

        return

    def step(self, msg):

        return

    def record(self, msg):
        """
        Record the message
        """
        return


class DemoHeadmate(BaseHeadmate):
    """
    """

    def __init__(self,
                 haddr: str,
                 htype: str,
                 scheduler,
                 *args,
                 prompt_handler: PromptHandler | str = "",
                 **kwargs):
        super().__init__(haddr, htype, scheduler)
        pass

    def active_and_process(self, msg, headmate_list: dict):
        response = f"Headmate [{self.haddr}] processed the msg: {msg}.and suppose to send it to someone"
        targets = ['0', '1']
        return response, targets

    def step(self, msg, headmate_list):
        response, targets = self.active_and_process(msg, headmate_list)
        self.send_msg(msg, targets, headmate_list)
        if self.debug:
            print(
                f"This is headmate {self.haddr}, I'm sending a msg to {targets}."
            )

        record_msg = f"Headmate [{self.haddr}] processed the msg: {msg}.and suppose to send it to someone"

        self.record(record_msg)

    def record(self, msg):
        """
        Record the message
        """
        self.cache.append(msg)
        return


class SchedulerHeadmate(BaseHeadmate):
    """
    """

    def __init__(self,
                 haddr: str,
                 *args,
                 prompt_handler: PromptHandler | str = "",
                 **kwargs):
        """
        Base class for schedulers, which should satisfy the following functions:
        (1) Have a request cache
        (2) Have the function to arrange the requests

        """
        super().__init__(
            haddr,
            "scheduler-general",
            *args,
        )

        self.request_list = []
        self.arranged_requests = []
        self.global_time = 0
        self.max_requests = 0

    def get_requests(self, request: dict):
        """
        Recieve the request
        Append it to the request list
        
        """
        self.request_list.append(request)

    def arrange_requests(self):
        """
        Different strategy for request arrangement
        (1) Handle the requests in request list
        (2) Order the requests: in dic[key][value] -> dic[time_step][order]
        (3) After calling, the dic arranged_request will reflect the new orders of requests.
        """

        return

    def step(self):
        # arrange the requests
        self.arrange_requests()

        self.arranged_requests = sorted(self.arranged_requests,
                                        key=lambda x: x['time'])

        self.global_time += 1

        return self.arranged_requests


class ParallelSchedulerHeadmate(SchedulerHeadmate):

    def __init__(self,
                 haddr: str,
                 *args,
                 prompt_handler: PromptHandler | str = "",
                 **kwargs):
        """
        Base class for schedulers, which should satisfy the following functions:
        (1) Have a request cache
        (2) Have the function to arrange the requests

        """
        super().__init__(
            haddr,
            "scheduler-parrall",
            *args,
        )

        pass

    def arrange_requests(self):
        """
        Parallelized Arrange Requests
        """
        time_stamp = self.time_step
        for request in self.request_list:
            self.arranged_requests.append({
                'time': time_stamp,
                'request': request
            })


class LLMHeadmate(BaseHeadmate):
    """
    """

    def __init__(self,
                 haddr: str,
                 *args,
                 prompt_handler: PromptHandler | str = "",
                 **kwargs):
        """
        """
        super().__init__(haddr, "llm-general", *args, prompt_handler)
        match prompt_handler:
            case PromptHandler(phandler):
                self.prompt_handler = phandler

            case str(ptemplate):
                self.prompt_handler = PromptHandler(".", ptemplate, "direct")
