"""
"""
import sys
sys.path.append("..")

import asyncio
from typing import Dict
from src.agent_proxy.proxy import Proxy, ToolProxy
from src.agent_proxy.crafting_tools import ProxiedAgent
from src.agent_proxy.utils import print, gen_rand_str, logger, logging
from src.proxied_games.tradeCraft import (BasicTCGameConfig,
                                            BasicTCGameDynamics,
                                            BasicTCLanguageProcessor,
                                            BASIC_TC_GAME_DYNAMICS,
                                            BASIC_TC_LANGUAGE_PROCESSOR)

TG_GAME_CONFIG = BasicTCGameConfig(addr="localhost", port=5000)



async def test_tool_proxy():

    p = ToolProxy("localhost", 5000, username="llm-agent-dummy-tester-"+gen_rand_str(3))
    await p._prelogin()

    async def item_info(item_name):
        """
        Get crafting recipes related to `item_name`.
        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}), each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number} where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.
        """
        print("get_item_info", item_name, s=1)
        nonlocal p
        return await p.toolize_item_info(item_name)


    async def old_item_info(item_name):
        """
        Get crafting recipes related to `item_name`.
        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}), each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number} where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.
        """
        print("get_item_info", item_name, s=1)
        nonlocal p
        return await p.toolize_crafting_node_nonredirect(item_name)

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

    async def approval_or_reject(message: dict):
        """
        Decide to approve or reject a proposal. Only available when `server__proposal` is received.

        Args:
            message = {"decision": "`approve` or `reject`",
                     "message":"a message to partner to convince her/him."}
        """
        nonlocal p
        return await p.toolize_approval_or_reject(message)

    async def craft_done(message: dict = {}):
        """
        Done with the crafting, tell host to be ready for next trading.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_craft_done(message)

    async def craft_recipe_check(message: dict):
        """
        Check whether a recipe is correct and affordable by self's resources.

        Args:
            message = {"recipe":{"input": {"item_name": amount},
                               "output":  {"item_name": amount},}}
        """
        nonlocal p
        return await p.toolize_craft_recipe_check(message)


    async def craft_recipe_apply(message: dict):
        """
        After recipe is checked and is valid, you may use this tool to apply the recipe you
        have just checked.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_craft_recipe_apply(message)


    async def possible_recipes_from_hand(message: dict):
        """
        Get the list of possible craft recipes affordable by your hand resources.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_possible_recipes_from_hand(message)

    async def check_event_history(username: str = ""):
        """
        Check all the incoming / outgoing messages.

        Args:
            message: str. Should be a string containing username.
        """
        print("check_event_history", s=1)
        print(username, s=2)
        nonlocal p
        return p.fsm.read_messages + p.fsm.unread_messages

    initial_msg = '''You are playing the tradeCraft game. In this game, two players starts with some hand resources, and each has a crafting target.
    Other players\' hand is visible for all, but target is each player\'s own secret.
    Two players take turns to make trading proposal and decide to accept or reject proposals. Items and crafting rules follows MineCraft, suppose you have crafting table, stone-cutting table, furnace, brewing stand, etc.
    You play this game via some tools, where you must input legal JSON-style messages. When you want to review the history of this game, you may use the tool `check_event_history`.
    In this game, your username is ''' + f"{p.fsm.username}."


    tools = [item_info,
             old_item_info,
             submit_proposal,
             approval_or_reject,
             craft_done,
             craft_recipe_check,
             craft_recipe_apply,
             possible_recipes_from_hand,
             check_event_history]
    print(initial_msg, s=26)
    username = p.fsm.username
    result = ""
    while p.fsm.state != "game_over":
        print("Tool Set:", *[x.__name__ for x in tools],s=25)
        flag = True
        while flag:
            await asyncio.sleep(0.1)
            command = input("toolName | argsJSON:")
            try:
                tool, args = command.split("|")
                tool = tool.strip()
                args = eval(args)
                print(f"Calling: {tool}({args})", s=23)
                result = await eval(tool)(args)
                flag = False
            except Exception as e:
                logger.exception(e)

        print("Tool Using Result:", s=3)
        print(result, s=24)

if __name__ == '__main__':
    asyncio.run(test_tool_proxy())
