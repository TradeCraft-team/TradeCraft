# Evaluation Item: Strategic Planning

You will be provided with two inputs:
1. **Game Introduction** — This is the game rule introduction. Read it carefully to understand the gameplay and rules.
2. **Game Log** — This is the actual game log to be evaluated.

You are asked to evaluate how well the player demonstrates **Strategic Planning** throughout the game.
**Strategic Planning** includes making long-term decisions that align with the final goal, adapting to the evolving game state, and managing limited resources proactively.

Each turn in the game log begins with the line:
## 🌀 Turn n start!
You must identify these markers and evaluate the behavior of each player for each individual turn.

⚠️ Important Instruction:
You MUST evaluate **every single turn** found in the game log. Do not skip or merge turns. If the game log contains 10 turns, your output JSON must include exactly 10 entries labeled from `"turn 1"` to `"turn 10"`.

Failure to evaluate all turns will be considered an incomplete response.

Please compare **both players** based on the game log. For each player and each turn, assign a **score from 0.0 to 1.0**, where:
- 1.0 = consistently demonstrated strong and consistent strategic planning
- 0.0 = no signs of strategic planning or completely ineffective behavior
- Intermediate values reflect partial effectiveness

---

Within a turn, you may encounter the following important elements:
- Player `player_name` (proposer) THINKS: ...
- Player events (actions taken)
- Server events (environmental feedback or results)

All these should be used as evidence when scoring.

---

## Game Introduction
Below here is the  **game introduction**
{{intro}}

## Game Log
Below here are the **game logs**
{{game_log}}

### Output Format (Strict JSON):
Return a JSON object containing scores and justifications **for each turn** in the game log.

```json
[
  {
    "turn 1": [
      {
        "user": "Alice",
        "score": 0.85,
        "justification": "Your explanation here."
      },
      {
        "user": "Bob",
        "score": 0.60,
        "justification": "Your explanation here."
      }
    ]
  },
  {
    "turn 2": [
      {
        "user": "Alice",
        "score": 0.80,
        "justification": "Another explanation here."
      },
      {
        "user": "Bob",
        "score": 0.65,
        "justification": "Another explanation here."
      }
    ]
  }
]
```
Only return the JSON array. Do not include extra explanation or markdown formatting.