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
    current_state: str = Field(
        description="Game state that you are told to record.")
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class Recorder(StateManager):
    """
    Recorder will decide what state are extreamly important to consider for the game and record it.
    """

    system_prompt_ = """
    You are a recording agent in a team, you have access to the current observation. Your duty is to record the current game state:
    Follow the record guidance and record important game state according to it.

    For your recording process, here are some tips that might help:
    1. You should follow the record guidance to record the current state.
    2. You should consider the current observation and the current state of the game, if the current observation shows that the state you've recorded has been changed, you should record the new state. Otherwise, you should keep the state you've recorded.
    
    You should write a JSON, 
    first the **thoughts** field about your thoughts,
    **current_state** field for the record you want to make(if you decide not to change the current state, just write the original one here), 
    finally you should write in **work_log** field briefly what you have done. 
    """
    current_state_template_ = """{% if state["current_state"]|length %}# The current state you recorded last time is:\n Current_State:{{state["current_state"]}}\n{% endif %}"""
    current_observation_template_ = """#Now the current observation has been changed to: \n{{state["current_observation"]}}\n"""

    def __init__(self, **kwargs):
        """Initialize"""
        super().__init__(**kwargs)
        self.response_cls = Response

        self.parsing_template_ = (self.record_guidance_template_ +
                                  self.current_state_template_ +
                                  self.current_observation_template_ 
                                #   self.work_log_template_
                                )

        self.parsing_template = jinja2.Template(self.parsing_template_)

    def state_updating(self, output: Response):
        """
        """
        return {
            "current_state": output.current_state,
            "work_log": [("recorder", output.work_log)]
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
