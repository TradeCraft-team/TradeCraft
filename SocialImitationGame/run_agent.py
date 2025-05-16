"""
"""
import asyncio
from typing import Dict
from pathlib import Path
from jinja2 import Template
from langchain_core.tools import Tool
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from src.agent_proxy.proxy_old import Proxy, DummyProxy, ToolProxy
from src.agent_proxy.crafting_tools import ProxiedAgent
from src.agent_proxy.utils import print
from src.proxied_games.tradeCraft import *


async def simple_verify():
    from langchain import hub
    from langchain.agents import create_react_agent, AgentExecutor
    import os
    from dotenv import load_dotenv, find_dotenv
    from langchain_openai import AzureChatOpenAI, ChatOpenAI, AzureOpenAI

    assert load_dotenv(find_dotenv(filename='.env', raise_error_if_not_found=True))

    os.environ["LANGCHAIN_PROJECT"] = 'sig_tool_test'

    p = ToolProxy("localhost", 5000, username="llm-agent-dummy-tester")
    # game_dynamics = BASIC_TC_GAME_DYNAMICS
    # language_processor = BASIC_TC_LANGUAGE_PROCESSOR
    # p = ToolProxy("localhost", 5000,
    #               username="llm-agent-dummy-tester",
    #               game_dynamics=game_dynamics,
    #               language_processor=language_processor)
    
    pagent = ProxiedAgent(p)
    await p._prelogin()
    await asyncio.sleep(5)

    @tool
    async def get_item_info(item_name):
        """
        Get crafting recipes related to `item_name`.
        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}), each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number} where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.
        """
        print("get_item_info", item_name, s=1)
        nonlocal pagent
        return await pagent.get_item_info(item_name)

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
            message = {"decision": "`approve` or `reject`",
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


    @tool
    async def possible_recipes_from_hand(message: dict):
        """
        Get the list of possible craft recipes affordable by your hand resources.

        Args:
            message = {"username": your username}
        """
        nonlocal p
        return await p.toolize_possible_recipes_from_hand(message)

    @tool
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

    prompt_template = hub.pull("hwchase17/react")
    llm = AzureChatOpenAI(model='gpt-4o-2024-05-13', temperature=0.,
                      api_key=os.environ['BIGAI_OAI_API_KEY'],
                      api_version=os.environ['BIGAI_API_VERSION'],
                      azure_endpoint=f"{os.environ['BIGAI_API_BASE']}/{os.environ['BIGAI_REGION']}",
                      streaming=False)
    # llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
    tools = [get_item_info,
             submit_proposal,
             approval_or_reject,
             craft_done,
             craft_recipe_check,
             craft_recipe_apply,
             possible_recipes_from_hand,
             check_event_history]
    
    agent = create_react_agent(llm, tools, prompt_template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, stream_runnable=False)

    game_init_path = Path(__file__).resolve().parents[1] / 'src' / 'proxied_games' / 'tradeCraft' / 'prompts' / 'game_init.txt'
    with open(game_init_path, 'r') as f:
        game_init = Template(f.read())
    game_start_instruction = game_init.render(username=p.fsm.username)

    await agent_executor.ainvoke({'input': game_start_instruction})
    # agent_executor.ainvoke({'input': 'how to craft a sword'})

    while p.fsm.state != "game_over":
        await asyncio.sleep(5)


def custom_react_prompt():
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    return PromptTemplate(template=template, 
                          input_variables=['input', 'agent_scratchpad', 'tool_names', 'tools'])

if __name__ == '__main__':
    asyncio.run(simple_verify())
