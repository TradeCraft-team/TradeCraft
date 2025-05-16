"""
graph agent or full autonomous agent
generalize ReAct agent not only for one single turn, but for the whole game
which participates in the game by the full toolset just like a human player
"""

import os
import ast
import re
from typing import Literal, Optional
import asyncio
import gymnasium
from datetime import datetime
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv, find_dotenv
from llm_factory import LLMFactory
from src.SIG_instances.graph_prototype.prototype import GraphAgent
# from src.SIG_instances.GraphStateMaintainer import GraphStateMaintainer as GraphAgent
# from src.SIG_instances.GSM_suki import GraphStateMaintainer as GraphAgent
from src.proxied_games.tradeCraft import *
from src.agent_proxy.proxy import ToolProxy


async def construct_and_run_agent():

    game_config = BASIC_TC_GAME_CONFIG
    game_dynamics = BASIC_TC_GAME_DYNAMICS
    language_processor = BASIC_TC_LANGUAGE_PROCESSOR

    p = ToolProxy(addr="localhost",
                  port=5000,
                  game_dynamics=game_dynamics,
                  language_processor=language_processor)

    await p._prelogin()

    @tool
    async def item_info(item_name: str):
        """
        Get crafting recipes related to `item_name`.
        Can be called in **any phase**.

        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}), each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number} where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.

        Args:
            item_name = item_name
        """

        nonlocal p
        item_name = item_name.lower()
        return await p.toolize_item_info(item_name)

    # Check all the incoming / outgoing messages of the user. # previous version
    @tool
    async def check_event_history(username=""):
        """
        Check the server-maintained history of all game events sent to and received from the server for the current player.
        Can be called in **any phase**.

        Args:
            username: str = your player name
        """
        nonlocal p
        history = p.language_processor.generate_prompt(
            event='',
            unread_msgs=p.unread_messages,
            read_msgs=p.read_messages,
            show_history=True)
        return history

    @tool
    async def submit_proposal(message):
        """
        Submit proposal to game. Only available when `server__start_proposal` is received.
        Can be called in **Phase 1** only.

        Args:
            message = {
                "proposal": {
                    "offer": {"item_name": amount},
                    "request": {"item_name": amount},
                    "self": your_username,
                    "partner": username_of_partner
                },
                "message": "a message to partner to convince her/him."
            }
        """
        nonlocal p
        if isinstance(message, str):
            message = ast.literal_eval(message)
        return await p.toolize_submit_proposal(message)

    @tool
    async def approval_or_reject(message):
        """
        Decide to approve or reject a proposal. Only available when `server__proposal` is received.
        Can be called in **Phase 2** only.

        Args:
            message = {
                "decision": "accept or reject",
                "message": "a message to partner to convince her/him."
            }
        """
        nonlocal p
        if isinstance(message, str):
            message = ast.literal_eval(message)
        return await p.toolize_approval_or_reject(message)

    @tool
    async def craft_done(message):
        """
        Done with the crafting, tell host to be ready for next trading.
        Can be called in **Phase 3** only.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        if isinstance(message, str):
            message = ast.literal_eval(message)
        return await p.toolize_craft_done(message)

    @tool
    async def craft_recipe_check(message):
        """
        Check whether a recipe is correct and affordable by self's resources.
        Can be called in **Phase 3** only.

        Args:
            message = {
                "recipe": {
                    "input": {"item_name": amount},
                    "output": {"item_name": amount},
                }
            }
        """
        nonlocal p

        def replace_fractions(text: str):
            return re.sub(r'(\d+)\s*/\s*(\d+)', r'"\1/\2"', text)

        if isinstance(message, str):
            try:
                message = ast.literal_eval(message)
            except ValueError as e:
                # "fuel": 1/8 => "fule": 0.125
                # message = eval(message)
                message = replace_fractions(message)
                message = ast.literal_eval(message)
        return await p.toolize_craft_recipe_check(message)

    @tool
    async def craft_recipe_apply(message):
        """
        After recipe is checked and is valid, you may use this tool to apply the recipe you
        have just checked using "craft_recipe_check".
        Can be called in **Phase 3** only.

        Args:
            message = {
                "recipe": {
                    "input": {"item_name": amount},
                    "output": {"item_name": amount},
                }
            }
        """
        nonlocal p
        if isinstance(message, str):
            message = ast.literal_eval(message)
        return await p.toolize_craft_recipe_apply(message)

    @tool
    async def possible_recipes_from_hand(username: str = ""):
        """
        Get the list of possible craft recipes affordable by your hand resources.
        Can be called in **Any Phase**.

        Args:
            username: str = your player name
        """
        nonlocal p
        return await p.toolize_possible_recipes_from_hand(
            {"username": username})

    tools = [
        item_info, check_event_history, submit_proposal, approval_or_reject,
        possible_recipes_from_hand, craft_recipe_check, craft_recipe_apply,
        craft_done
    ]

    # gpt-4o-2024-05-13 -> gpt-4o-2024-08-06
    model = 'gpt-4o-2024-08-06'
    # for testing
    # model = 'gpt-4o-mini-2024-07-18'
    llm = LLMFactory(model=model, provider='azure_openai')
    agent = GraphAgent(proxy=p, full_tool_set=tools, llm=llm)

    agent.save_graph_to_local('graph.png')
    game_start_instruction = agent.game_init.render(username=p.fsm.username,
                                                    max_turns=30)

    await agent.run({'input': game_start_instruction})


async def construct_and_run_with_env():
    """
    """

    env = gymnasium.make("sig/ProxyTooled-v0",
                         addr="localhost",
                         port=5000,
                         game_dynamics=BASIC_TC_GAME_DYNAMICS,
                         language_processor=BASIC_TC_LANGUAGE_PROCESSOR)
    tools = env.tools
    print(tools)

    # gpt-4o-2024-05-13 -> gpt-4o-2024-08-06
    model = 'gpt-4o-2024-08-06'
    # for testing
    # model = 'gpt-4o-mini-2024-07-18'
    llm = LLMFactory(model=model, provider='azure_openai')
    agent = GraphAgent(env, full_tool_set=tools, llm=llm)

    # game_start_instruction = agent.game_init.render(
    #     username=env.proxy.fsm.username, max_turns=30)

    await agent.run({'input': ""})


if __name__ == "__main__":
    assert load_dotenv(
        find_dotenv(filename='.env', raise_error_if_not_found=True))
    asyncio.run(construct_and_run_agent())
    # asyncio.run(construct_and_run_with_env())
