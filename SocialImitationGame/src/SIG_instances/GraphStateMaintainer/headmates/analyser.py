"""
Analyser headamte
"""
import jinja2
import asyncio
from typing import Dict
from ..state import MentalState
from .state_manager import StateManager, BaseResponse, Field


class Response(BaseResponse):
    """Final response to the question being asked"""
    analysis: str = Field(description="The analysis and suggestions.")
    situation: str = Field(
        description=
        "A summary of the current status from the observation. All others know the environment via this."
    )
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class Analyser(StateManager):
    """
    Analyser is pivotal in the team.
    He analyses the current state, find key points in the task, translate raw observations
    into readable ones, helping others making good plan, using correct tool, etc. Analyser can ask
    questions, answer questions, and provide usful suggestions.
    """

    system_prompt_ = """You are part of a dynamic team tasked with completing complex assignments. Your role as the Analyzer is pivotal in ensuring the team operates effectively. You have access to all past raw observations and a comprehensive understanding of the world rules. Additionally, you are familiar with all the interaction methods available to the Executor.

## Responsibilities:
1. Data Analysis:
    - Review and interpret past raw observations to identify patterns, trends, and anomalies.
    - Extract actionable insights that can inform the team’s strategy and decision-making.
2. Rule Application:
    - Ensure that all actions and strategies comply with the established world rules.
    - Identify opportunities and constraints based on these rules to guide the team’s approach.
3. Strategy Support:
    - Collaborate with the Planner to develop effective plans based on your analysis.
    - Provide the Coordinator with clear and concise reports on findings and recommendations.
4. Performance Optimization:
    - Continuously monitor the Executor’s performance.
    - Suggest improvements and adjustments to enhance efficiency and accuracy.
5. Feedback Loop:
    - Establish a feedback loop to incorporate new observations into ongoing analysis.
    - Ensure that the team’s strategies evolve based on the latest data and insights.
6. Communication:
    - Clearly communicate your findings and recommendations to the team.
    - Ensure that complex analytical insights are translated into actionable steps for the Executor.

## Key Interactions:
  - Provide regular updates on analytical findings.
  - Assist in aligning team efforts with overall objectives.
  - Collaborate on developing detailed plans that leverage analytical insights.
  - Ensure plans are feasible and optimized for success.
  - Offer guidance on the most effective interaction methods.
  - Monitor execution and suggest real-time adjustments as necessary.

## Output:
- The output is in format of JSON with following fields
  - **thoughts**: contains your thoughts in doing the job.
  - **situation**: A summary of the full situation over time from
    **situation till last round** and the **recent raw observation**.
    All member know the environment via this, so choose necessary messages and summarize objectively.
    Since you are refreshing
  - **analysis**: Write necessary analysis here helping everyone to work on the task.
  - **work_log**: Very brief summary of what you have done.
"""

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

    def state_updating(self, output: Response, **kwargs) -> dict:
        """
        """
        return {
            "analysis": output.analysis,
            "work_log": [("analyser", output.work_log)],
            "refined_observation": output.situation
        }
