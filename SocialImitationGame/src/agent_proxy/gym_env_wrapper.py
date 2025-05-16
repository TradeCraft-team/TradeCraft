"""
Gymnasium Environments
"""

from typing import Callable
from .utils import print
from .gym_env import GameProxyBaseEnv, GameProxyBaseAsyncEnv
from .gym_wrappers import TooledWrapper, SynchronizeWrapper
from .proxy import ToolProxy


class SyncProxyEnv(GameProxyBaseEnv):
    pass


class AsyncTooledProxyEnv(TooledWrapper):
    """
    Base class of Proxy Environment with Tools
    """
    metadata = {"async": True, "render_modes": []}
    mark_tool = TooledWrapper.mark_tool

    def __init__(self, addr: str, port: int, proxy=ToolProxy, **kwargs):
        """
        Initialize.

        kwargs:
        -------
        docs: dict, (tool_name: str, tool_doc: str) the doc description
                  used in `langchain.tools.tool` registration.
        system_tool_async: bool = True   # should be False?
        """
        # Initialize the environment, espeically the proxy.
        env = GameProxyBaseAsyncEnv(addr, port, proxy=proxy, **kwargs)
        # mark system tools from proxy dynamically while instantiation.
        _gd = env.unwrapped.proxy.game_dynamics

        self.system_tool_async = kwargs.get("system_tool_async", True)

        system_tool_gen = (self.asystem_tool_gen
                           if self.system_tool_async else self.system_tool_gen)
        for t in _gd._game_dynamics:
            t_name = _gd.eventname_to_toolname(t)
            if t_name in self.marked_tools:
                print(f"Tool `{t_name}` is now replaced by a system tool.")
            setattr(
                self.__class__,  # class
                t_name,  # name
                self.__class__.mark_tool(
                    system_tool_gen(
                        t_name,
                        kwargs.get("docs", {}).get(t_name,
                                                   f"NO doc for {t_name}"),
                    ),
                    is_async=self.system_tool_async,
                    marked_tools=self.__class__.marked_tools,
                ),  # method
            )

        # Initialize along parent, register all tools.
        super().__init__(env)

    def asystem_tool_gen(self, t_name: str, doc: str) -> Callable:
        """
        Generate self method from `self.proxy.toolize_<toolname>`
        """

        async def inner(self, messages):
            """
            Standard template for tool

            As langchain uses pydantic to control arg formats.
            tool-calling format is thus unified in this term.
            """

            nonlocal t_name
            action = (t_name, messages)
            print("ACTION =", action, s=1)
            _, _, _, _, info = await self.step(action)
            return info["translated"]

        inner.__name__ = t_name
        inner.__doc__ = doc
        setattr(self.__class__, t_name, inner)

        return inner

    def system_tool_gen(self, t_name: str, doc: str) -> Callable:
        """
        Generate self method from `self.proxy.toolize_<toolname>`
        """

        def inner(self, messages):
            """
            Standard template for tool

            As langchain uses pydantic to control arg formats.
            tool-calling format is thus unified in this term.
            """

            nonlocal t_name
            action = (t_name, messages)
            print("ACTION =", action, s=1)
            _, _, _, _, info = self.step(action)
            return info["translated"]

        inner.__name__ = t_name
        inner.__doc__ = doc
        setattr(self.__class__, t_name, inner)

        return inner

    @mark_tool("accessory")
    async def check_event_history(self, messages: dict):
        """
        Check all received events from server, including error messages.
        messages: dict = {}
        """
        return self.env.proxy.language_processor.generate_prompt(
            event="",
            unread_msgs=self.env.proxy.unread_messages,
            read_msgs=self.env.proxy.read_messages,
            show_history=True)
