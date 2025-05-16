"""
Proxy Interface
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from openai import OpenAI, AzureOpenAI
from datetime import datetime as dt
from typing import List, Dict, Tuple
from dotenv import load_dotenv

from .fsm import BaseFsm
from .utils import gen_rand_str, print, defaultdict_to_dict, logger
from .base_proxied_game import (BaseLanguageProcessor, BASE_LANGUAGE_PROCESSOR,
                                BaseGameConfig, BASE_GAME_CONFIG,
                                BaseGameDynamics, BASE_GAME_DYNAMICS)

LLM_LOG_PATH = "./llm_logs/"


class Proxy:
    """
    Proxy. cli interface with most functionality of web UI.
    """

    def __init__(self, addr=None, port=None, **kwargs):
        """
        Parameters
        ----------
        game_config: BaseGameConfig object.
        game_dynamics: BaseGameDynamics object.
        language_processor: BaseLanguageProcessor
        """
        self.state = {}
        self.sio_info = {
            'addr': addr,
            'port': port,
        }
        self.stop_status = False
        self.states = defaultdict(dict)
        self.game_config = kwargs.get("game_config", BASE_GAME_CONFIG)
        self.sio_info = {
            "addr": self.game_config.server_addr,
            "port": self.game_config.server_port
        }
        self.game_dynamics = kwargs.get("game_dynamics", BASE_GAME_DYNAMICS)
        self.language_processor = kwargs.get("language_processor",
                                             BASE_LANGUAGE_PROCESSOR)

        self.log_name = (
            LLM_LOG_PATH +
            f'llm_log_{dt.strftime(dt.now(), "%Y%m%d_%H%M%S")}.txt')
        self.entry_tool = self.game_dynamics.entry_tool

    async def _prelogin(self):
        self.fsm = BaseFsm(self,
                           game_dynamics=self.game_dynamics,
                           game_config=self.game_config)
        await self.fsm._prelogin()
        await self.fsm.pregame()
        # 新添加了username，感觉languageprocessor需要知道username，但是没有接收过
        self.language_processor.user_name = self.fsm.username
        self.language_processor.gamename = self.fsm._base_msg_dict.get(
            "gamename", "")

    async def run(self):
        await self._prelogin()
        print("Apply entry tools...", s=27)
        for entry_tool in self.proxy.game_dynamics.entry_tool:
            print(f"self.proxy.toolize_{entry_tool}", s=1)
            response = await getattr(self, f"toolize_{entry_tool}")({
                "messages": {}
            })
            print(response, s=27)
        return response

    def generate_prompt(self, event: str) -> str:
        """
        Generate Prompt, Call language_processor's generator
        """
        return self.language_processor.generate_prompt(
            event,
            unread_msgs=deepcopy(self.unread_messages),
            read_msgs=deepcopy(self.read_messages))

    def query_with_prompt(self, event: str, prompt: str):
        pass

    def parse_answer(self, answer, event=None):
        return self.language_processor.parse_answer(answer, event)


class ToolProxy(Proxy):

    def __init__(self, addr, port, **kwargs):
        super().__init__(addr, port, **kwargs)
        try:
            self.game_dynamics.eventname_to_toolname
            self.game_dynamics.toolname_to_eventname
        except AttributeError:
            raise AttributeError(
                "`game_dynamics` does not implement name translation.")

    async def _prelogin(self):
        await super()._prelogin()
        for eventname in self.game_dynamics.game_dynamics:
            toolname = self.game_dynamics.eventname_to_toolname(eventname)
            ToolProxy.toolize_general(toolname)
            # print(toolname, eval(f"ToolProxy.toolize_{toolname}"), s=1)

    @classmethod
    def toolize_general(cls, toolname: str):
        """
        Translate waitfor_xxx methods in ToolFsm into translated functions.
        This should be exactly the tool form, however a class method cannot be
        called correctly in `langchain`, so one must wrap it after instantiated
        the ToolProxy, and write proper docstring there (this increases the
        complexity and flexibility at the same time.)
        """

        async def _inner(self, msg: dict | str) -> Tuple[str, bool]:
            """
            """
            msg = self.parse_answer(
                msg, self.game_dynamics.toolname_to_eventname(toolname))
            # print(toolname, msg, s=1)
            ret_msgs, self.stop_status = await getattr(self.fsm, "waitfor_" +
                                                       toolname)(msg)
            self.unread_messages = deepcopy(self.fsm.unread_messages)
            self.read_messages = deepcopy(self.fsm.read_messages)

            # MAYBE we do not need this. Just record all errors.
            if not any(event in ret_msgs
                       for event in self.game_dynamics.error_events):

                self.fsm.read_messages += [self.fsm.unread_messages]
                self.fsm.unread_messages = []
            return self.generate_prompt(list(ret_msgs.keys()))

        setattr(cls, "toolize_" + toolname, _inner)


# class Auto2PlayerFillerProxy(Proxy):
#     """
#     Fills into 2 Player matching games a player
#         when an "available_player" is in that hall.
#     """
#     def __init__(self, addr, port, **kwargs):
#         super().__init__(addr, port, **kwargs)
#         self.proxy_list = []
#         self.proxy_upper_limit = kwargs.get("upper_limit", 5)
#         self.subproxy_unassigned = True

#     async def _prelogin(self):
#         self.fsm = Auto2PlayerFillerFsm(self)
#         await self.fsm._prelogin()
#         await self.add_new_subproxy()

#     def run(self):
#         super().run()

#     async def add_new_subproxy(self):
#         self.proxy_list += [DummyProxy(self.sio_info["addr"],
#                                        self.sio_info["port"],
#                                        username="llm-agent-dummy-tester"+gen_rand_str(10))]
#         await self.proxy_list[-1]._prelogin()
