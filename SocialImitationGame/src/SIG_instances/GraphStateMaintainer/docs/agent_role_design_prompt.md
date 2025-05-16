Please design a general multi-agent structure for accomplishing a task.

## Background
A task is given via language, where a *description* is given, introducing
necessary background and goal of the task. Based on the reinforcement learning
framework, a set of "tools" are provided to interact with the environment. Among
the tools, there are several "action tools" which could change the state of environment
and get new observation as return. Other "help tools" are designed to query for
necessary information or rule description of the environment. Each tool is with
a description of itself, telling the agent how it could be used. The ultimate goal
of the agent system you design should be achieving the goal in the task desciption.
Usually, multiple actions has to be taken and various abilities are necessary.

## Strategy
We want to solve the above problem by designing a general multi-agent structure,
where each agent is driven by a large language model with prompt particularly 
designed to invoke some necessary ability. Among the agents, a **State** object
as python dictionary is shared to all agents, as a structured shared memory among agents.
Each agent read necessary part of the shared memory and make their own contribution,
via changing part of the shared memory. For example, the *planning agent* may write
his plan into the "plan" part of the **State** object, and the *action agent* calls
the correct tool with correct arguments, and write what he observe from the environment
to the observation part of the state. Each agent may only see their own necessary part
of the shared memory by translating value for corresponding keys in the State dictionary.
The agent may not hold a conversation history, as we think all necessary information could
be stored to the shared memory.

## Your job
Please follow the instructions below, step by step, during which, feel free to write any thoughts
which could help you work better.

Instructions:
1. Try to understand the strategy described above.
2. Design a useful State structure. The knowledge of cognitive architectures is useful here. 
   So you may recall it before designing. No worries if later you find necessary to add a new
   key when you design agent roles, as we will collect the new ones and add them into states.
   So this could be only a draft. 
3. Design the agent roles one by one. For each of which, describe the role-name, the system prompt
   describing its job and necessary information it could use (unrelated to the State dictionary, like what other 
   agent-roles are, etc.), which part
   of the shared memory (state dictionary) it can read, which part of the shared memory it should
   write (also design the "writting" is to replace or to append). There are two agent roles you have to
   design: the *routing agent* and the *acting agent*. To EXAMPLES of the descriptions are shown bellow.
   Remember, you may redesign them, the example provided may not be the perfect ones!
   - routing agent: he is a manager, telling which other agent should be called to function, so it
                    knows what other agent-roles are, including their descriptions.
                    The routing agent reads the **plan** part of the state, finding in the plan
                    what is the next step which is not done, and decide which agent-role in his list 
                    is most suitable for the next step, then tells that agent-role to work. 
                    The routing agent does not change the shared memory.
                    After any other agent-role finishes their jobs, the routing agent is activated again,
                    to decide who to be activated next.
                    
   - acting agent: he is the actor, someone else may have analyzed the situation, made a good plan,
                   but the acting agent's role is to act and observe the enviroment.
                   The acting agent reads the **plan** part of the shared memory, extracting the action
                   request, and call the correct tool, finally append the return text to the **observation**
                   part of the state dictionary.
4. Summarizing the above agent-roles you design, you may write an updated State dictionary design.        

Now you can work on your job:
