async def _phase_route(self, state: GraphState):
        # https://python.langchain.com/v0.1/docs/modules/agents/how_to/agent_structured/

        class Response(BaseModel):
            """Final response to the question being asked"""
            next_step: Literal['make_decision', 'make_proposal'] = Field(description="The next phase of the game")
            current_hands: Dict[str, str] = Field(description="The current hands of the player")
            crafting_target: str = Field(description="The target to be crafted")
            oppos_hands: Dict[str, Dict[str, str]] = Field(description="The hands of the opponents")

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        llm_with_tools = self.llm.bind_tools(self.full_tool_set + [Response])
        agent = (
            {
                "input": lambda x: x["input"],
                # Format agent scratchpad from intermediate steps
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | react_parse
        )
        agent_executor = AgentExecutor(tools=self.full_tool_set, agent=agent, verbose=True, stream_runnable=False, handle_parsing_errors=True)

        resp = await agent_executor.ainvoke(
            {"input": 
             f"{state['input']}\n"
             f"Extract only the current game states required by the `Response` using the provided tools.\n"
            }, 
            # return_only_outputs=True
        )
        return resp

async def _phase_route(self, state: GraphState):

        game_input = state['input']

        class Response(BaseModel):
            """Final response to the question being asked"""
            next_step: Literal['make_decision', 'make_proposal'] = Field(description="The next phase of the game")
            current_hands: Dict[str, str] = Field(description="The current hands of the player")
            crafting_target: str = Field(description="The target to be crafted")
            oppos_hands: Dict[str, Dict[str, str]] = Field(description="The hands of the opponents")

        # Define the prompt template
        prompt = PromptTemplate.from_template(
            "{game_input}\n"
            "Extract the current game states using various tools, including current hands and crafting target.\n"
            "Response with the following format:\n"
            "{format_instructions}"
        )

        # Create the output parser
        parser = PydanticOutputParser(pydantic_object=Response)

        # Create the agent
        tools = self.full_tool_set
        react_prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(llm=self.llm, tools=tools, prompt=react_prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, stream_runnable=False, handle_parsing_errors=True)

        # Create the chain
        chain = (
            {"game_input": RunnablePassthrough(), 
             "format_instructions": lambda _: parser.get_format_instructions()}
            | prompt
            | (lambda x: {'input': x})
            | agent_executor
        )

        # Invoke the chain
        resp = await chain.ainvoke(game_input)

        try:
            json_str = re.search(r'```json\s*([\s\S]*?)```', resp['output']).group(1)
            result = json.loads(json_str)
        except:
            result = resp['output']

        return {"next_step": result['next_step'], 
                "current_hands": result['current_hands'], 
                "crafting_target": result['crafting_target'],
                "oppos_hands": result['oppos_hands']}

async def _make_decision(self, state: GraphState):
        class Response(BaseModel):
            """Final response to the question being asked"""
            approval_or_reject: Literal['approve', 'reject'] = Field(description="The approval or reject of the proposal")

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        llm_with_tools = self.llm.bind_functions(self.full_tool_set + [Response])
        agent = (
            {
                "input": lambda x: x["input"],
                # Format agent scratchpad from intermediate steps
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | react_parse
        )

        agent_executor = AgentExecutor(tools=self.full_tool_set, agent=agent, verbose=True, stream_runnable=False, handle_parsing_errors=True)

        resp = await agent_executor.ainvoke(
            {"input": f"Now the game state is {translate_current_states(state)}. You are in the make_decision phase, and you have to make a decision on the proposal from my opponent with the following format:\n{Response.schema_json()}"}, 
            return_only_outputs=True
        )

        return resp


async def _make_proposal(self, state: GraphState):

        class Response(BaseModel):
            """Final response to the question being asked"""
            offer: Dict[str, str] = Field(description="The offer to be made")
            request: Dict[str, str] = Field(description="The request to be made")
            self: str = Field(description="The username of the proposer")
            partner: str = Field(description="The username of the opponent")
            message: str = Field(description="The message to be sent")

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # llm_with_tools = self.llm.bind_tools(self.full_tool_set + [Response])
        llm_with_tools = self.llm.bind_functions(self.full_tool_set + [Response])
        agent = (
            {
                "input": lambda x: x["input"],
                # Format agent scratchpad from intermediate steps
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | react_parse
        )
        agent_executor = AgentExecutor(tools=self.full_tool_set, agent=agent, verbose=True)

        resp = await agent_executor.ainvoke(
            {"input": f"Now the game state is {translate_current_states(state)}. You are in the make_proposal phase, and you have to make a proposal to my opponent"}, 
            return_only_outputs=True
        )
        return resp



# todo, 1015, 不稳定，需要替换为更标准化的方案
    # async def _phase_route(self, state: GraphState):

    #     game_input = state['input']

    #     class Response(BaseModel):
    #         """Final response to the question being asked"""
    #         username: str = Field(description="The username of the player")
    #         next_step: Literal['make_decision', 'make_proposal',
    #                            'crafting'] = Field(
    #                                description="The next phase of the game")
    #         current_hands: Dict[str, str] = Field(
    #             description="The current hands of the player")
    #         crafting_target: str = Field(
    #             description="The target to be crafted")
    #         oppos_hands: Dict[str, Dict[str, str]] = Field(
    #             description="The hands of the opponents")

    #     # Define the prompt template
    #     # return StringPromptValue instance
    #     prompt = PromptTemplate.from_template(
    #         "{game_input}\n"
    #         "Extract the current game states using various tools, including current hands and crafting target.\n"
    #         "**Finally** response with the following format:\n"
    #         "{format_instructions}")

    #     # Create the output parser
    #     parser = PydanticOutputParser(pydantic_object=Response)

    #     # Create the agent
    #     tools = self.full_tool_set
    #     agent = create_react_agent(llm=self.llm,
    #                                tools=tools,
    #                                prompt=self.react_prompt_temaplte)
    #     agent_executor = AgentExecutor(agent=agent,
    #                                    tools=tools,
    #                                    stream_runnable=False,
    #                                    handle_parsing_errors=True)

    #     # Create the chain
    #     chain = ({
    #         "game_input":
    #         RunnablePassthrough(),
    #         "format_instructions":
    #         lambda _: parser.get_format_instructions()
    #     }
    #              | prompt
    #              | (lambda x: {
    #                  'input': x.text
    #              })
    #              | agent_executor)

    #     # Invoke the chain
    #     resp = await chain.ainvoke(game_input)

    #     try:
    #         json_str = re.search(r'```json\s*([\s\S]*?)```',
    #                              resp['output']).group(1)
    #         result = json.loads(json_str)
    #     except:
    #         result = resp['output']

    #     return {
    #         "username": result['username'],
    #         "next_step": result['next_step'],
    #         "current_hands": result['current_hands'],
    #         "crafting_target": result['crafting_target'],
    #         "oppos_hands": result['oppos_hands']
    #     }