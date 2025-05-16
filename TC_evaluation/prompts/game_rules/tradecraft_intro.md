# About *tradeCraft*

The game *tradeCraft* is a multiplayer, turn-based strategy game. In the game
there are several players, each holding a hand of items in MineCraft style
which is visible to all players, and has their own **secret** target item to obtain.
In **trading** phase, the items could be exchanged between two players in any
ratio if both agrees to exchange. And in **crafting** phase, new items could be
crafted from items in hand by each player following strictly the recipes of MineCraft.

## Procedure
The game is turn-based. The player take turns to play as proposer. 
We emphasize that all players should adhear strictly to the procedures. Otherwise their action would trigger a **phase error**. 

A turn is made up of the following 3 steps **strictly** in the following order*:
1. Proposer makes a trading proposal at the begining of the turn, assigning
  - which player (**self**) is proposing,
  - which player (**partner**) to trade with,
  - the set of items **offer** to the partner,
  - the set of items **request** from the partner,
  - a *text message* sent to the partner.
   Then the proposal is sent to the partner.
2. When receiving the proposal, the **partner** must decide to accept it or
   reject it. A *text message* is allowed to send back to proposer secretly.
   If accepted, the items in the proposal is traded, and the item change is
   shown to everyone, otherwise, only `proposer's proposal is rejected` can
   be seen by others.
3. When the proposal are handled(either accepted or rejected), all players craft items in the following procedure:
  - Send to server a recipe in terms of `{"input":{item:amount}, "output":{item:amount}}`,
    to **check** whether the recipe is eligible to craft or not. A recipe is
    eligible if it is a valid recipe with exact amount of items (allow to use
    fractions!) and player's hand has sufficient amount of each input item.
    Suppose that you have crafting table, stone-cutting table, furnace, brewing
    stand, campfire, etc. to help you craft, but you still need fuel when using
    furnace.
  - Player should always **craft_recipe_check** before they try to **craft_recipe_apply**. If the recipe is checked   **correct and feasible**, player can **apply** the recipe. The player
    can choose to check another recipe without applying previous one, in which
    case the hand is not changed at all. If the recipe were not valid, the
    player cannot apply it. 

  - In the craft phase, you don't necessarily have to perform crafting. If there is nothing to craft under the current stage, player can choose to stop the crafting phase by calling **craft_done**. And if there is any fractional item left in hand, non interger part is discarded.

  The next proposal turn won't begin until **all players** done with crafting.
  The results of each player's crafting is revealed only when the turn ends.

## Goal
In the game, each player has a **target item** which is unknown by others. The
goal is to use the items in hand, together with the items traded from others,
to craft the target item. System checks each player's hand after all players
finish crafting. If any player has target item in hand, the game is over. After
certain turns, if no players won, the game ends with a `all lose` result.

