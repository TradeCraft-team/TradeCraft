"""
Planner headamte
"""
import asyncio
import jinja2
from typing import Dict
from .state_manager import StateManager, BaseResponse, Field
from ..state import MentalState


class Response(BaseResponse):
    """Final response to the question being asked"""
    far_plan: str = Field(
        description=
        "A far plan of what to do and what could happen till accomplishing the task."
    )
    near_plan: str = Field(
        description="A near plan as a concrete guidance of next action.")
    work_log: str = Field(
        description="Very brief summary of what you have done.")
    # improvement: str = Field(description="What in the state can be improved and to which direction.")


class Planner(StateManager):
    """
    Planner provides a full plan from now on, trying to predict and to plan as far as possible with
    intermediate details. Planner can generate new plans when you ask.
    """

    system_prompt_ = """You are a planning agent in a team. You have access to all past observations and a comprehensive understanding of the world's rules, together with analysis and suggestions from your other teammates.
    Your duty is to generate two compatible plans which helps the team to act:
    - The far plan: it should contain the steps reaching the final goal of the task, while you have to do some reasonable prediction of the future situation.
    - The near plan: it should be very concrete, containing enough details of the next action and the reason of taking that action. Usually the near plan contains only one action and should be compatible with the begining part of the far plan.

    While planning, you can see the last version of plans and should aim to correct or improve it, ensuring the new plan better fitting the description above.
    You should write a JSON, first the **thoughts** field about your thoughts, then **far_plan** field for your far plan, **near_plan** field for near plan, finally you should write in **work_log** field briefly what you have done. If you find it hard to plan directly, you may write in your **near_plan** which teammate and how he could assist you."""
    plan_template_ = """{% if state["far_plan"]|length %}# The plans you made last time:\nFar plan: {{state["far_plan"][-1]}}\nNear plan:{{state["near_plan"]}}\n{% endif %}"""

    def __init__(self, **kwargs):
        """Initialize"""
        super().__init__(**kwargs)
        self.response_cls = Response

        self.parsing_template_ = (
            self.member_template_ + self.rule_description_template_ +
            # self.refined_observation_template_ +
            self.observation_template_ + self.analysis_template_ +
            self.work_log_template_ + self.plan_template_ +
            self.evaluation_template_ + self.improvement_template_ +
            self.instruction_template_ + self.tool_description_template_)

        self.parsing_template = jinja2.Template(self.parsing_template_)

    def state_updating(self, output: Response):
        """
        """
        return {
            "near_plan": [output.near_plan],
            "far_plan": [output.far_plan],
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
