import json
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from langchain_openai import ChatOpenAI
from langchain_core.agents import AgentActionMessageLog, AgentFinish
from trustcall import create_extractor

def react_parse(output):
    # https://python.langchain.com/v0.1/docs/modules/agents/how_to/agent_structured/
    # If no function was invoked, return to user
    if "function_call" not in output.additional_kwargs:
        return AgentFinish(return_values={"output": output.content}, log=output.content)

    # Parse out the function call
    function_call = output.additional_kwargs["function_call"]
    name = function_call["name"]
    inputs = json.loads(function_call["arguments"])

    # If the Response function was invoked, return to the user with the function inputs
    if name == "Response":
        return AgentFinish(return_values=inputs, log=str(function_call))
    # Otherwise, return an agent action
    else:
        return AgentActionMessageLog(
            tool=name, tool_input=inputs, log="", message_log=[output]
        )

def create_structured_react(model, tools, response_model):
    # https://langchain-ai.github.io/langgraph/how-tos/react-agent-structured-output/
    # Inherit 'messages' key from MessagesState, which is a list of chat messages 
    class AgentState(MessagesState):
        # Final structured response from the agent
        final_response: response_model

    # Force the model to use tools by passing tool_choice="any"
    # FIXME: tool_choice="any" is not supported by Azure OpenAI
    tools = tools + [response_model]
    model_with_response_tool = model.bind_tools(tools, tool_choice="auto")

    # Define the function that calls the model
    def call_model(state: AgentState):
        response = model_with_response_tool.invoke(state['messages'])
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    # Define the function that responds to the user
    def respond(state: AgentState):
        # Construct the final answer from the arguments of the last tool call
        response = response_model(**state['messages'][-1].tool_calls[0]['args'])
        # We return the final answer
        return {"final_response": response}

    # Define the function that determines whether to continue or not
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is only one tool call and it is the response tool call we respond to the user
        if len(last_message.tool_calls) == 1 and last_message.tool_calls[0]['name'] == response_model.__name__:
            return "respond"
        # Otherwise we will use the tool node again
        else:
            return "continue"

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("respond", respond)
    workflow.add_node("tools", ToolNode(tools))

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "respond": "respond",
        },
    )

    workflow.add_edge("tools", "agent")
    workflow.add_edge("respond", END)
    return workflow.compile()


def create_structured_react_v2(model: AzureChatOpenAI, tools, response_model):
    # https://python.langchain.com/v0.1/docs/modules/agents/how_to/agent_structured/
    class AgentState(MessagesState):
        # Final structured response from the agent
        final_response: response_model
    
    model_with_tools = model.bind_tools(tools, )
    model_with_structured_output = model.with_structured_output(response_model, )

    # Define the function that calls the model
    def call_model(state: AgentState):
        response = model_with_tools.invoke(state["messages"])
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    # Define the function that responds to the user
    def respond(state: AgentState):
        # response = model_with_structured_output.invoke(
        #     [HumanMessage(content=state["messages"][-1].content)]
        # )
        # return {'final_response': response}
        llm = create_extractor(model, tools=[response_model], tool_choice="auto")
        response = llm.invoke([HumanMessage(content=state["messages"][-1].content)])
        # We return the final answer
        return {"final_response": response['responses'][0]}
    
    # Define the function that determines whether to continue or not
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we respond to the user
        if not last_message.tool_calls:
            return "respond"
        # Otherwise if there is, we continue
        else:
            return "continue"
    
    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("respond", respond)
    workflow.add_node("tools", ToolNode(tools))

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "respond": "respond",
        },
    )

    workflow.add_edge("tools", "agent")
    workflow.add_edge("respond", END)
    graph = workflow.compile()
    return graph
