"""
Router Class: Basic, necessary headmate in GSM
"""
import asyncio
import jinja2
from typing import Dict, List
from .state_manager import StateManager, BaseResponse, Field
from ..state import MentalState
from .executor import Executor
from ....agent_proxy.utils import print, logger


class Response(BaseResponse):
    """Final response to the question being asked"""
    instruction: str = Field(description="Tells the next agent what to do.")
    act_or_not: bool = Field(
        description=
        "Tells to act or not, if act, call executor, otherwise assign one.")
    next_agent: str = Field(
        description="Name of agent who will follow you **instruction** to work"
    )
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class Coordinator(StateManager):
    """
    Coordinator is the center of the team. After your teamates' finishing a job,
    the coordinator is informed and evaluate the whole state immediately, then decding
    which member will be called and what job should be done to proceed.
    """

    system_prompt_ = """You are the Coordinating agent in a team. 
    You should clearly tell the next agent what to do with instructions. 
    
    Focus on the "plan" field, which is the near plan as a concrete guidance of next action:
    (1) If handcraft changed, you should call the recorder to record it.
    (1) If planner has made a plan, you should call the executor to execute it. If their isn't a plan for current state, you should ask the planner to make one. You should also check worklog to see the plan has been executed or not.
    (3) If the executor couldn't execute the plan, you should ask the planner to modify it or make a new one. 
    (4) If the current observation has been changed, you should call the **recorder** to preserve the current state.
    (5) After that, you can call the planner to make a new plan for new state.
    Your output should be formatted as a **JSON object**.

Follow these steps to perform your task:

1. Write your thoughts to **thoughts** field. This is a scratchpad helping you be more reasonable.
2. Decide whether to execute the current plan or make a new one and indicate your decision in the **act_or_not** field.
3. If you decide to call the executor to carry out the action or call the planner to make a new plan, recording these in the **next_agent** and **instruction** fields respectively. 
If you find in observations that task is already finished or failed, please write "game_over" into **next_agent** to stop. You may call any other member as long as need, despite they are just called, e.g., if you find the executor did not follow what you ask him to do, you may insist the task in instruction and call him again.

"""

    def __init__(self, **kwargs):
        """Initialize"""
        super().__init__(**kwargs)
        self.response_cls = Response
        self.parsing_template_ = (
            self.member_template_ + 
            self.rule_description_template_ +
            self.observation_template_ + 
            self.current_state_template_ + 
            self.current_observation_template_ + 
            self.plan_template_ + 
            self.work_log_template_)

        self.parsing_template = jinja2.Template(self.parsing_template_)

    def gen_prompt(self, state: MentalState, **kwargs) -> List[tuple]:
        """
        """
        # print the keys in state
        return [("system", self.system_prompt_),
                ("human",
                 self.parsing_template.render(
                     state=state,
                     role_cls=self.role_cls,
                 ))]

    def state_updating(self, output: Response, **kwargs) -> dict:
        """
        """
        if output.act_or_not:
            next_agent = "executor"
        else:
            next_agent = output.next_agent
            if next_agent not in self.role_cls:
                print("Coordinator outputs an invalid `next_agent`:",
                      next_agent,
                      s=1)
        return {
            "instruction": output.instruction,
            "next_agent": next_agent,
            "work_log": [("coordinator", output.work_log)]
        }
