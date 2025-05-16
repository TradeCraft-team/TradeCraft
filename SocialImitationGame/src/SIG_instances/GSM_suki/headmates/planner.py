"""
Planner headamte
"""
import asyncio
import jinja2
from typing import Dict
from .state_manager import StateManager, BaseResponse, Field
from ..state import MentalState
from ....agent_proxy.utils import print, logger


class Response(BaseResponse):
    """Final response to the question being asked"""
    plan: str = Field(
        description="A near plan as a concrete guidance of next action.")
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class Planner(StateManager):
    """
    Planner provides plans, trying to predict and to plan with
    intermediate details. Planner can generate new plans when you ask.
    """

    system_prompt_ = """You are a planning agent in a team. You have access to all past observations and a comprehensive understanding of the world's rules, together with analysis and suggestions from your other teammates.
    Your duty is to generate plans which helps the team to act:
    
    While planning, you can see the last version of plans and should aim to correct or improve it, ensuring the new plan better fitting the description above.
    It should contain only one action and should be compatible with the begining part of the plan.
    Attention! You should always consider which phase the game is currently in and make plan that obey the game procedure.
    Attention! A phase_error means the plan you made couldn't be done in the current phase, try to fix it considering the game procedure in rule description field. 

    You should write a JSON, first the **thoughts** field about your thoughts, **plan** field for near plan, finally you should write in **work_log** field briefly what you have done. If you find it hard to plan directly, you may write in your **plan** which teammate and how he could assist you."""
    plan_template_ = """{% if state["plan"]|length %}# The plans you made last time:\n Plan:{{state["plan"]}}\n{% endif %}"""

    def __init__(self, **kwargs):
        """Initialize"""
        super().__init__(**kwargs)
        self.response_cls = Response
        self.parsing_template_ = (self.rule_description_template_ +
                                  self.tool_description_template_+
                                #   self.observation_template_ +
                                  self.current_observation_template_ +
                                  self.current_state_template_ +
                                  self.work_log_template_ +
                                  self.plan_template_ +
                                  self.instruction_template_
                                  )
        self.parsing_template = jinja2.Template(self.parsing_template_)

    def state_updating(self, output: Response):
        """
        """
        return {
            "plan": output.plan,
            "work_log": [("planner", output.work_log)]
        }


"""
member
rule-description
observation
analysis
work log
plan
evaluation
improvement
instruction
tool-description
"""
