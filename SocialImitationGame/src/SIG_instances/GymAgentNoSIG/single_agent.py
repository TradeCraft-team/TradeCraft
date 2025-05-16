"""
Graph state maintainer: main entry
"""

import re
import asyncio

from langchain_core.prompts import PromptTemplate
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
# from src.llm_proxy.app import run_llm_proxy
from .react_parser import ReActSingleInputOutputParser as OutParser
from ...agent_proxy.utils import print, logger
from langchain_core.runnables import RunnableConfig

from src.agent_proxy import env_db_logger

from langchain_core.runnables import RunnableLambda

CUR_PATH = Path(__file__).parent

from collections import defaultdict


def extract_hand_blocks(text):
    """提取每位玩家的 hand craft 项目列表（不含更新说明行）"""
    player_blocks = re.findall(
        r'Hand items has been updated for player \*\*(.+?)\*\*, now player \*\*\1\*\* has:\n(.*?)(?=\n\n|\Z)',
        text,
        flags=re.DOTALL
    )
    if not player_blocks:
        return {}
    return {player_id: items_block.strip() for player_id, items_block in player_blocks}
def extract_game_info(info):
    text = info.get("translated", "")

    # 提取 Final Goal（带数量）
    goal_match = re.search(r'Final Goal is to get \*{3}(.*?)\*{3}', text)
    final_goal = goal_match.group(1).strip() if goal_match else None

    return {
        "final_goal": final_goal,
    }

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
    def __init__(self, env, game_id,llm,port=8191, **kwargs,):
        """
        Initialize.
        """
        # run_llm_proxy(host="127.0.0.1", port=port)
        # original_endpoint = llm.azure_endpoint
        # llm.azure_endpoint = f"http://127.0.0.1:{port}/{original_endpoint.replace('https://', '').replace('http://', '')}"
        # print(llm.azure_endpoint)
        self.env = env
        self.dblogger = lambda mtype: (RunnableLambda(
            lambda x, **kwargs: env_db_logger(env, mtype, sleep=2)(x)))
        self.llm = llm

        self.log_llm = lambda misc: (self.dblogger({"mtype": "prompt",**misc}).bind(stop=[])
                                    | llm.bind(stop=["\nObservation"])
                                    | self.dblogger({"mtype": "model_gen", **misc}).bind(stop=[]))

        self.config = RunnableConfig(tags=[game_id])
        self.tool_dict = dict(
            (t.name, t) for t in env.tools if "system" in t.tags)
        self.proposer_retry_time=0
        # print(*[x.args_schema.schema() for x in self.tool_dict.values()],
        #       sep="\n\n")
        self.history = []
        self.recent_messages = []
        self.goal = ""
        self.target = None
        self.opponent_nme = None
        self.hand_crafts = None
        self.opponent_hand_crafts = None

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
                prompt_file.stem] = PromptTemplate.from_template(content)

        # print(self.prompt_templates)
    
    async def generate_action(self, info):
        """
        """
        print("Agent is trying to generate an action...")
        extract_info = extract_game_info(info)
    
        if extract_info.get('final_goal') is not None:
            self.target = extract_info['final_goal']
        print("tttttttttttttttttttttttt",self.target,s=1)
        self._maintain_history(info["translated"].split("\n#"))
        phase = self.router()
        self._maintain_handcraft(info)
        print(f"🤖: SelfHand: {self.hand_crafts}", s=1)
        print(f"🤖: Opponent: {self.opponent_hand_crafts}", s=1)
        self._show_history()
        
    
        return await self.processors[phase]()
    
    def _show_history(self, ):
        for item in self.history:
            print('-'*50)
            print(f"{item}", s = 5)


    def _maintain_history(self, new_entry: str, max_length: int = 10):
        """
        Maintain the self.history buffer with a fixed maximum length.

        Args:
            new_entry (str): The new entry to append.
            max_length (int): The maximum allowed length of the history.
        """
        self.history.extend(new_entry)
        print(f"🤖 Currently the length of history is: {len(self.history)}", s = 1)
        if len(self.history) > max_length:
            self.history.pop(0)

    def _maintain_handcraft(self, info):
        text = info.get("translated", "")
        hands = extract_hand_blocks(text)
      
        if hands:  
            self.hand_crafts = hands.get(self.self_id, self.hand_crafts)
            self.opponent_hand_crafts = hands.get(self.other_players[0], self.opponent_hand_crafts)
        else:
            print(f"Nothing changed in hand crafts, continue.")
        

    def router(self):
        """
        Returns which type of prompt template to use.
        """
        if self.goal == "":

            class Response(BaseModel):
                goal: str = Field(description="The goal part in the message.")
                self_id: str = Field(
                    description="The player id of self, emphasized.")
                other_players: list[str] = Field(
                    description="List of ALL OTHER players' ids.")

            llm_structured_output = (self.llm.with_structured_output(Response, method="function_calling")
                                     | self.dblogger("struct_gen"))
            result = llm_structured_output.invoke(self.history[0])
            # print(result, s=4)
            self.goal = result.goal
            self.self_id = result.self_id
            self.other_players = result.other_players

        # print(self.history, s=27)
        cnt = len(self.history)
        while (cnt := cnt - 1) >= 0:
            for key, val in self.phase_clue.items():
                if re.findall(val, self.history[cnt]):
                    # print(" " * 79, f"\nPhase: {key}", s=6)
                    self.last_key_msg = self.history[cnt]
                    return key

        raise Exception("Phase not defined.")

    async def proposer(self):
        """
        Making Proposals
        """
        # await asyncio.sleep(10)  # optional delay
        # self.plan = await self.planner("making a proposal")

        class Response(BaseModel):
            offer: str = Field(description="Items you want to offer.")
            request: str = Field(description="Items you want from partner.")
            partner: str = Field(
                description="The player you want to trade with.")
            message: str = Field(
                description="The message you want to send to partner.")

        tools = [t for n, t in self.tool_dict.items() if n in ("item_info")
                 ] + [rethink]
        agent = create_react_agent(self.log_llm({"role": "proposer"}),
                                   tools,
                                   self.prompt_templates["proposer"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False,
                                       max_iterations=8,
                                       handle_parsing_errors=True)
        # print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", len(self.history))
        # print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn",self.history)
        resp = await agent_executor.ainvoke(
                {
                    "intro": self.intro,
                    # "plan": self.plan,
                    "target": self.target, 
                    "opponent_id": self.other_players[0], 
                    "observations": "\n".join(self.history),
                    "self_id": self.self_id, 
                    "hand_crafts": self.hand_crafts, 
                    "opponents_crafts": self.opponent_hand_crafts, 
                    "tools": render_text_description(tools)
                },config=self.config)
        # print(resp)
        if not resp["output"]:
            print("⚠️ Reached max_iterations without producing Final Answer.")
            proposal = {
            "self": self.self_id,
            "partner": self.other_players[0],
            "request":{},
            "offer": {}}
            assert isinstance(proposal["request"], dict)
            assert isinstance(proposal["offer"], dict)
            message = 'Maximum number of iterations reached without outputting correct information'
            return ("submit_proposal", {"proposal": proposal, "message": message})
        self.proposer_retry_time+=1
        out = re.findall("```json\n([.]*)\n```", resp["output"], re.DOTALL)

        prompt = """
        Please extract necessary info from the following text, including:
        - "partner" (a string,the other player's id),
        - "request" (a JSON string of dict, e.g., '{{"minecraft:iron_ore": 2}}'),
        - "offer" (a JSON string of dict, e.g., '{{"minecraft:coal": 1, "minecraft:stick": 2}}'),
        - "message" (a complete English sentence).
        ⚠️ All dictionary fields must be in **valid JSON format**, i.e., strings like '{{"item_name": quantity}}'.
        ❌ DO NOT output 'item1: 1, item2: 2' format — this is invalid.
        {state}
        """
        prompt = PromptTemplate.from_template(prompt)
        llm_structured_output = (prompt
                                 | self.llm.with_structured_output(Response)
                                 | self.dblogger("struct_gen"))
        result = llm_structured_output.invoke({"state": resp["output"]})

        # print(result, s=1)
        proposal = {
            "self": self.self_id,
            "partner": result.partner,
            "request": eval(result.request),
            "offer": eval(result.offer)
        }
        assert isinstance(proposal["request"], dict)
        assert isinstance(proposal["offer"], dict)
        message = result.message
        if self.proposer_retry_time>4:
            proposal = {
            "self": self.self_id,
            "partner": self.other_players[0],
            "request":{},
            "offer": {}}
            assert isinstance(proposal["request"], dict)
            assert isinstance(proposal["offer"], dict)
            message = 'Formatting issues repeated multiple times'
            return ("submit_proposal", {"proposal": proposal, "message": message})
        return ("submit_proposal", {"proposal": proposal, "message": message})

    async def decision_maker(self):
        """
        Making decision
        """
        # await asyncio.sleep(5)  # optional delay

        # self.plan = await self.planner("making decision")

        class Response(BaseModel):
            decision: str = Field(
                description="The decision (accept / reject) on recent proposal."
            )
            message: str = Field(
                description="The message you want to send to partner.")

        tools = [t for n, t in self.tool_dict.items() if n in ("item_info")
                 ] + [rethink]
        agent = create_react_agent(self.log_llm({"role": "decision_maker"}),
                                   tools,
                                   self.prompt_templates["decision_maker"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False,
                                       max_iterations=8,
                                       handle_parsing_errors=True)
        # print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", count_elements(self.history[0]))
        # print
        # (self.history)

        resp = await agent_executor.ainvoke(
            {
                "intro": self.intro,
                # "plan": self.plan,
                "target": self.target, 
                "opponent_id": self.other_players[0], 
                "observations": "\n".join(self.history),
                "proposal": self.last_key_msg,
                "self_id": self.self_id, 
                "hand_crafts": self.hand_crafts, 
                "opponents_crafts": self.opponent_hand_crafts, 
                "tools": render_text_description(tools)
            }, config=self.config)
        # print(resp)
        if resp["output"]=='Agent stopped due to iteration limit or time limit.':
            print("⚠️ Reached max_iterations without producing Final Answer.")
            return ("approval_or_reject", {
            "decision": 'reject',
            "message": 'Maximum number of iterations reached without outputting correct information'
            })

        prompt = """Please extract necessary info from the following text, including
        "decision", "message", forming a complete proposal.
        {state}
        """
        prompt = PromptTemplate.from_template(prompt)
        llm_structured_output = (prompt
                                 | self.llm.with_structured_output(Response)
                                 | self.dblogger("struct_gen"))
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
        # await asyncio.sleep(10)
        self.plan = await self.planner("crafting")
        self.proposer_retry_time=0
        tools = [
            t for n, t in self.tool_dict.items()
            if n in ("item_info", "possible_recipes_from_hand",
                     "craft_recipe_check", "craft_recipe_apply")
        ] + [rethink]
        agent = create_react_agent(self.log_llm({"role": "planner"}),
                                   tools,
                                   self.prompt_templates["crafter"],
                                   output_parser=OutParser())
        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False,
                                       max_iterations=10,
                                       handle_parsing_errors=True)
        # await asyncio.sleep(20)
        # print("lennnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", count_elements(self.history[0]))
        # print(self.history)

        resp = await agent_executor.ainvoke(
            {
                "crafting_rule_set": "MineCraft",
                "plan": self.plan,
                "target":self.target, 
                "opponent_id": self.other_players[0], 
                "observations": "\n".join(self.history),
                "intro": self.intro,
                "self_id": self.self_id, 
                "hand_crafts": self.hand_crafts, 
                "opponents_crafts": self.opponent_hand_crafts, 
                "tools": render_text_description(tools)
            }, config=self.config)
        # print(resp)
        if not resp["output"]=='Agent stopped due to iteration limit or time limit.':
            print("⚠️ Reached max_iterations without producing Final Answer.")
        return ("craft_done", {})

    async def planner(self, target: str):
        """
        Planner
        """
        # await asyncio.sleep(5)
        class Response(BaseModel):
            plan: str = Field(description="The plan itself.")

        tools = [
            t for n, t in self.tool_dict.items()
            if n in ("item_info", "possible_recipes_from_hand")
        ] + [rethink]
        agent = create_react_agent(self.log_llm({"role": "crafter"}),
                                   tools,
                                   self.prompt_templates["planner"],
                                   output_parser=OutParser())
        

        agent_executor = AgentExecutor(agent=agent,
                                       tools=tools,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False,
                                       max_iterations=5,
                                       handle_parsing_errors=True)


        resp = await agent_executor.ainvoke(
            {
                "target": target,
                "goal": self.target,
                "opponent_id": self.other_players[0],
                "hand_crafts": self.hand_crafts,
                "opponents_crafts": self.opponent_hand_crafts,
                "intro": self.intro,
                "plan": self.plan,
                "observations": "\n".join(self.history),
                "self_id": self.self_id, 
            },config=self.config)
        
        prompt = """Please extract necessary info from the following text, including
        "plan", forming a complete plan.
        {state}
        """
        prompt = PromptTemplate.from_template(prompt)
        llm_structured_output = (prompt
                                 |self.llm.with_structured_output(Response)
                                 | self.dblogger("struct_gen"))
        result = llm_structured_output.invoke(resp["output"])
        return result.plan
