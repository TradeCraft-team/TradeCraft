"""
https://arxiv.org/pdf/2409.10038
https://github.com/diagram-of-thought/diagram-of-thought/blob/main/prompts/iterative-reasoner.md
"""

import os
import operator
from typing import Annotated, TypedDict, Dict, Literal, List
from langgraph.graph import END, StateGraph, add_messages
from langchain_core.messages import BaseMessage
from langchain_openai import AzureChatOpenAI

from dotenv import load_dotenv, find_dotenv
assert load_dotenv(find_dotenv(filename='.env', raise_error_if_not_found=True))


model = 'gpt-4o-2024-08-06'

llm = AzureChatOpenAI(
    model=model,
    temperature=0.,
    api_key=os.environ['BIGAI_OAI_API_KEY'],
    api_version=os.environ['BIGAI_API_VERSION'],
    azure_endpoint=f"{os.environ['BIGAI_API_BASE']}/{os.environ['BIGAI_REGION']}",
    streaming=False
)

class GraphState(TypedDict):
    problem_statement: str
    propositions: Annotated[list[str], operator.add]
    summarization: str

def proposer(state: GraphState) -> GraphState:
    p1 = 'proposition by proposer' # may be wrong
    return {'propositions': [p1]}

def critic(state: GraphState) -> GraphState:
    proposition_prime = f"proposition by critic from {state['propositions'][-1]}"
    return {'propositions': [proposition_prime]}

def summizer(state: GraphState) -> GraphState:
    summarization = f"summarization by summizer from {state['propositions'][1:]} and {state['problem_statement']}"
    return {'summarization': summarization}


def should_critic_repeat(state: GraphState):
    should_repeat = False  # Replace with actual logic
    if should_repeat:
        return 'repeat'
    else:
        return 'end'

def should_cycle_repeat(state: GraphState):
    should_repeat = True  # Replace with actual logic
    if should_repeat:
        return 'repeat'
    else:
        return 'end'

workflow = StateGraph(GraphState)
workflow.add_node('proposer', proposer)
workflow.add_node('critic', critic)
workflow.add_node('summizer', summizer)

workflow.add_edge('proposer', 'critic')
workflow.add_edge('critic', 'summizer')

workflow.add_conditional_edges(
    'critic',
    should_critic_repeat,
    {
        'repeat': 'critic',
        'end': 'summizer'
    }
)

workflow.add_conditional_edges(
    'summizer',
    should_cycle_repeat,
    {
        'repeat': 'proposer',
        'end': END
    }
)


workflow.set_entry_point('proposer')

graph = workflow.compile()
image_data = graph.get_graph().draw_mermaid_png()
# print(image_data)
with open('dot2.png', 'wb') as file:
    file.write(image_data)
