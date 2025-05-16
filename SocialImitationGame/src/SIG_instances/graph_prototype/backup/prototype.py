from typing import Annotated, TypedDict, Dict, Literal, List
import operator, random, json, re
from jinja2 import Template
from pathlib import Path
from langchain import hub
from langchain_core.agents import AgentAction, AgentFinish, AgentActionMessageLog
from langchain_core.messages import BaseMessage, AIMessage, convert_to_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langgraph.graph import END, StateGraph, add_messages

from ..structured_react import create_structured_react, create_structured_react_v2
from ....SIG_core.base_sig_agent import BaseSIGAgent as BaseSIG
from ....agent_proxy.utils import print, logger


class GraphState(TypedDict):
    """
    shared by all nodes in the graph
    """
    messages: Annotated[list[BaseMessage], add_messages]
    input: str
    username: str
    # game status directly related
    # phase, or say `next`
    next_step: str
    crafting_finish_reason: str
    # 通过 check_event_history 获取
    crafting_target: str
    # maybe blf state
    current_hands: dict
    # blf state
    oppos_hands: Dict[str, Dict]
    oppos_targets: Dict[str, str]

    # state => plan => game interaction => summary/reflection
    planning: str

    # 用于记录turn-based的跟服务器的交互
    turn_based_interaction: Annotated[list[str], operator.add]

    # list of (action, observation) and can be continuous append
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
    # agent_scratchpad
    # "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"])


def translate_current_states(state: GraphState) -> str:
    """
    Translate the current game state into a natural language description for the LLM.
    """
    description = f"""
Current game state:
- Your username: {state['username']}
- Your crafting target: {state['crafting_target']}
- Items in your hand: {', '.join([f"{item}: {amount}" for item, amount in state['current_hands'].items()])}

Opponents' information:
"""
    for opponent, hand in state['oppos_hands'].items():
        description += f"- {opponent}'s items: {', '.join([f'{item}: {amount}' for item, amount in hand.items()])}\n"
        # description += f"  {opponent}'s target: {state['oppos_targets'].get(opponent, 'Unknown')}\n"

    return description.strip()


