"""
"""
import asyncio
from jinja2 import Template
from pathlib import Path
from langchain.tools.render import render_text_description
from ...SIG_core import BaseSIGAgent, GymSIGAgent
from ...agent_proxy.utils import print, logger

# from langchain.tools.base import BaseTool


class MechanicalTurk(GymSIGAgent):
    """
    Real Mechanical Turk, meaning, you must type instead of using Language Models!!!

    Purely human-in-the-loop, used for testing Proxy / Translations~
    """

    def __init__(self, proxy, *args, **kwargs):
        """
        Initialize
        """
        super().__init__(proxy, *args, **kwargs)
        self.llm = kwargs.get("llm", None)
        # "full_tool_set" is a requested arg. For MTurk is tool-driven.
        self.full_tool_set = dict(
            (t.name, t) for t in kwargs.get("full_tool_set"))
        self.prompt_template = kwargs.get("prompt_template")

        if kwargs.get('game_init'):
            with open(kwargs.get('game_init'), 'r') as f:
                self.game_init = Template(f.read())
        else:
            game_init_path = Path(__file__).resolve().parents[
                2] / 'proxied_games' / 'tradeCraft' / 'prompts' / 'game_init.txt'
            with open(game_init_path, 'r') as f:
                self.game_init = Template(f.read())

        # self.agent = create_react_agent(self.llm, self.full_tool_set, self.prompt_template)
        # self.agent_executor = AgentExecutor(agent=self.agent,
        #                                     tools=self.full_tool_set,
        #                                     verbose=True,
        #                                     stream_runnable=False)

    async def main_loop(self, msg, *args, **kwargs):
        print("==== START ====\n",
              msg.get("input", {}).get("translated", "NO INPUT!"))
        flag = True
        # print(self.full_tool_set, s=1)
        while flag:
            try:

                print(render_text_description(self.full_tool_set.values()),
                      sep="",
                      s=23)
                print(
                    f"your name: {self.proxy.fsm.username}, input format: tool_name(tool_args):",
                    s=3)

                answer = input().strip()
                tool_name_len = answer.find("(")

                if tool_name_len < 1 or answer[-1] != ")":
                    raise
                tool_name = answer[:tool_name_len]
                args = answer[tool_name_len + 1:-1]

                t_input = eval(args)

                response = await self.full_tool_set[tool_name].ainvoke(
                    {"messages": t_input})

                print(response, sep="", s=25)
            except Exception as e:
                print("An exception is raised.", sep="", s=1)
                logger.exception(e)
                response = "Incorrect Toolname"
