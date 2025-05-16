"""
"""
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from ...SIG_core import BaseSIGAgent



class ReActAgent(BaseSIGAgent):
    """
    """

    def __init__(self, proxy, *args, **kwargs):
        """
        Initialize
        """
        super().__init__(proxy, *args, **kwargs)
        self.llm = kwargs.get("llm")
        self.full_tool_set = kwargs.get("full_tool_set", [])
        self.prompt_template = kwargs.get("prompt_template", None)

        if self.prompt_template is None:
            # https://smith.langchain.com/hub/hwchase17/react
            # Question: {input}
            # Thought:{agent_scratchpad}
            self.prompt_template = hub.pull("hwchase17/react")

        # intermediate_steps: list of tuple (action, observation)
        # <thought-action-observation>
        # observation means the return of the action (function call)
        self.agent = create_react_agent(self.llm, self.full_tool_set, self.prompt_template)
        self.agent_executor = AgentExecutor(agent=self.agent,
                                            tools=self.full_tool_set,
                                            verbose=True,
                                            # TongGPT api compatible
                                            stream_runnable=False)


    async def start_sig(self, _input):
        # _input: as the query of the user
        # here this invoke, will ended until yield the AgentFinish
        await self.agent_executor.ainvoke({"input": _input})
