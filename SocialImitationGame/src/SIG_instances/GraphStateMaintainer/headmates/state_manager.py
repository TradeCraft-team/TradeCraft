"""
State Manager
"""
import asyncio
import random
import jinja2
from typing import List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from ..state import MentalState
from ....agent_proxy.utils import print, logger


class BaseResponse(BaseModel):
    """
    Base Response to Other Headmates
    """
    thoughts: List[str] = Field(
        description=
        "The thoughts before real outputs, helps you improve output quality.")


class StateManager:
    """
    Base class for state maintainer model
    """

    system_prompt_ = ""

    member_template_ = """## Team Description:\nYour team is star-shaped, there are {{role_cls|length}} agents, all connected to the central member called **Coordinator**, and all actions and observations are through another one called **Executor**. NO member has private memory, they can only see and remember what is written in a shared "State".
Members and their functions / duties are:
{% for k, v in role_cls.items() %}
- {{k}}: {{v.__doc__.strip()}}
{% endfor %}\n\n"""

    analysis_template_ = """## Analysis\n{{state["analysis"]}}\n"""
    evaluation_template_ = """## Evaluation\nThe coordinator evaluated the current state and responds:\n{{state["evaluation"]}}\n"""
    improvement_template_ = """## Improvement\nThe coordinator thinks the following improvement could be made:\n{{state["improvement"]}}\n"""
    instruction_template_ = """## Current Instruction\nHere is the suggested task from the coordinator, please follow it together with your role-job to act: {{state["instruction"]}}"""

    rule_description_template_ = """## Introduction of **team task**\n{{state["rule_description"]}}\n"""

    goal_template_ = """In the specific team task, the goal is {{state["goal"]}}\n"""

    plan_template_ = """{% if state["far_plan"]|length %}## Plan made by planner:\n- Far plan:\n{{state["far_plan"][-1]}}\n- Near plan:\n{{state["near_plan"]}}\n{% endif %}"""

    observation_template_ = """## Raw observations in receiving order\n{% for x in state["observation"] %}{{x}}\n{% endfor %}\n"""
    # refined_observation_template_ = """# Summarized observation\n{% for x in state["refined_observation"] %}{{x}}\n{% endfor %}\n"""
    refined_observation_template_ = """## Summarized observation\n{{state["refined_observation"]}}\n"""
    work_log_template_ = """## Work log\n{% for item in state["work_log"][-10:] %}\n- *Member* {{item[0]}} has done: {% for work in item[1:] %}{{work}}{% endfor %}\n{% endfor %}\n"""

    tool_description_template_ = "\n## Tools:\n{{state[\"tool_description\"]}}\n"
    pydantic_formatting_template_ = """## Response Format\nYour response should be in the following format:\n{{format}}"""

    meta_template_ = {""}

    def __init__(self, **kwargs):
        """
        Initialize
        """
        self.role_cls = kwargs.get("role_cls")
        self.dummy = kwargs.get("dummy", False)
        self.llm = None if self.dummy else kwargs.get("llm")
        self.cnt = 0
        self.response_cls = BaseResponse
        self.parsing_template = jinja2.Template("Default template.")

    def gen_prompt(self, state: MentalState, **kwargs) -> List[tuple]:
        """
        """
        return [("system", self.system_prompt_),
                ("human", self.parsing_template.render(state=state, **kwargs))]

    async def node_callback(self, state: MentalState):
        """Main entry, as langgraph node callback"""
        prompt = ChatPromptTemplate(self.gen_prompt(state,
                                                    role_cls=self.role_cls),
                                    template_format="jinja2")

        print("=" * 24, "PROMPT", "=" * 24 + "\n", prompt, s=24)
        if self.dummy:
            output = self.dummy_process(prompt, state)
        else:
            flow = prompt | self.llm.with_structured_output(self.response_cls)
            output = await flow.ainvoke({"state": state})

        ret = self.state_updating(output)
        print("=" * 24, "OUTPUT", "=" * 24 + "\n", ret, s=26)
        return ret

    def state_updating(self, output: BaseResponse, **kwargs):
        """Update states using the Mental state rules."""
        self.cnt += 1
        return {
            "errors": [f"{self.__class__} {self.cnt+1}"],
            "next_agent": self.next_agent_ if self.dummy else "coordinator"
        }

    async def process(self, prompt: str) -> str:
        pass
        return ""

    def next_agent(self, state: MentalState, **kwargs):
        """If work as a conditional node, this tells where to go."""
        print(state.get("next_agent"), s=3)
        return state.get("next_agent")

    def dummy_process(self, prompt: ChatPromptTemplate, state: MentalState):
        """
        """
        self.next_agent_ = "game_over"  # random.choice(list(self.role_cls.keys()))
        return str(self.__class__) + str(self.__doc__) + "\n\n"
