"""
Executor headamte
"""
import asyncio
import jinja2
import json
import re
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools.render import ToolsRenderer, render_text_description
# from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
# from trustcall import create_extractor

from .state_manager import StateManager, BaseResponse, Field
from ..state import MentalState
from ....agent_proxy.utils import print, logger


class Response(BaseResponse):
    """Final response to the question being asked"""
    tool_name: str = Field(description="The name of tool you want to use")
    kwargs: dict = Field(
        description="The corresponding argument into the tool.")
    tool_description: Dict[str, str] = Field(
        description=
        "Brief intro to each tool, of format`{tool_name: description}`")
    work_log: str = Field(
        description="Very brief summary of what you have done.")


class DescriptionResponse(BaseResponse):
    """Final response to the question being asked"""
    tool_description: Dict[str, str] = Field(
        description=
        "Brief intro to each tool, of format`{tool_name: description}`")
    work_log: str = Field(
        description="Very brief summary of what you have done.")


def render_text_description(functions: list):
    ret = ""
    for f in functions:
        ret += f"### Tool name: `{f.name}`\n```{f.description}```\n\n"
    return ret


class Executor(StateManager):
    """
    The only agent who can interact with environment, via calling `tools` with
    correct arguments following instruction and plan. Accepts **very concrete
    instructions** about what to do, such as calling some specific tool with some input.
    """
    tool_template_ = "\n# Tools:\n{{tools}}\n"

    system_prompt_ = """You are the Executing agent in a team. You are the only one in your team
who can interact with environment via tools. Your output should be formatted as a **JSON object**.

# Instructions
    1. Accroding to the task, generate some thoughts which may help you work better.
    2. If you find part of some desciption is wrong, output correct description
       in **tool_description** field.
    3. Choose a tool to call, write the name in **tool_name** field. Tool name must be one item in [{{tool_names}}]!
    4. Write the input kwargs corresponding to the tool you choose above, with *correct format*, into **kwargs** field. Check *Args* of tool descriptions in the [Tools] section.
    5. Before stopping, you may summarize briefly what you have done into **work_log** field.

    """

    describe_prompt_ = """
You are the Executing agent in a team. You are the only one in your team
who can interact with environment via tools. Your output should be formatted as a **JSON object**.
# Instructions
    1. Accroding to the task, generate some **thoughts** which may help you work better.
    2. Since there is no tool descriptions, output description of each tool
       in **tool_description** field as an {item name: description} dictionary.
    3. Before stopping, you may summarize briefly what you have done into **work_log** field.

## Tools:
{{tools}}

    Please follow the instructions above."""

    react_prompt_ = """Answer the following questions as best you can. You have access to the following tools:
{tools}

Use the following format:

- Question: the input question you must answer
- Thought: you should always think about what to do
- Action: the action to take, should be one of [{tool_names}]
- Action Input: the input to the action
- Observation: the result of the action

Begin!

Question: {input}

Thought:{agent_scratchpad}"""

    def __init__(self, tools: list = [], **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.tools = tools
        self.tool_dict = dict((t.name, t) for t in tools)

        self.response_cls = Response

        self.parsing_template_ = (
            self.member_template_ + self.rule_description_template_ +
            self.observation_template_ + self.analysis_template_ +
            # self.refined_observation_template_ +
            self.plan_template_ + self.instruction_template_ +
            # self.improvement_template_ +
            self.tool_template_ + self.pydantic_formatting_template_)

        self.parsing_template = jinja2.Template(self.parsing_template_)

    def state_updating(self, output, state: MentalState, **kwargs):
        """
        """
        tools = state["tool_description"]
        # tools.update(output.tool_description)
        # observation = [""] if isinstance(output, DescriptionResponse) else [output.observation]

        # pure llm, not strictly structured
        print(output.content, s=20)
        find_result = re.findall(R"\{.*\}", output.content, re.DOTALL)
        print(find_result, s=22)
        output_json = json.loads(find_result[0])

        observation = [""]
        if len(state["tool_description"]) > 0:
            observation = output_json["observation"]

        tools.update(output_json["tool_description"])
        work_log = output_json["work_log"]

        return {
            "observation": observation,
            "tool_desciption": tools,
            "work_log": [("executor", work_log)]
        }

    async def node_callback(self, state: MentalState):
        """
        Main entry, as langgraph node callback
        [TODO] How to really call a tool? Especially when Pydantic is not good to use.
        """

        if self.dummy:
            return await super().node_callback(state)

        if len(state["tool_description"]) == 0:
            description = await self.describe_tools(state)
            return description

        prompt = ChatPromptTemplate(self.gen_prompt(state,
                                                    role_cls=self.role_cls),
                                    template_format="jinja2")

        # # React & AgentExecutor:
        # parser = PydanticOutputParser(pydantic_object=Response)
        # # Create the agent
        # tools = self.full_tool_set
        # agent = create_react_agent(llm=self.llm,
        #                            tools=tools,
        #                            prompt=self.react_prompt_temaplte)
        # agent_executor = AgentExecutor(agent=agent,
        #                                tools=tools,
        #                                stream_runnable=False,
        #                                handle_parsing_errors=True)
        # # Create the chain
        # chain = ({
        #     "game_input":
        #     RunnablePassthrough(),
        #     "format_instructions":
        #     lambda _: parser.get_format_instructions()
        # }
        #          | prompt
        #          | (lambda x: {
        #              'input': x.text
        #          })
        #          | agent_executor)

        # # Invoke the chain
        # resp = await chain.ainvoke(game_input)
        # return ret

        # Direct call tools.
        self.tool_raw = render_text_description(self.tools)
        self.llm.bind_tools(self.tools)
        parser = PydanticOutputParser(pydantic_object=Response)
        prompt_ = self.gen_prompt(state,
                                  role_cls=self.role_cls,
                                  tools=self.tool_raw,
                                  format=parser.get_format_instructions())
        cnt = 5
        ret = {}
        while (cnt := cnt - 1) > 0:
            prompt = ChatPromptTemplate(prompt_, template_format="jinja2")
            print("=" * 24, "PROMPT", "=" * 24 + "\n", prompt, s=24)
            try:
                flow = prompt | self.llm.with_structured_output(
                    self.response_cls)
                output = await flow.ainvoke({
                    "state":
                    state,
                    "tools":
                    self.tool_raw,
                    "tool_names":
                    ", ".join(self.tool_dict)
                })
                tool_name = output.tool_name
                kwargs = output.kwargs
                obs = await self.tool_dict[tool_name].ainvoke(input=kwargs)
                td = state["tool_description"]
                td.update(output.tool_description)
                ret = {
                    "observation": [obs],
                    "work_log": [("executor", output.work_log)],
                    "tool_description": td
                }
                print("=" * 24, "OUTPUT", "=" * 24 + "\n", ret, s=26)
                return ret

            except Exception as e:
                print(e, f"{cnt} trials left here.", s=1)
                prompt_ += [
                    ("human",
                     f"Last trial results in Error {e}, please correct.")
                ]
        return ret

    async def describe_tools(self, state: MentalState):
        """
        """
        tools = render_text_description(self.tools)

        prompt = ChatPromptTemplate([("system", ""),
                                     ("human", self.describe_prompt_)],
                                    template_format="jinja2")
        print("=" * 24, "PROMPT", "=" * 24 + "\n", prompt, s=24)
        flow = prompt | self.llm  # self.llm.with_structured_output(DescriptionResponse)

        cnt = 5
        while (cnt := cnt - 1) > 0:
            output = await flow.ainvoke({"tools": tools})
            try:
                ret = self.state_updating(output, state=state)
                print("=" * 24, "OUTPUT", "=" * 24 + "\n", ret, s=26)
                return ret
            except Exception as e:
                print(e, f"{cnt} trials left here.", s=1)
