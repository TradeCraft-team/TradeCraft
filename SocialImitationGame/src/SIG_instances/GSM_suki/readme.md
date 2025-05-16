
for 0926 discussion

- full automatious agent pipeline base langgraph
    - graph construction (nodes/edges/transitions)
        - graph image;
        - easy to construct
            - workflow definition;
            - manage the workflow and states;
    - react & structured output: avoid the tedious manual string output parsing;
        - structured output: 
            - openai official
                - https://openai.com/index/introducing-structured-outputs-in-the-api/
                - gpt-4o-2024-08-06
            - langchain: 
                - https://api.python.langchain.com/en/latest/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html
                - (response/output) model as a tool
                    - `llm.bind_tools([tool, Response], strict=True)`
                    - `resp = llm.with_structured_output(Response, strict=True)`
        - tool input validation check by pydantic;
    - langsmith to debug
        - node/tool/agent: input/output
        - event translatation;
        - tool input compatibility to the server validation (pydantc check);

- trade craft
    - online/interactive multi-turn 
        - dynamic/adaptive reasoning/planning/acting
    - multi-players 

- todo
    - translate 
        - necessary event translation to control the context
    - multi-turn pipeline
        - system support or llm to wait for the opponent's response especially when make a proposal ??
    - classifical prompt engineering: https://arxiv.org/pdf/2409.10038
        - plan (proposition, proposer)
        - reflect (critique, critic)
        - summary (summarizer)
        - repeat/cycle
        ...
    - reasoning scale
        - inner turn
        - inter turn

--------------------------------------------


### related tools

- 决策相关
    - item_info,
        - input: item
        - output: item 的描述
    - possible_recipes_from_hand,
        - input: hand
        - output: 可能的 recipe
    - check_event_history
        - input: username
        - output: 事件历史

- 交互（game dynamics）相关：emit event to game server base game_dynamics
    - list: 这些 tool 都会 同步事件，内部基于 game dynamics 实现 wait for the specific response；
        - submit_proposal,
        - approval_or_reject,
        - craft_done,
        - craft_recipe_check,
        - craft_recipe_apply,
    - 目前的实现，工具名基于game_dynamics映射到具体的 event 实现事件的触发；
        - `tool_proxy.game_dynamics.toolname_to_eventname[toolname]`
            - `player__{toolname}`

```
def game_start(self):
    """
    Callback of server__game_start.
    It registers the rest of waitfor_methods, since when the self.base_msg_dict is fixed.
    """

    for name, rets in self.game_dynamics.game_dynamics.items():
        self.generate_waitfor_methods(name, rets)
```

### ReAct vs. langgraph

ReAct: `<thought-action-observatio>` 的三元组

- 其实有一个 yield 的 aciton 是否为 AgentFinish 的循环判断
    - AgentAction 和 AgentFinish
    - ReAct 本质上是循环执行工具，直到回到了初始问题（AgentFinish）    
        - 多数时间，初始问题的回答，需要执行多次工具调用；
        - 但仍然只是解决一个问题；
        - 考虑到 trade craft 是多轮的，需要每轮都调用 react，单个的 react 无法完成 trade craft 的多轮博弈过程；
- 有别于一般的没有 cycle 的 linear chain
- 其实是就是一个 graph

```
graph = create_react_agent(model, tools=tools)
display(Image(graph.get_graph().draw_mermaid_png()))
```

### todo & question

- ~~@tool, 必须传入参数（tool_input~~
- ~~generate_prompt 调用language_processor生成query，应该作为工具的一部分，而不是额外进一步的处理~~
- 考虑基于 react 实现一步决策，然后基于 langgraph prototype 交互决策；
