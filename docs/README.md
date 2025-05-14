# TradeCraft: an Arena for Long-term Strategic Social Reasoning and Planning

✨ **Highlights** ✨

*   **Advanced Social Intelligence Evaluation**: TradeCraft is a flexible, extensible multi-agent benchmark designed to evaluate high-order Theory of Mind, strategic social reasoning, and planning.
*   **Complex Long-Term Strategy**: Features 944 items, 1,144 crafting recipes, and 84 tag-based substitution rules, requiring agents to manage long multi-step crafting chains under strict compositional constraints.
*   **Dual Interfaces & Comprehensive Evaluation**: Offers a Gymnasium-compatible API for LLMs and a GUI for human players, alongside a multi-dimensional framework to evaluate agent capabilities thoroughly.

<!-- 📖 **Overview**

Developing agents capable of high-order recursive Theory of Mind and strategic social reasoning and planning remains a central challenge in advancing social intelligence, the evaluation of which is also a big challenge. We present *TradeCraft*, a flexible and extensible multi-agent benchmark environment designed to evaluate social intelligence under strict compositional constraints. *TradeCraft* comprises 944 items, 1,144 crafting recipes, and 84 tag-based item substitution rules, which require agents to reason over long multi-step crafting chains while accurately managing both item types and quantities. The platform supports variable participant configurations and dynamic rule conditions, enabling rich and diverse social scenarios. *TradeCraft* features dual interfaces: a Gymnasium-compatible API for integrating large language models and a graphical user interface for human participants, facilitating both human-AI interaction and model evaluation. Our multi-dimensional evaluation framework measures strategic reasoning and planning, cooperative and competitive interaction, resource negotiation, compliance with constraints, and adaptive behavior. By embedding strict rules, dynamic interactions, and trade-based goals, *TradeCraft* incentivizes high-order strategic reasoning and hybrid-motivation behavior, offering a rigorous testbed for agents capable of socially intelligent, long-term decision-making in structured environments. We also comprehensively evaluate current large language models in rich dimensions, providing useful insights into large language models' social intelligence. -->

🚀 **Key Features**

*   **Multi-Agent Social Intelligence Benchmark**: Designed to evaluate high-order recursive Theory of Mind, strategic social reasoning, and planning.
*   **Extensive Crafting System**: Features 944 items, 1,144 crafting recipes, and 84 tag-based item substitution rules, demanding complex, multi-step reasoning.
*   **Dual Interfaces**:
    *   **Gymnasium-Compatible API**: For seamless integration and evaluation of Large Language Models (LLMs) and other AI agents.
    *   **Graphical User Interface (GUI)**: For human participation, observation, and human-AI interaction.
*   **Flexible Configuration**: Supports variable participant numbers and dynamic rule conditions to create diverse social scenarios.
*   **Compositional Constraints**: Enforces strict rules on item crafting and interaction, requiring precise management of item types and quantities.
*   **Long-Horizon Tasks**: Challenges agents with tasks that require planning over extended sequences of actions.
*   **Multi-Dimensional Evaluation Framework**: Assesses:
    *   Strategic reasoning and planning
    *   Cooperative and competitive interaction
    *   Resource negotiation
    *   Compliance with constraints
    *   Adaptive behavior
*   **Incentivizes Advanced Reasoning**: Embeds strict rules, dynamic interactions, and trade-based goals to promote high-order strategic thinking and hybrid-motivation behavior.

🏗️ **Architecture & Pipeline**

*   TradeCraft utilizes a client-server architecture to manage game state and agent interactions.
*   The server hosts the game logic, including the crafting rules, item states, and agent management.
*   Agents (LLMs or human players) connect to the server via:
    *   The **Gymnasium-compatible API** for programmatic control, allowing AI agents to perceive the environment and execute actions.
    *   The **Graphical User Interface (GUI)**, which provides a visual representation of the game world for human players.
*   This dual-interface design allows for flexible experimentation, including AI vs. AI, Human vs. Human, and Human vs. AI setups.

<img src="figs/pipeline.png" alt="Pipeline" width="800">

📊 **Benchmark & Evaluation**

*   TradeCraft provides a rigorous testbed for evaluating social intelligence in structured, long-term decision-making environments.
*   Our comprehensive evaluation framework assesses multiple dimensions of agent performance (see Key Features).
*   We have conducted extensive evaluations of current Large Language Models, providing insights into their social intelligence capabilities.
*   For detailed benchmark results and analysis, please refer to our paper: `[Link to Paper/Placeholder for Paper Title]`



💾 **Dataset & Game Rules**

*   The core of TradeCraft is its rich and complex crafting system:
    *   **Items**: 944 unique items.
    *   **Crafting Recipes**: 1,144 distinct recipes.
    *   **Tag-Based Substitution Rules**: 84 rules allowing for flexible item usage based on tags.
*   These components create a vast combinatorial space, requiring agents to navigate long crafting chains and adapt to dynamic conditions.
*   Game rules are designed to be strict and compositional, ensuring success depends on careful adherence to constraints and strategic interaction.

⚙️ **Setup**

### Installation

```bash
# Create and activate a conda environment (Python 3.10 recommended)
conda create -n tradecraft python=3.10
conda activate tradecraft

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory for API configurations:

```
OPENAI_API_KEY=your_openai_api_key
CLAUDE_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_api_key
# Add other necessary API keys or configurations
```

### Running the Server

```bash
# Start the game server
# It will typically run on http://localhost:5000
python tradeCraft/run_server.py
```

🎮 **Usage**

*   **Running the Game Server**:
    *   Execute the command provided in the "Running the Server" section above.
*   **Developing and Running Agents (via Gymnasium API)**:
    *   Implement your agent logic to interact with the environment using the Gymnasium API.
    *   Refer to the `SocialImitationGame/src/agent_proxy/` directory for base agent structures and the `tradeCraft/src/` for game-specific logic.
    *   *(Consider adding an `examples/` directory with sample agent implementations and linking it here.)*
*   **Playing as a Human (via GUI)**:
    *   Once the server is running, open your web browser and navigate to `http://localhost:5000` (or the configured address).
    *   Follow the on-screen instructions to join or observe games.

📜 **License**

This project is licensed under the terms of the [Specify License Name - e.g., MIT License]. Please see the `LICENSE` file for more details.


🙏 **Acknowledgements**
