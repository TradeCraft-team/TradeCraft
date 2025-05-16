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

def proposer(state: GraphState) -> GraphState:
    # by llm
    p1 = 'proposition by proposer' # may be wrong
    return state['propositions'].append(p1)

def critic_1(state: GraphState) -> GraphState:
    p1_prime = f'proposition refined by critic from {state["propositions"][-1]}'
    return state['propositions'].append(p1_prime)

def critic_2(state: GraphState) -> GraphState:
    p1_prime_verified = f'proposition verified by critic from {state["propositions"][-1]}'
    return state['propositions'].append(p1_prime_verified)

def final_proposer(state: GraphState) -> GraphState:
    p3 = f'proposition verified by final proposer from {state["propositions"][-1]} and {state["problem_statement"]}'
    return state['propositions'].append(p3)

def critic_3(state: GraphState) -> GraphState:
    p3_verified = f'proposition verified by critic from {state["propositions"][-1]}'
    return state['propositions'].append(p3_verified)

def summarizer(state: GraphState) -> GraphState:
    summary = f'summary of propositions: {state["propositions"][-1]} and {state["propositions"][-2]} and {state["problem_statement"]}'
    return state['propositions'].append(summary)

workflow = StateGraph(GraphState)
workflow.add_node('proposer', proposer)
workflow.add_node('critic_1', critic_1)
workflow.add_node('critic_2', critic_2)
workflow.add_node('final_proposer', final_proposer)
workflow.add_node('critic_3', critic_3)
workflow.add_node('summarizer', summarizer)

workflow.add_edge('proposer', 'critic_1')
workflow.add_edge('critic_1', 'critic_2')
workflow.add_edge('critic_2', 'final_proposer')
workflow.add_edge('final_proposer', 'critic_3')
workflow.add_edge('critic_3', 'summarizer')

workflow.set_entry_point('proposer')
workflow.add_edge('summarizer', END)

graph = workflow.compile()

image_data = graph.get_graph().draw_mermaid_png()
with open('dot.png', 'wb') as file:
    file.write(image_data)