class GraphAgent(BaseSIG):

    def __init__(self, proxy, *args, **kwargs):
        """
        Initialize
        """
        super().__init__(proxy, *args, **kwargs)
        self.llm = kwargs.get("llm", None)
        self.system_prompt = kwargs.get(
            "system_prompt",
            "You are a skilled and strategic trader living in the world of Minecraft."
        )
        self.react_prompt_temaplte = kwargs.get("react_prompt",
                                                hub.pull("hwchase17/react"))
        if self.llm is None:
            self.llm = AzureChatOpenAI(model="gpt-4o", temperature=0)

        self.full_tool_set = kwargs.get("full_tool_set", [])
        self.prompt_template = kwargs.get("prompt_template")

        if kwargs.get('game_init'):
            with open(kwargs.get('game_init'), 'r') as f:
                self.game_init = Template(f.read())
        else:
            game_init_path = Path(__file__).resolve().parents[
                2] / 'proxied_games' / 'tradeCraft' / 'prompts' / 'game_init.txt'
            with open(game_init_path, 'r') as f:
                self.game_init = Template(f.read())

        self.graph = self._build_graph()

    def _build_graph(self):
        # StateGraph: shared state
        # enabling nodes to communicate and update this shared information during execution.
        workflow = StateGraph(GraphState)
        workflow.add_node('phase_route', self._phase_route)
        # workflow.add_node('waiting_for_opponent', waiting_for_opponent)
        workflow.add_node('make_decision', self._make_decision)
        workflow.add_node('make_proposal', self._make_proposal)
        workflow.add_node('crafting', self._crafting)
        workflow.add_node('crafted_target', self._crafted_target)

        workflow.set_entry_point('phase_route')
        workflow.add_edge('make_decision', 'crafting')
        workflow.add_edge('make_proposal', 'phase_route')
        # workflow.add_edge('waiting_for_opponent', 'phase_route')
        workflow.add_edge('crafted_target', END)

        workflow.add_conditional_edges(
            'phase_route',
            self._phase_condition,
            {
                'make_proposal': 'make_proposal',
                'make_decision': 'make_decision',
                'crafting': 'crafting',
                # 'waiting_for_opponent': 'waiting_for_opponent',
            })
        workflow.add_conditional_edges('crafting', self._crafting_condition, {
            'crafting_done': 'phase_route',
            'crafted_target': 'crafted_target',
        })
        graph = workflow.compile()
        return graph

    def save_graph_to_local(self, file_path: str):
        image_data = self.graph.get_graph().draw_mermaid_png()
        with open(file_path, 'wb') as file:
            file.write(image_data)

    async def main_loop(self, msg):
        flag = True
        print("==== START ====\n", msg.get("input", "NO INPUT!"))

        while flag:
            await self.graph.ainvoke(msg)

    async def _phase_route(self, state: GraphState):

        class Response(BaseModel):
            """Final response to the question being asked"""
            username: str = Field(description="The username of the player")
            next_step: Literal['make_decision', 'make_proposal',
                               'crafting'] = Field(
                                   description="The next phase of the game")
            current_hands: Dict[str, int | str] = Field(
                description="The current hands of the player")
            crafting_target: str = Field(
                description="The target to be crafted")
            oppos_hands: Dict[str, Dict[str, int | str]] = Field(
                description="The hands of the opponents")

        # react = create_structured_react(self.llm, self.full_tool_set, Response)
        react = create_structured_react_v2(self.llm, self.full_tool_set,
                                           Response)
        result = await react.ainvoke(
            input={
                "messages":
                [("human", f"{state['input']}\n"
                  "At now only extract the current game states, which inclues [username, next_step, current_hands, crafting_target, oppos_hands], using the provided tools and their outputs (next_step means what you should do given the current game states, and oppopents can be multiple, so oppos_hands is a dict of hands of all opponents), and do not proceed to the next phase. Note the item name and player name should strictly follow the format of function output."
                  )]
            })
        resp = result['final_response']
        if isinstance(resp, dict):
            return {
                "username": resp['username'],
                "next_step": resp['next_step'],
                "current_hands": resp['current_hands'],
                "crafting_target": resp['crafting_target'],
                "oppos_hands": resp['oppos_hands']
            }
        else:
            return {
                "username": resp.username,
                "next_step": resp.next_step,
                "current_hands": resp.current_hands,
                "crafting_target": resp.crafting_target,
                "oppos_hands": resp.oppos_hands
            }

    def _phase_condition(self, state: GraphState):
        return state['next_step']

    async def _make_decision(self, state: GraphState):
        # pure react agent
        agent = create_react_agent(
            self.llm,
            self.full_tool_set,
            self.react_prompt_temaplte,
            #    stop_sequence=['approval_or_reject']
        )
        agent_executor = AgentExecutor(agent=agent,
                                       tools=self.full_tool_set,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)

        # make_decision can only be executed once.
        resp = await agent_executor.ainvoke(
            {
                "input":
                f"Now the game state is {translate_current_states(state)}.\n You are in the make_decision phase, and you have to make a decision on the proposal from your opponents to progress the game. Once you submit the decision, you must stop and await further instructions."
            }, )

        return {'turn_based_interaction': ['make_decision', resp['output']]}

    async def _make_proposal(self, state: GraphState):
        # pure react agent
        agent = create_react_agent(
            self.llm,
            self.full_tool_set,
            self.react_prompt_temaplte,
            #    stop_sequence=["submit_proposal"]
        )
        agent_executor = AgentExecutor(agent=agent,
                                       tools=self.full_tool_set,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)

        # make_proposal can only be executed once.
        # TODO, game init missing;
        resp = await agent_executor.ainvoke(
            {
                "input":
                f"Now the game state is {translate_current_states(state)}.\nYou are in the make_proposal phase, and you have to make a proposal to your opponents to progress the game. Once you submit the proposal, you must stop and await further instructions."
            }, )
        print(resp, s=25)
        return {'turn_based_interaction': ['make_proposal', resp['output']]}

    async def _crafting(self, state: GraphState):
        agent = create_react_agent(self.llm, self.full_tool_set,
                                   self.react_prompt_temaplte)
        agent_executor = AgentExecutor(agent=agent,
                                       tools=self.full_tool_set,
                                       verbose=True,
                                       return_intermediate_steps=True,
                                       stream_runnable=False)

        class Response(BaseModel):
            """Final response to the question on being asked current game states"""
            crafting_steps: List[dict] = Field(
                description="The current crafting step")
            finish_reason: Literal['crafted_target', 'crafting_done'] = Field(
                description="The reason for finishing the crafting phase")

        resp = await agent_executor.ainvoke(
            {
                "input":
                f"Now the game state is {translate_current_states(state)}"
                f"We are at the **Crafting Phase** of the game. You are about to decide whether / what to craft using your current resources so that you can either **win** or prepare for **next trading**."
                f"Please craft step by step following the Minecraft recipes until you either successfully craft the target item or have prepared adequately for the next trading phase."
                f"When you finished crafting, you should output the `crafting_steps` and `finish_reason`, the schema of the `crafting_steps` and `finish_reason` is as follows: {Response.model_json_schema()}."
            }, )
        # print(resp, s=25)

        # strict=True, model output is guaranteed to exactly match the JSON Schema provided in the tool definition.
        llm_structured_output = self.llm.with_structured_output(Response)
        result = llm_structured_output.invoke(resp['output'])

        return {
            'turn_based_interaction': [result['crafting_steps']],
            'crafting_finish_reason': result['finish_reason']
        }

    def _crafting_condition(self, state: GraphState):
        if state['crafting_finish_reason'] == 'crafted_target':
            return 'crafted_target'
        return 'phase_route'

    def _crafted_target(self, state: GraphState):
        return {'turn_based_interaction': ['crafted_target']}
