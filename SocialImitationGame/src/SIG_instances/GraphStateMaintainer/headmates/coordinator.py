"""
Router Class: Basic, necessary headmate in GSM
"""
import asyncio
import jinja2
from typing import Dict, List
from .state_manager import StateManager, BaseResponse, Field
from ..state import MentalState
from .executor import Executor


class Response(BaseResponse):
    """Final response to the question being asked"""
    evaluation: str = Field(
        description=
        "How the state looks like, which part is good and which part is not so good."
    )
    # improvement: str = field(
    #     description="what in the state can be improved and to which direction."
    # )

    instruction: str = Field(description="Tells the next agent what to do.")
    # act_or_not: bool = Field(
    #     description=
    #     "Tells to act or not, if act, call executor, otherwise assign one.")
    next_agent: str = Field(
        description="Name of agent who will follow you **instruction** to work"
    )
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class Coordinator(StateManager):
    """
    Coordinator is the center of the team. After any other member's finishing a job,
    the coordinator is informed and evaluate the whole task immediately, then deciding
    which member will be called and what job should be done to proceed.
    """

    system_prompt_ = """
# Role Settings
- Role: coordinator
- Your job: lead a team to work on a task. YOUR PART is: repeatedly assign to whom concretely what to do next conceretely. Everyone else reports to you.
- Input: A JSON state recording both your team info and task status is maintained for coorperation, provided in Markdown format.
    ```markdown
    # Input
    ## Team Description
    [Immutable] Introduction to all members.
    ## Introduction to Team tasks
    [Immutable] Environment information, goal, rules to follow.
    ## Observation
    [Accumulative] All messages from server, **from earliest to latest**.
    ## Analysis
    [By Analyser] Latest analysis edited by analyser.
    ## Plan
    [By Planner] Contains **far plan** showing far tendency / strategy, and **near plan** for concrete actions to take next.
    ## Work Log
    [Accumulative] Each member summarize their work after work.
    ## Evaluation
    [By Coordinator] Evaluation of the full state except the last member's change.
    ## Instruction
    [By Coordinator] The concrete instruction by coordinator to the member just worked.
    ## Tool Description
    [Immutable] Summarized by Executor, describing how to communicate with the environment.
    ```

- Output: a JSON object about *your thought* and *how to update the state*. As coordinator, your output should be like:
    ```json
    {
    "thoughts": "A scratchpad helping you be more reasonable. Write the logic of thoughts leading to decision.",
    "evaluation": "How is each part look like, which part needs an update, where is possibly wrong, which looks good, etc.",
    "next_agent": "Among other members, which should work next?"
    "instruction": "What should the next member do? Write precisely and concretely.",
    "work_log": "Briefly say what you have done in this round."
    }
    ```
"""
    """
    Follow these steps to perform your task:

1. Write your thoughts to **thoughts** field. This is a scratchpad helping you be more reasonable.
2. Evaluate the quality of the other agent's output, and record your assessment in the **evaluation** field.
3. Identify possible directions for improvement, and document them in the **improvement** field.
4. Decide whether the current state is adequate for a one-step action, and indicate your decision in the **act_or_not** field. To make the team efficient, after about 7 rounds of thinking, an action should be executed.
5. If you decide to act, call the executor to carry out the action. If not, specify a suitable agent and provide brief instructions for improvement, recording these in the **next_agent** and **instruction** fields respectively. If you find in observations that task is already finished or failed, please write "game_over" into **next_agent** to stop. You may call any other member as long as need, despite they are just called, e.g., if you find the executor did not follow what you ask him to do, you may insist the task in instruction and call him again.

Refer to the list of available collaborators below to determine which agents you can call upon.
"""

    def __init__(self, **kwargs):
        """Initialize"""
        super().__init__(**kwargs)
        self.response_cls = Response
        self.parsing_template_ = (
            self.member_template_ + self.rule_description_template_ +
            # self.refined_observation_template_ +
            self.observation_template_ + self.analysis_template_ +
            self.plan_template_ + self.work_log_template_ +
            self.evaluation_template_ +  # self.improvement_template_ +
            self.instruction_template_ + self.tool_description_template_)

        self.parsing_template = jinja2.Template(self.parsing_template_)

    def gen_prompt(self, state: MentalState, **kwargs) -> List[tuple]:
        """
        """
        return [("system", self.system_prompt_),
                ("human",
                 self.parsing_template.render(
                     state=state,
                     role_cls=self.role_cls,
                 ))]

    def state_updating(self, output: Response, **kwargs) -> dict:
        """
        """
        if False:  # output.act_or_not:
            next_agent = "executor"
        else:
            next_agent = output.next_agent
            if next_agent not in self.role_cls:
                print("Coordinator outputs an invalid `next_agent`:",
                      next_agent,
                      s=1)
        return {
            "instruction": output.instruction,
            "evaluation": output.evaluation,
            # "improvement": output.improvement,
            "next_agent": next_agent,
            "work_log": [("coordinator", output.work_log)]
        }
