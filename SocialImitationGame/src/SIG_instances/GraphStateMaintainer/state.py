"""
Defines the state. Key part of the `StateMaintainer` instance.
"""
import operator
from typing import Annotated, TypedDict, Dict, Literal, List
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class TaskItem(TypedDict):
    key: str
    item_index: int
    task: str
    status: str


class MentalState(TypedDict):
    """
    Mental state of the agent. May store necessary things in long-short term memory
    and may roughly follow the BDI structure.
    """
    evaluation: str
    improvement: str
    instruction: str
    analysis: str
    # necessary self identity information. In tradeCraft, may be self username.
    identity_info: Dict  # ?

    # The task description and background information
    rule_description: str

    # The goal of the task
    goal: str

    # A list of planned actions to achieve the goal
    far_plan: Annotated[List[str], operator.add]
    near_plan: Annotated[List[str], operator.add]
    # The index of the current step in the plan

    observation: Annotated[List[str], operator.add]
    refined_observation: str  # Annotated[List[str], operator.add]

    work_log: Annotated[List[List[str]], operator.add]

    thoughts: List[str]

    tool_description: Dict[str, str]

    errors: Annotated[List[str], operator.add]

    act_or_not: str
    next_agent: str
