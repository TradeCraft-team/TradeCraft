"""
Base
"""
import asyncio
import json
from abc import ABC
from gymnasium import Env, Wrapper
from .headmate import BaseHeadmate
from .sig_config import SIGConfig
from .sig_model import DemoSIGModel as SIGModel
from ..utils import print
from ..agent_proxy.proxy import Proxy
from ..agent_proxy import *


class BaseSIGAgent(ABC):
    """
    Agentify the SIG system.
    """

    def __init__(self,
                 proxy: Proxy,
                 *args,
                 sig_model: SIGModel = None,
                 **kwargs):
        """
        Initialize.
        """
        self.proxy = proxy
        self.llm = kwargs.get("llm")

        self.sig_model = sig_model

    async def run(self, *args, **kwargs):
        # while self.proxy.fsm.state not in proxy.start_states:
        #     await asyncio.sleep(0.2)
        await self.start_sig(*args, **kwargs)
        while self.proxy.fsm.state not in self.proxy.fsm.stop_states:
            await asyncio.sleep(5)

    async def start_sig(self, *args, **kwargs):
        pass


class GymSIGAgent(BaseSIGAgent):
    """
    The SIG Agent with Tools class with Gym.

    [TODO] This is the Async Version.
    """

    # @override ?
    def __init__(self,
                 env: Proxy | Wrapper,
                 *args,
                 sig_model: SIGModel = None,
                 **kwargs):
        """
        env is required.
        """

        match env:
            case Proxy() as proxy:
                self.driver = "proxy"
                super().__init__(proxy, *args, sig_model, **kwargs)

            case Wrapper():
                self.driver = "gymnasium"
                super().__init__(env.unwrapped.proxy, *args, sig_model,
                                 **kwargs)
                self.env = env
                self.is_async = self.env.metadata["async"]

            case _:
                raise Exception("Please provide an env or a proxy.")

    async def main_loop(self, msg, *args, **kwargs):
        """
        """
        pass

    async def start_sig(self, msg, *args, **kwargs):
        """
        Start SIG with Proxy
        """
        raw = msg.get("input", "NO Initial INPUT!")
        print("==== START ====\n", raw)

        # entry_tool: ready_to_start
        if (entry_tool := self.proxy.game_dynamics.entry_tool):
            # print(f"self.proxy.toolize_{entry_tool[0]}", s=1)
            response = await eval(f"self.proxy.toolize_{entry_tool[0]}")({
                "messages": {}
            })
            print(response, s=25)
        return await self.main_loop({"input": raw + response}, *args, **kwargs)

    async def start_sig_env(self, *args, **kwargs):
        """
        Start SIG with Gym Environment
        """
        if self.is_async:
            obs, info = await self.env.reset()
        else:
            reset_coro = asyncio.to_thread(self.env.reset())
            obs, info = await reset_coro

        return await self.main_loop({"input": info}, *args, **kwargs)

    async def run(self, *args, **kwargs):
        """
        Run with Gym Env.
        """
        match self.driver:
            case "proxy":
                return await super().run(*args, **kwargs)

            case "gymnasium":
                return await self.start_sig_env(*args, **kwargs)


class DevSIGAgent(BaseSIGAgent):
    """
    May move tested parts into BaseSIGAgent.
    """
