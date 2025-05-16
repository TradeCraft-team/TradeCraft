"""
Graph state maintainer: main entry
"""
from langgraph.graph import END, StateGraph, add_messages
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from pathlib import Path
from jinja2 import Template

from langchain import hub

from .state import MentalState
from .headmates import Coordinator, Planner, Executor, Recorder

from ...SIG_core.base_sig_agent import BaseSIGAgent, GymSIGAgent
from ...agent_proxy.utils import print, logger


class GraphStateMaintainer(GymSIGAgent):
    """
    State Maintainer using Langgraph

    Necessary Headmates:
      - coordinator: the center of the star, activate others to update the state.
      - executor: interaction interface with environment, the ENTRY node.
    Extra Headmate Examples:
      - planner
      - ...
    """

    def __init__(self,
                 proxy,
                 *args,
                 extra_roles={
                     "planner": Planner,
                     "recorder": Recorder
                 },
                 **kwargs):
        """
        Initialize
        """

        super().__init__(proxy, *args, **kwargs)
        self.llm = kwargs.get("llm")

        self.system_prompt = kwargs.get(
            "system_prompt",
            "You are a skilled and strategic trader living in the world of Minecraft."
        )

        if self.llm is None:
            self.llm = AzureChatOpenAI(model="gpt-4o", temperature=0)
        self.full_tool_set = kwargs.get("full_tool_set", [])

        self.role_cls = {"coordinator": Coordinator, "executor": Executor}
        self.role_cls.update(extra_roles)
        self.roles = {
            "coordinator":
            Coordinator(role_cls=self.role_cls, llm=self.llm),
            "executor":
            Executor(role_cls=self.role_cls,
                     llm=self.llm,
                     tools=self.full_tool_set)
        }

        print(extra_roles)
        for key, cls in extra_roles.items():
            print("====", key, cls)
            self.roles[key] = cls(role_cls=self.role_cls, llm=self.llm)

        if kwargs.get('game_init'):
            with open(kwargs.get('game_init'), 'r') as f:
                self.game_init = Template(f.read())
        else:
            game_init_path = Path(__file__).resolve().parents[
                2] / 'proxied_games' / 'tradeCraft' / 'prompts' / 'game_init.txt'
            with open(game_init_path, 'r') as f:
                self.game_init = Template(f.read())

        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Build a star-shaped graph, centered at `coordinator`.
        """

        workflow = StateGraph(MentalState, )

        print(self.roles, s=2)
        for key, role in self.roles.items():
            workflow.add_node(key, role.node_callback)

        workflow.set_entry_point("executor")

        for key, role in self.roles.items():
            if key != "coordinator":
                workflow.add_edge(key, "coordinator")

        print(dict([("game_over", END)] +
                   [(x, x) for x in self.roles if x != "coordinator"]),
              s=1)
        workflow.add_conditional_edges(
            "coordinator", self.roles["coordinator"].next_agent,
            dict([("game_over", END)] +
                 [(x, x) for x in self.roles if x != "coordinator"]))
        graph = workflow.compile()
        return graph

    def _initialize_state(self, message: dict) -> MentalState:
        """
        message
        """
        self.mental_state = MentalState(message)
        return self.mental_state

    def save_graph_to_local(self, file_path: str):
        image_data = self.graph.get_graph().draw_mermaid_png()
        with open(file_path, 'wb') as file:
            file.write(image_data)

    async def start_sig(self, msg):

        self.save_graph_to_local("./test.png")
        print("==== START ====\n", msg.get("input", "NO INPUT!"))

        # entry_tool: ready_to_start
        if (entry_tool := self.proxy.game_dynamics.entry_tool):
            print(f"self.proxy.toolize_{entry_tool[0]}", s=1)
            response = await eval(f"self.proxy.toolize_{entry_tool[0]}")({
                "messages": {}
            })
            print(response, s=25)

    async def process(self, msg, *args, **kwargs):
        """
        Process.
        """
        flag = True
        # print(msg, s=27)
        path = Path(__file__).resolve().parents[0] / 'prompts' / 'intro.md'
        with open(path, "r", encoding="utf8") as fp:
            intro = fp.read()

        execute_guide = Path(
            __file__).resolve().parents[0] / 'prompts' / 'execute_guidance.md'
        with open(execute_guide, "r", encoding="utf8") as fp:
            guide = fp.read()

        record_guide = Path(
            __file__).resolve().parents[0] / 'prompts' / 'record_guidance.md'
        with open(record_guide, "r", encoding="utf8") as fp:
            record = fp.read()
        while flag:
            await self.graph.ainvoke(
                self._initialize_state({
                    "rule_description": intro,  # msg["input"],
                    "observation": [msg],
                    "execution_guide": guide,
                    "record_guide": record,
                    "tool_description": {}
                }),
                {"recursion_limit": 100})

    async def start_sig_env(self, *args, **kwargs):
        """
        Start with Env
        """

        _, info = self.env.reset()

        return await self.process(info, *args, **kwargs)
