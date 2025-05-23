## Evaluation Item: Cooperation

You are asked to evaluate how well the player demonstrates **cooperation** throughout the game.

Cooperation refers to the player's willingness and ability to work toward mutual benefit with others, including fair trades and shared progress.

Please compare **both players** based on the game log. For each player, assign a **score from 0.0 to 1.0**, where:
- 1.0 = consistently demonstrated strong and consistent cooperation
- 0.0 = no signs of cooperation or completely ineffective behavior
- Intermediate values reflect partial effectiveness

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