"""
Graph state maintainer: main entry
"""

import re
import asyncio

from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.tools.render import render_text_description
from pydantic import BaseModel, Field
from pathlib import Path
from jinja2 import Template
from typing import Dict
import json
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.tools import tool
from src.llm_proxy.app import run_llm_proxy
from .react_parser import ReActSingleInputOutputParser as OutParser
from ...agent_proxy.utils import print, logger

CUR_PATH = Path(__file__).parent


@tool
def rethink(messages: str):
    """
    Dummy Tool

    A tool which can buy you another round to rethink.
    It accepts any string for inupt and outputs empty string.

    Args:
    messages = "any string"
    """
    return ""
def count_elements(x):
    if isinstance(x, dict):
        return sum(count_elements(v) for v in x.values())
    elif isinstance(x, list):
        return sum(count_elements(i) for i in x)
    else:
        return 1  # 

class GymAgent:
    """
    Baseline Model

    An exact single agent. Play by managing workflow.
    """

    def __init__(self, env, llm,port=8191, **kwargs,):
        """
        Initialize.
        """
        # run_llm_proxy(host="127.0.0.1", port=port)
        # original_endpoint = llm.azure_endpoint
        # llm.azure_endpoint = f"http://127.0.0.1:{port}/{original_endpoint.replace('https://', '').replace('http://', '')}"
        # print(llm.azure_endpoint)
        self.env = env
        self.llm = llm

        self.tool_dict = dict(
            (t.name, t) for t in env.tools if "system" in t.tags)

        print(*[x.args_schema.schema() for x in self.tool_dict.values()],
              sep="\n\n")
        self.history = []
        self.recent_messages = []
        self.goal = ""
        self.plan = "The game just begins, no plans have been made yet!"
        # print("=" * 80)
        # print(render_text_description(self.tool_dict.values()))
        self.phase_clue = {
            "proposing_phase": R"## Proposing Phase",
            "decision_phase": R"## Decision Phase\nPlayer",
            "craft_phase": R"## Crafting Phase",
            "game_over": R"# Game Over"
        }
        self.processors = {
            "proposing_phase": self.proposer,
            "decision_phase": self.decision_maker,
            "craft_phase": self.crafter,
            "game_over": lambda: ""
        }
        # load prompt
        self.intro = kwargs.get("intro", "")
        self.prompt_templates = {}
        prompt_path = CUR_PATH / "prompts"
        for prompt_file in prompt_path.glob('*.txt'):
            with prompt_file.open('r', encoding='utf-8') as file:
                content = file.read()
            self.prompt_templates[
                prompt_file.stem] = ChatPromptTemplate.from_template
                

        print(self.prompt_templates)

    async def generate_action(self, info):
        """
        """
        self.history.extend(info["translated"].split("\n#"))
        await asyncio.sleep(10)  # optional delay
        phase = self.router()
        print("debug_ollama_generate",phase)
        # await asyncio.sleep(3)  # optional delay
        return await self.processors[phase]()

    def router(self):
        """
        Returns which type of prompt template to use.
        """
        if self.goal == "":

            class Response(BaseModel):
                goal: str = Field(description="The goal part in the message.")
                self_id: str = Field(
                    description="The player id of self, emphasized.")
                other_players: list = Field(
                    description="List of ALL OTHER players' ids.")

            llm_structured_output = self.llm.with_structured_output(Response, method="function_calling")
            print("debug_ollama",llm_structured_output)
            # print("historyyyyyyyyyyyyyyyyyyy",self.history[0])
            result = llm_structured_output.invoke(self.history[0])
            print(result, s=4)
            self.goal = result.goal
            self.self_id = result.self_id
            self.other_players = result.other_players

        print(self.history, s=27)
        cnt = len(self.history)
        while (cnt := cnt - 1) >= 0:
            for key, val in self.phase_clue.items():
                if re.findall(val, self.history[cnt]):
                    print(" " * 79, f"\nPhase: {key}", s=6)
                    self.last_key_msg = self.history[cnt]
                    return key

        raise Exception("Phase not defined.")

    async def proposer(self):
        """
        Making Proposals
        """
        await asyncio.sleep(10)  # optional delay
        self.plan = await self.planner("making a proposal")

        class Response(BaseModel):
            offer: str = Field(description="Items you want to offer.")
            request: str = Field(description="Items you want from partner.")
            partner: str = Field(
                description="The player you want to trade with.")
            message: str = Field(
                description="The message you want to send to partner.")

        tools = [t for n, t in self.tool_dict.items() if n in ("item_info")
                 ] + [rethink]
        agent = create_react_agent(self.llm,
                                   tools,
                                   self.prompt_templates["proposer"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)
        print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", len(self.history))
        print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",self.history)
        resp = await agent_executor.ainvoke(
            {
                "intro": self.intro,
                "plan": self.plan,
                "observations": "\n".join(self.history),
                "self_id": self.self_id
            }, )
        print(resp)
        out = re.findall("```json\n([.]*)\n```", resp["output"], re.DOTALL)
        # try:
        #     out = json.loads(out[0])


        # prompt = """Please extract necessary info from the following text, including
        # "partner", "request", "offer", "message", forming a complete proposal.
        # {state}
        # """
        prompt = """
        Please extract necessary info from the following text, including:
        - "partner" (a string,"agent_1"),
        - "request" (a JSON string of dict, e.g., '{{"minecraft:iron_ore": 2}}'),
        - "offer" (a JSON string of dict, e.g., '{{"minecraft:coal": 1, "minecraft:stick": 2}}'),
        - "message" (a complete English sentence).
        ⚠️ All dictionary fields must be in **valid JSON format**, i.e., strings like '{{"item_name": quantity}}'.
        ❌ DO NOT output 'item1: 1, item2: 2' format — this is invalid.
        {state}
        """
        prompt = PromptTemplate.from_template(prompt)
        llm_structured_output = prompt | self.llm.with_structured_output(
            Response)
        result = llm_structured_output.invoke({"state": resp["output"]})

        print(result, s=1)
        proposal = {
            "self": self.self_id,
            "partner": result.partner,
            "request": eval(result.request),
            "offer": eval(result.offer)
        }
        assert isinstance(proposal["request"], dict)
        assert isinstance(proposal["offer"], dict)
        message = result.message
        return ("submit_proposal", {"proposal": proposal, "message": message})

    async def decision_maker(self):
        """
        Making decision
        """
        await asyncio.sleep(5)  # optional delay

        self.plan = await self.planner("making decision")

        class Response(BaseModel):
            decision: str = Field(
                description="The decision (accept / reject) on recent proposal."
            )
            message: str = Field(
                description="The message you want to send to partner.")

        tools = [t for n, t in self.tool_dict.items() if n in ("item_info")
                 ] + [rethink]
        agent = create_react_agent(self.llm,
                                   tools,
                                   self.prompt_templates["decision_maker"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)
        print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", count_elements(self.history[0]))
        print(self.history)

        resp = await agent_executor.ainvoke(
            {
                "intro": self.intro,
                "plan": self.plan,
                "observations": "\n".join(self.history),
                "proposal": self.last_key_msg,
                "self_id": self.self_id
            }, )
        print(resp)
        prompt = """Please extract necessary info from the following text, including
        "decision", "message", forming a complete proposal.
        {state}
        """
        prompt = PromptTemplate.from_template(prompt)
        llm_structured_output = prompt | self.llm.with_structured_output(
            Response)
        result = llm_structured_output.invoke({"state": resp["output"]})

        decision = result.decision
        message = result.message
        return ("approval_or_reject", {
            "decision": decision,
            "message": message
        })

    async def crafter(self):
        """
        Crafting
        """
        await asyncio.sleep(10)
        self.plan = await self.planner("crafting")
        tools = [
            t for n, t in self.tool_dict.items()
            if n in ("item_info", "possible_recipes_from_hand",
                     "craft_recipe_check", "craft_recipe_apply")
        ] + [rethink]
        agent = create_react_agent(self.llm,
                                   tools,
                                   self.prompt_templates["crafter"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)
        await asyncio.sleep(20)
        print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", count_elements(self.history[0]))
        print(self.history)

        resp = await agent_executor.ainvoke(
            {
                "crafting_rule_set": "MineCraft",
                "plan": self.plan,
                "observations": "\n".join(self.history),
                "self_id": self.self_id
            }, )
        print(resp)
        return ("craft_done", {})

    async def planner(self, target: str):
        """
        Planner
        """
        await asyncio.sleep(5)
        class Response(BaseModel):
            plan: str = Field(description="The plan itself.")

        tools = [
            t for n, t in self.tool_dict.items()
            if n in ("item_info", "possible_recipes_from_hand")
        ] + [rethink]
        agent = create_react_agent(self.llm,
                                   tools,
                                   self.prompt_templates["planner"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)
        print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", count_elements(self.history[0]))
        print(self.history)
        resp = await agent_executor.ainvoke(
            {
                "target": target,
                "intro": self.intro,
                "plan": self.plan,
                "observations": "\n".join(self.history),
                "self_id": self.self_id
            }, )
        print("\nResponse", s=1)
        print(resp)
        llm_structured_output = self.llm.with_structured_output(Response)
        result = llm_structured_output.invoke(resp["output"])
        return result.plan
