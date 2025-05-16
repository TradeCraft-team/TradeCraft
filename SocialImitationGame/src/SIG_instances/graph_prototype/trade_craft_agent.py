from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from src.SIG_core.base_sig_agent import BaseSIGAgent
import json

# 定义状态结构
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]  # 存储消息历史
    current_phase: str  # 当前游戏阶段
    my_resources: Dict[str, float]  # 我方资源
    opponent_resources: Dict[str, float]  # 对手资源
    goal_item: str  # 目标物品
    username: str  # 玩家用户名
    opponent_username: str  # 对手用户名
    crafting_plan: List[Dict]  # 合成计划
    trade_strategy: Dict  # 交易策略
    opponent_goal_prediction: str  # 对手目标预测

class TradeCraftAgent(BaseSIGAgent):
    def __init__(self, proxy, *args, **kwargs):
        super().__init__(proxy, *args, **kwargs)
        self.llm = kwargs.get("llm", None)
        self.full_tool_set = kwargs.get("full_tool_set", [])
        self.graph = self._build_graph()

    async def _get_tool_by_name(self, tool_name: str):
        """获取指定名称的工具"""
        for tool in self.full_tool_set:
            if tool.__name__ == tool_name:
                return tool
        return None

    async def _get_item_info(self, item_name: str):
        """获取物品的合成配方信息"""
        tool = await self._get_tool_by_name("item_info")
        if tool:
            return await tool(item_name)
        return None

    async def _check_recipe(self, recipe: Dict):
        """检查合成配方是否可行"""
        tool = await self._get_tool_by_name("craft_recipe_check")
        if tool:
            return await tool({"recipe": recipe})
        return None

    async def _apply_recipe(self, recipe: Dict):
        """应用合成配方"""
        tool = await self._get_tool_by_name("craft_recipe_apply")
        if tool:
            return await tool({"recipe": recipe})
        return None

    async def _extract_proposal_from_message(self, messages: List[Dict]):
        """从消息中提取交易提案"""
        if not messages:
            return None
            
        prompt = f"""
        From the latest game message below, extract the trade proposal information.
        Return the result in JSON format:
        {{
            "offer": {{"item_name": amount, ...}},
            "request": {{"item_name": amount, ...}},
            "partner": "username"
        }}

        Latest message:
        {messages[-1].get('content', '')}
        """
        
        try:
            proposal_info = await self.llm.ainvoke(prompt)
            return json.loads(proposal_info)
        except:
            return None

    async def _get_initial_resources(self):
        """获取初始资源状态"""
        # 使用 check_event_history 工具获取初始状态信息
        for tool in self.full_tool_set:
            if tool.__name__ == "check_event_history":
                history = await tool()
                # 使用 LLM 解析历史信息中的资源分配信息
                prompt = f"""
                From the game history below, extract the initial resources for both players.
                Return the result in JSON format:
                {{
                    "my_resources": {{"item_name": amount, ...}},
                    "opponent_resources": {{"item_name": amount, ...}},
                    "opponent_username": "username"
                }}

                Game history:
                {history}
                """
                try:
                    resources_info = await self.llm.ainvoke(prompt)
                    return json.loads(resources_info)
                except:
                    return {
                        "my_resources": {},
                        "opponent_resources": {},
                        "opponent_username": ""
                    }
        return {
            "my_resources": {},
            "opponent_resources": {},
            "opponent_username": ""
        }

    async def _create_initial_plan(self, state, crafting_paths):
        """创建初始游戏计划"""
        prompt = f"""
        Create a comprehensive game plan based on:
        1. Goal item: {state["goal_item"]}
        2. Complete crafting information:
        {json.dumps(crafting_paths, indent=2)}
        3. Initial resources:
           - Our resources: {state["my_resources"]}
           - Opponent's resources: {state["opponent_resources"]}

        Create a plan that includes:
        1. Optimal crafting sequence
        2. Required trades
        3. Resource priorities

        Return in JSON format:
        {{
            "crafting_plan": [
                {{"step": 1, "recipe": {{"input": {{}}, "output": {{}}}}, "required_resources": []}},
                ...
            ],
            "trade_strategy": {{
                "priority_requests": ["item1", "item2"],
                "tradeable_resources": ["item1", "item2"],
                "trade_rules": ["rule1", "rule2"]
            }}
        }}
        """
        try:
            plan = await self.llm.ainvoke(prompt)
            return json.loads(plan)
        except:
            return {
                "crafting_plan": [],
                "trade_strategy": {
                    "priority_requests": [],
                    "tradeable_resources": [],
                    "trade_rules": []
                }
            }

    async def _predict_opponent_goal(self, state):
        """预测对手的目标物品"""
        prompt = f"""
        Based on the opponent's behavior, predict their goal:
        1. Their trade proposals: {state.get("opponent_trades", [])}
        2. Their resource changes: {state["opponent_resources"]}
        3. Their rejected trades: {state.get("rejected_trades", [])}

        What item might they be trying to craft?
        Return just the item name, or "unknown" if unclear.
        """
        try:
            prediction = await self.llm.ainvoke(prompt)
            return prediction.strip()
        except:
            return "unknown"

    async def _update_plan(self, state, crafting_paths):
        """更新游戏计划"""
        prompt = f"""
        Update our game plan based on:
        1. Current state:
           - Our resources: {state["my_resources"]}
           - Opponent resources: {state["opponent_resources"]}
           - Opponent's predicted goal: {state["opponent_goal_prediction"]}
        2. Original plan:
           - Crafting plan: {state.get("crafting_plan", [])}
           - Trade strategy: {state.get("trade_strategy", {})}
        3. Crafting paths: {json.dumps(crafting_paths, indent=2)}

        Return updated plan in the same JSON format as before.
        Consider:
        1. What adjustments are needed based on current resources?
        2. How to counter opponent's strategy?
        3. What alternative paths are available?
        """
        try:
            updated_plan = await self.llm.ainvoke(prompt)
            return json.loads(updated_plan)
        except:
            return state.get("crafting_plan", []), state.get("trade_strategy", {})

    async def process_game_start(self, state):
        """处理游戏开始状态"""
        messages = state.get("messages", [])
        if not messages:
            return state

        # 使用 LLM 分析初始信息
        prompt = f"""
        Based on the game start information below, please extract:
        1. The player's username
        2. The goal item that needs to be crafted

        Game information:
        {messages[0].get('content', '')}

        Return your analysis in JSON format:
        {{
            "username": "extracted username",
            "goal_item": "extracted goal item"
        }}
        """

        llm_response = await self.llm.ainvoke(prompt)
        try:
            import json
            analysis = json.loads(llm_response)
        except:
            analysis = {
                "username": "",
                "goal_item": ""
            }

        # 获取初始资源
        resources_info = await self._get_initial_resources()

        # 获取合成路径信息
        crafting_paths = await self._analyze_crafting_path(state["goal_item"])
        
        # 创建初始计划
        initial_plan = await self._create_initial_plan(state, crafting_paths)
        
        return {
            **state,
            "messages": messages,
            "current_phase": "waiting_server",
            "my_resources": resources_info["my_resources"],
            "opponent_resources": resources_info["opponent_resources"],
            "goal_item": analysis.get("goal_item", ""),
            "username": analysis.get("username", ""),
            "opponent_username": resources_info["opponent_username"],
            "crafting_plan": initial_plan.get("crafting_plan", []),
            "trade_strategy": initial_plan.get("trade_strategy", {}),
            "opponent_goal_prediction": "unknown"
        }

    async def _update_resources_after_trade(self, state, trade_info):
        """更新交易后的资源状态"""
        if not trade_info:
            return state
            
        my_resources = state["my_resources"].copy()
        opponent_resources = state["opponent_resources"].copy()
        
        # 更新资源
        for item, amount in trade_info["offer"].items():
            my_resources[item] = my_resources.get(item, 0) - amount
            opponent_resources[item] = opponent_resources.get(item, 0) + amount
            
        for item, amount in trade_info["request"].items():
            my_resources[item] = my_resources.get(item, 0) + amount
            opponent_resources[item] = opponent_resources.get(item, 0) - amount
            
        return {
            **state,
            "my_resources": my_resources,
            "opponent_resources": opponent_resources
        }

    async def _update_resources_after_craft(self, state, recipe):
        """更新合成后的资源状态"""
        if not recipe:
            return state
            
        my_resources = state["my_resources"].copy()
        
        # 扣除输入材料
        for item, amount in recipe["input"].items():
            my_resources[item] = my_resources.get(item, 0) - amount
            
        # 添加输出物品
        for item, amount in recipe["output"].items():
            my_resources[item] = my_resources.get(item, 0) + amount
            
        return {
            **state,
            "my_resources": my_resources
        }

    async def _analyze_crafting_path(self, item_name: str):
        """分析物品的完整合成路径"""
        items_to_check = {item_name}
        crafting_info = {}
        
        while items_to_check:
            current_item = items_to_check.pop()
            if current_item not in crafting_info:
                info = await self._get_item_info(current_item)
                crafting_info[current_item] = info
                
                # 从配方中提取新的材料
                try:
                    recipes = info.split('\n')[0]  # 获取第一行（输出配方）
                    for recipe in recipes.split(';'):
                        if 'input' in recipe:
                            ingredients = recipe.split('input:')[1].split('output:')[0]
                            for ingredient in ingredients.split(','):
                                if ':' in ingredient:
                                    new_item = ingredient.split(':')[0].strip()
                                    if new_item not in crafting_info:
                                        items_to_check.add(new_item)
                except:
                    pass
                    
        return crafting_info

    async def make_proposal(self, state):
        """提出交易提案"""
        # 更新对手目标预测
        opponent_goal = await self._predict_opponent_goal(state)
        state = {**state, "opponent_goal_prediction": opponent_goal}
        
        # 获取并更新计划
        crafting_paths = await self._analyze_crafting_path(state["goal_item"])
        updated_plan = await self._update_plan(state, crafting_paths)
        state = {
            **state,
            "crafting_plan": updated_plan.get("crafting_plan", state["crafting_plan"]),
            "trade_strategy": updated_plan.get("trade_strategy", state["trade_strategy"])
        }
        
        # 基于计划生成提案
        prompt = f"""
        Generate a trade proposal based on our plan:
        1. Current plan: {json.dumps(state["crafting_plan"], indent=2)}
        2. Trade strategy: {json.dumps(state["trade_strategy"], indent=2)}
        3. Opponent's predicted goal: {state["opponent_goal_prediction"]}
        4. Current resources:
           - Ours: {state["my_resources"]}
           - Opponent's: {state["opponent_resources"]}

        Follow trade rules:
        {json.dumps(state["trade_strategy"].get("trade_rules", []), indent=2)}

        Return trade proposal in required JSON format.
        """
        
        proposal = await self.llm.ainvoke(prompt)
        try:
            proposal_dict = json.loads(proposal)
            # 提交提案
            tool = await self._get_tool_by_name("submit_proposal")
            if tool:
                await tool(proposal_dict)
                return {
                    **state,
                    "current_phase": "waiting_server"
                }
        except:
            pass
            
        return {
            **state,
            "current_phase": "waiting_server"
        }

    async def handle_opponent_proposal(self, state):
        """处理对手的提案"""
        # 更新对手目标预测
        opponent_goal = await self._predict_opponent_goal(state)
        state = {**state, "opponent_goal_prediction": opponent_goal}
        
        # 获取并更新计划
        crafting_paths = await self._analyze_crafting_path(state["goal_item"])
        updated_plan = await self._update_plan(state, crafting_paths)
        state = {
            **state,
            "crafting_plan": updated_plan.get("crafting_plan", state["crafting_plan"]),
            "trade_strategy": updated_plan.get("trade_strategy", state["trade_strategy"])
        }
        
        # 1. 从消息中提取提案信息
        proposal = await self._extract_proposal_from_message(state["messages"])
        if not proposal:
            return {**state, "current_phase": "waiting_server"}
            
        # 2. 分析目标物品的完整合成路径
        crafting_paths = await self._analyze_crafting_path(state["goal_item"])
            
        # 3. 使用 LLM 评估提案
        prompt = f"""
        Evaluate the trade proposal based on the following information:
        1. My goal item: {state["goal_item"]}
        2. Complete crafting information:
        {json.dumps(crafting_paths, indent=2)}
        3. My current resources: {state["my_resources"]}
        4. Proposal:
           - They offer: {proposal.get("offer", {})}
           - They request: {proposal.get("request", {})}

        Analyze:
        1. Does this trade help us get closer to our goal?
        2. Are we giving away materials we need for crafting?
        3. Is this a fair trade considering the crafting values?
        4. Could the opponent be trying to craft our goal item?

        Return just "accept" or "reject" and a brief explanation message.
        Format: "decision|message"
        """
        
        response = await self.llm.ainvoke(prompt)
        decision, message = response.split("|", 1)
        decision = decision.strip().lower()
        
        # 4. 发送决定
        tool = await self._get_tool_by_name("approval_or_reject")
        if tool:
            await tool({
                "decision": decision,
                "message": message.strip()
            })
        
        # 5. 如果接受，更新资源状态
        if decision == "accept":
            updated_state = await self._update_resources_after_trade(state, proposal)
        else:
            updated_state = state
            
        return {
            **updated_state,
            "current_phase": "waiting_server"
        }

    async def handle_crafting(self, state):
        """处理合成阶段"""
        updated_state = state
        has_crafted = False

        # 获取并更新计划
        crafting_paths = await self._analyze_crafting_path(state["goal_item"])
        updated_plan = await self._update_plan(state, crafting_paths)
        updated_state = {
            **updated_state,
            "crafting_plan": updated_plan.get("crafting_plan", state["crafting_plan"]),
            "trade_strategy": updated_plan.get("trade_strategy", state["trade_strategy"])
        }

        while True:
            # 基于计划选择下一个合成步骤
            prompt = f"""
            Choose the next crafting step based on our plan:
            1. Crafting plan: {json.dumps(updated_state["crafting_plan"], indent=2)}
            2. Current resources: {updated_state["my_resources"]}
            3. Available recipes: {json.dumps(crafting_paths, indent=2)}

            Return the best recipe to execute next, or null if no viable step.
            Include explanation of why this step is chosen.
            """
            
            # 2. 使用 LLM 分析可行的合成路径
            recipe_suggestion = await self.llm.ainvoke(prompt)
            try:
                recipe = json.loads(recipe_suggestion)
                if not recipe:
                    break  # 没有可行的配方，退出循环
                    
                # 3. 检查配方是否可行
                check_result = await self._check_recipe(recipe)
                if check_result and "success" in check_result:
                    # 4. 应用配方
                    await self._apply_recipe(recipe)
                    # 5. 更新资源状态
                    updated_state = await self._update_resources_after_craft(updated_state, recipe)
                    has_crafted = True
                    
                    # 检查是否已经达到目标
                    if updated_state["my_resources"].get(updated_state["goal_item"], 0) > 0:
                        break  # 已经合成目标物品，退出循环
                else:
                    break  # 配方检查失败，退出循环
            except:
                break  # 出现异常，退出循环
        
        # 6. 发送完成信号
        tool = await self._get_tool_by_name("craft_done")
        if tool:
            await tool({"username": state["username"]})
        
        return {
            **updated_state,
            "current_phase": "waiting_server"
        }

    async def wait_for_instruction(self, state):
        """等待并处理服务器指示"""
        # 检查最新消息，判断是否需要我方发起提案
        messages = state.get("messages", [])
        if not messages:
            return state
            
        # 使用 LLM 分析最新消息，判断当前应该执行的操作
        prompt = f"""
        Based on the latest game message below, determine what action is required:
        1. If we need to make a proposal, return "make_proposal"
        2. If we need to respond to opponent's proposal, return "handle_proposal"
        3. If we need to do crafting, return "crafting"
        4. If waiting for server or unclear, return "wait"

        Latest message:
        {messages[-1].get('content', '')}

        Return just one of these exact strings: "make_proposal", "handle_proposal", "crafting", "wait"
        """
        
        next_action = await self.llm.ainvoke(prompt)
        next_action = next_action.strip().lower()
        
        return {
            **state,
            "current_phase": next_action
        }

    def _build_graph(self):
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("process_game_start", self.process_game_start)
        workflow.add_node("wait_for_instruction", self.wait_for_instruction)
        workflow.add_node("make_proposal", self.make_proposal)
        workflow.add_node("handle_opponent_proposal", self.handle_opponent_proposal)
        workflow.add_node("handle_crafting", self.handle_crafting)

        # 设置入口
        workflow.set_entry_point("process_game_start")

        # 添加边和条件
        workflow.add_edge("process_game_start", "wait_for_instruction")
        
        # 从等待状态转向具体操作
        workflow.add_conditional_edges(
            "wait_for_instruction",
            self._route_from_waiting,
            {
                "make_proposal": "make_proposal",
                "handle_proposal": "handle_opponent_proposal",
                "crafting": "handle_crafting",
                "wait": "wait_for_instruction"
            }
        )

        # 所有操作完成后回到等待状态
        workflow.add_edge("make_proposal", "wait_for_instruction")
        workflow.add_edge("handle_opponent_proposal", "wait_for_instruction")
        workflow.add_edge("handle_crafting", "wait_for_instruction")

        return workflow.compile()

    def _route_from_waiting(self, state):
        phase = state.get("current_phase", "wait")
        if phase == "make_proposal":
            return "make_proposal"
        elif phase == "handle_proposal":
            return "handle_proposal"
        elif phase == "crafting":
            return "crafting"
        elif phase == "wait":
            return "wait"
        return END

    def save_graph_to_local(self, file_path: str):
        image_data = self.graph.get_graph().draw_mermaid_png()
        with open(file_path, 'wb') as file:
            file.write(image_data)

