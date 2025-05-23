## Evaluation Item: Adaptability

You are asked to evaluate how well the player demonstrates **adaptability** throughout the game.

Adaptability is the ability to adjust strategies and decisions in response to changing game conditions, including new trades, resources, or partner behaviors.

Please compare **both players** based on the game log. For each player, assign a **score from 0.0 to 1.0**, where:
- 1.0 = consistently demonstrated strong and consistent adaptability
- 0.0 = no signs of adaptability or completely ineffective behavior
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