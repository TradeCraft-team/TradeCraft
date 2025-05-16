"""
Real Gymnasium Environment
"""
import asyncio
import gymnasium
import json
import numpy as np
from gymnasium import Wrapper, utils
from gymnasium.spaces import Sequence, Tuple, Discrete, Dict, Box
from datetime import datetime as dt
from pydantic import BaseModel

from .proxy import ToolProxy
from .utils import print
from .gym_wrappers import SynchronizeWrapper
from ..utils.dbhandler import save_log_to_db
import time

class GameProxyBaseAsyncEnv(gymnasium.Env):
    """
    GameProxyEnvironment in gymnasium
    """
    metadata = {"async": True, "render_modes": []}

    def __init__(self, addr: str, port: int, proxy=ToolProxy, **kwargs):
        """
        Initialize.
        """
        self.addr = addr
        self.port = port
        self.proxy = proxy(self.addr, self.port, **kwargs)
        self.tool_dict = dict(
            enumerate([
                self.proxy.game_dynamics.eventname_to_toolname(x)
                for x in self.proxy.game_dynamics._game_dynamics
            ]))  # do some "get_tools" upgrade
        # print(self.tool_dict)
        self.item_dict = {0: "stick"}

        # Baby model for making Gymnasium work.
        self._action_space = Tuple(
            [Box(0, 1, dtype=int),
             Dict({"messages": Box(0, 1, dtype=int)})])

        # To be implemented. In LLM this is not so important.
        self._observation_space = Box(0, 1, dtype=int)

    @property
    def action_space(self):

        return self._action_space

    @property
    def observation_space(self):

        return self._observation_space

    async def reset(self, seed: int | None = None, options: dict = {}):
        """
        Reset
        """
        await self.proxy._prelogin()
        for tool in self.proxy.entry_tool:
            res = await self.step((tool, {"messages": {}}))
            # print("RESET", res)

        obs, _, _, _, info = res
        return obs, info

    async def step(self, action):
        """
        """
        observation = np.array([0])
        reward = 0
        terminated = False
        truncated = False
        info = {}

        match action:
            case (np.ndarray() as tool_id, dict() as msg):
                func_name = self.tool_dict.get(tool_id[0])
                kwargs = msg

            case (str(name), d):
                func_name = name
                kwargs = d

            case (func, dict() as d) if callable(func):
                func_name = func.__name__
                kwargs = d

            case str() as name:
                func_name = name
                kwargs = {}

        # print(func_name, kwargs, s=4)
        try:
            res = await getattr(self.proxy, f"toolize_{func_name}")(kwargs)
            info = {"translated": res}

        except Exception as e:
            raise e

        try:
            observation = await self.proxy.game_dynamics.get_obs()
        except AttributeError:
            observation = np.array([0])
        except Exception as e:
            print(e)
            raise e

        terminated = "# Game Over" in info or self.proxy.stop_status
        return observation, reward, terminated, truncated, info

    async def close(self):
        """
        """
        return await getattr(self.proxy, "toolize__quit_game")({
            "messages": ""
        })

    async def render(self, *args, **kwargs):
        pass

    def convert_message_to_log_dict(self, x, mtype: str | dict) -> dict:
        """
        Convert a message to log dict format.
        """
        match x:
            case BaseModel() as bm:
                msg = bm.model_dump_json()
            case _:
                msg = json.dumps(x)

        match mtype:
            case str():
                mtype = {"mtype": mtype}
            case dict():
                pass
            case _:
                raise Exception("Incorrect mtype.")

        return {
            "player": self.proxy.language_processor.user_name,
            "game": self.proxy.language_processor.gamename,
            "msg": msg,
            "time": dt.now().strftime("%Y%m%d-%H%M%S-%f"),
            **mtype
        }


class GameProxyBaseEnv(Wrapper):

    metadata = {}

    def __init__(self, addr: str, port: int, proxy=ToolProxy, **kwargs):
        """
        Initialize.
        """
        env = SynchronizeWrapper(
            GameProxyBaseAsyncEnv(addr, port, proxy=proxy, **kwargs))
        super().__init__(env)


def env_db_logger(env,
                  mtype: str | dict = "model_generation",
                  sleep: float = 0.,
                  ruleset="TradeCraft"):

    env = env.env if isinstance(env, Wrapper) else env
    lp = env.proxy.language_processor

    def _logger(x):
        nonlocal env, mtype, lp, sleep

        collection = (f"Duo_{lp.gamename}" + f"_{lp.user_name}")
        save_log_to_db(collection, env.convert_message_to_log_dict(x, mtype))

        # asyncio.sleep(sleep)
        time.sleep(sleep)
        return x

    return _logger
