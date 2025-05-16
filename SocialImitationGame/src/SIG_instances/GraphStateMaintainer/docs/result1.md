# 多代理系统

## 用户:
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

## ChatGPT:
## Understanding the Strategy

We need to design a multi-agent system where each agent has a specific role and interacts with a shared memory structure (the **State** object) to achieve a given task. The agents will read from and write to specific parts of the **State** object, coordinating their actions to accomplish the goal described in the task.

## Designing the State Structure

The **State** object will be a Python dictionary with keys representing different parts of the shared memory. Here is a draft of the **State** structure:

```python
State = {
    "description": "",  # The task description and background information
    "goal": "",         # The goal of the task
    "plan": [],         # A list of planned actions to achieve the goal
    "current_step": 0,  # The index of the current step in the plan
    "observation": [],  # Observations from the environment after actions are taken
    "tools": {},        # A dictionary of available tools and their descriptions
    "rules": "",        # Rules and information about the environment
    "status": "",       # The current status of the task (e.g., "in progress", "completed")
    "errors": []        # Any errors encountered during the execution
}
```

## Designing Agent Roles

### 1. Routing Agent

**Role Name**: Routing Agent

**System Prompt**:
```
You are the Routing Agent. Your job is to manage the flow of the task execution. You need to read the current plan and decide which agent should be activated next based on the current step. You know all the agent roles and their descriptions. After any agent finishes their job, you will be activated again to decide the next step.
```

**Read from State**:
- `plan`
- `current_step`
- `status`

**Write to State**:
- None (the Routing Agent does not modify the State)

**Operation**:
- Read the current step from `current_step`.
- Determine the next agent to activate based on the plan and the current step.
- Activate the chosen agent.

### 2. Acting Agent

**Role Name**: Acting Agent

**System Prompt**:
```
You are the Acting Agent. Your job is to execute actions as per the plan and observe the environment. You need to read the current plan and identify the action to be taken. Use the appropriate tool to perform the action and then record the observation in the shared memory.
```

**Read from State**:
- `plan`
- `current_step`
- `tools`

**Write to State**:
- `observation` (append)
- `current_step` (increment by 1 after action is taken)

**Operation**:
- Read the current step from `current_step`.
- Extract the action from the `plan`.
- Use the correct tool to perform the action.
- Append the observation to `observation`.
- Increment `current_step` by 1.

### 3. Planning Agent

**Role Name**: Planning Agent

**System Prompt**:
```
You are the Planning Agent. Your job is to create a plan to achieve the given goal. You need to read the task description and the goal, then formulate a sequence of actions that will lead to the goal. Write this plan into the shared memory.
```

**Read from State**:
- `description`
- `goal`
- `tools`
- `rules`

**Write to State**:
- `plan` (replace)

**Operation**:
- Read the task description and goal.
- Formulate a sequence of actions (plan) to achieve the goal.
- Write the plan into the `plan` part of the State.

### 4. Analysis Agent

**Role Name**: Analysis Agent

**System Prompt**:
```
You are the Analysis Agent. Your job is to analyze observations and update the status of the task. You need to read the observations and determine if the goal has been achieved or if there are any errors. Update the status accordingly.
```

**Read from State**:
- `observation`
- `goal`

**Write to State**:
- `status` (replace)
- `errors` (append if any errors are found)

**Operation**:
- Read the observations.
- Analyze the observations to determine if the goal is achieved or if there are any errors.
- Update the status and append any errors to the `errors` part of the State.

## Updated State Structure

Based on the agent roles designed, here is the updated **State** structure:

```python
State = {
    "description": "",  # The task description and background information
    "goal": "",         # The goal of the task
    "plan": [],         # A list of planned actions to achieve the goal
    "current_step": 0,  # The index of the current step in the plan
    "observation": [],  # Observations from the environment after actions are taken
    "tools": {},        # A dictionary of available tools and their descriptions
    "rules": "",        # Rules and information about the environment
    "status": "",       # The current status of the task (e.g., "in progress", "completed")
    "errors": []        # Any errors encountered during the execution
}
```

This structure and the agent roles should provide a robust framework for solving tasks using a multi-agent system. Each agent has a specific role and interacts with the shared memory to coordinate their actions and achieve the goal efficiently.
