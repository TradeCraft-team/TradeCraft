"""
"""
import asyncio
import gymnasium
from typing import Dict
from langchain_core.tools import Tool
from langchain_core.tools import tool
from src.agent_proxy.proxy import Proxy, ToolProxy
from src.agent_proxy.utils import print
from src.SIG_core import BaseSIGAgent, GymSIGAgent

from src.proxied_games.tradeCraft import *
from src.SIG_instances.MechanicalTurk import MechanicalTurk
from src.SIG_instances.GymAgentNoSIG.single_agent import GymAgent
from llm_factory import LLMFactory

async def simple_verify(sig_cls: BaseSIGAgent):
    import os
    from dotenv import load_dotenv, find_dotenv

    assert load_dotenv(
        find_dotenv(filename='.env', raise_error_if_not_found=True))

    os.environ["LANGCHAIN_PROJECT"] = 'sig_tool_test'
    """ EXAMPLE FOR CALLING @tool DECORATED FUNCTIONS """
    # @tool
    # async def test(x: list):
    #     "TEST"
    #     print(f"test function called", *x, s=1)
    #     await asyncio.sleep(1)

    #     print(f"test function called", *x, s=1)
    #     return ""

    # a = await test.arun({"x":["123OK"]})

    game_dynamics = BASIC_TC_GAME_DYNAMICS
    language_processor = BASIC_TC_LANGUAGE_PROCESSOR
    p = ToolProxy("localhost",
                  5001,
                  game_dynamics=game_dynamics,
                  language_processor=language_processor)
    await p._prelogin()
    # await asyncio.sleep(3)

    @tool
    async def item_info(item_name):
        """
        Get crafting recipes related to `item_name`.
        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}), each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number} where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.

        Args:
            item_name = "item_name"
        """

        nonlocal p
        return await p.toolize_item_info(item_name)

    @tool
    async def submit_proposal(message: dict):
        """
        Submit proposal to game. Only available when `server__start_proposal` is received.

        Args:
            message = {"proposal":{"offer": {"item_name": amount},
                                   "request": {"item_name": amount},
                                   "self": your_username,
                                   "partner": username_of_partner},
                       "message":"a message to partner to convince her/him."}
        """
        nonlocal p
        return await p.toolize_submit_proposal(message)

    @tool
    async def approval_or_reject(message: dict):
        """
        Decide to approve or reject a proposal. Only available when `server__proposal` is received.

        Args:
            message = {"decision": "`accept` or `reject`",
                     "message":"a message to partner to convince her/him."}
        """
        nonlocal p
        return await p.toolize_approval_or_reject(message)

    @tool
    async def craft_done(message: dict = {}):
        """
        Done with the crafting, tell host to be ready for next trading.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_craft_done(message)

    @tool
    async def craft_recipe_check(message: dict):
        """
        Check whether a recipe is correct and affordable by self's resources.

        Args:
            message = {"recipe":{"input": {"item_name": amount},
                               "output":  {"item_name": amount},}}
        """
        nonlocal p
        return await p.toolize_craft_recipe_check(message)

    @tool
    async def craft_recipe_apply(message: dict):
        """
        After recipe is checked and is valid, you may use this tool to apply the recipe you
        have just checked.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_craft_recipe_apply(message)

    # @tool
    # async def possible_recipes_from_hand(message: dict):
    #     """
    #     Get the list of possible craft recipes affordable by your hand resources.

    #     Args:
    #         message = {"username": your username}
    #     """
    #     nonlocal p
    #     return await p.toolize_possible_recipes_from_hand(message)

    @tool
    async def possible_recipes_from_hand(username: str = ""):
        """
        Get the list of possible craft recipes affordable by your hand resources.

        Args:
            username: your player name
        """
        nonlocal p
        return await p.toolize_possible_recipes_from_hand(
            {"username": username})

    @tool
    async def check_event_history(username: str = ""):
        """
        Check all the incoming / outgoing messages.

        Args:
            message: str. Should be a string containing username.
        """
        nonlocal p
        return p.fsm.read_messages + p.fsm.unread_messages

    # prompt_template = hub.pull("hwchase17/react")
    # llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
    tools = [
        item_info, submit_proposal, approval_or_reject, craft_done,
        craft_recipe_check, craft_recipe_apply, possible_recipes_from_hand,
        check_event_history
    ]

    # print(get_item_info.name, "\n\n")
    # print(get_item_info.description, "\n\n")
    # print(get_item_info.to_json())

    agent = sig_cls(p, full_tool_set=tools)
    game_start_instruction = agent.game_init.render(username=p.fsm.username)

    await agent.run({'input': game_start_instruction})


async def gym_verify(sig_cls: GymSIGAgent):
    import os
    from dotenv import load_dotenv, find_dotenv

    assert load_dotenv(
        find_dotenv(filename='.env', raise_error_if_not_found=True))

    os.environ["LANGCHAIN_PROJECT"] = 'sig_tool_test'
    """ EXAMPLE FOR CALLING @tool DECORATED FUNCTIONS """
    # @tool
    # async def test(x: list):
    #     "TEST"
    #     print(f"test function called", *x, s=1)
    #     await asyncio.sleep(1)

    #     print(f"test function called", *x, s=1)
    #     return ""

    # a = await test.arun({"x":["123OK"]})

    game_dynamics = BASIC_TC_GAME_DYNAMICS
    language_processor = BASIC_TC_LANGUAGE_PROCESSOR
    env = gymnasium.make("sig/AsyncProxyTooled-v0",
                         addr="127.0.0.1",
                         port=5000,
                         docs=BASIC_TC_GAME_CONFIG.tool_docs,
                         game_dynamics=BASIC_TC_GAME_DYNAMICS,
                         language_processor=BASIC_TC_LANGUAGE_PROCESSOR)

    tools = env.tools
    print(tools)

    # print(get_item_info.name, "\n\n")
    # print(get_item_info.description, "\n\n")
    # print(get_item_info.to_json())

    agent = sig_cls(env, full_tool_set=tools)
    # game_start_instruction = agent.game_init.render(username=p.fsm.username)

    return await agent.run({'input': ""})


if __name__ == '__main__':
    llm = LLMFactory(model='gpt-4o-mini-2024-07-18', provider='azure_openai')
    # sig_cls = GymAgent(llm=llm)
    sig_cls=MechanicalTurk
    asyncio.run(gym_verify(sig_cls))
