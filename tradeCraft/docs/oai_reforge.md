# The Reforged OAI System

Please construct the system in directory './oai/', leave './oai_demo/'
a working old version, until being merged back to **dev** branch when './oai_demo/' will be deleted.


## Run

- The server: in `../tradeCraft/`, run `python run_server.py`


## Crafting Rules
- We assume the players stay in a space on undistroyable blocks. NO new resources but the existing and crafted ones will be available.
- There are undistroyable `crafting-table`, `campfire`, `furnace`, `stone-cutter`, etc. So the players need not to build them before using their functions.
- Furnace rule: use same amount of fuel as in the MC game, while crafting allow the fractional amount, but once done the non-integer fuel will be burned up.


## Existing tools
- Graph: it is an and-or-graph with recipes the and-node and all others the or-node. Nodes are stored in `Graph.node_dict` as dictionary.
- node has `parents`:
  - for recipes, a parent points to input of it,
  - for items, a parent is either a tag which it belongs to or a recipe that uses it as input,
  - for tags, a parent is a recipe that uses it as input.
- node has `children`, the inverse of parents:
  - for recipes, a child points to output of it,
  - for items, a child is a recipe that produces it as output,
  - for tags, a child is an item which belongs to it.

There are simple and flexible traversal methods, forward (on children) or backward (on parents).


## **SYSTEM DESIGN**
### Structure:
```
oai
 ┣ config
 ┃ ┣ game.py
 ┃ ┗ __init__.py
 ┣ static
 ┃ ┣ css
 ┃ ┃ ┗ bootstrap.min.css
 ┃ ┗ js
 ┃ ┃ ┣ bootstrap5.3.3.bundle.min.js
 ┃ ┃ ┣ crafting.js
 ┃ ┃ ┣ jquery-3.7.1.min.js
 ┃ ┃ ┣ math.min.js
 ┃ ┃ ┗ socket.io.min.js
 ┣ templates
 ┃ ┣ base.html
 ┃ ┣ test.html
 ┃ ┗ vanilla.html
 ┣ utils
 ┃ ┣ rand_gen.py
 ┃ ┗ __init__.py
 ┣ app.py
 ┣ central_event_redistributer.py
 ┣ dbhandler.py
 ┣ event_handler.py
 ┣ game.py
 ┣ hall.py
 ┣ player.py
 ┣ route.py
 ┗ __init__.py
```
- static: where frontend lives, js and css files, we make all necessary js packages downloaded here to avoid network problems
  - crafting.js: the mini-wiki of crafting rules, follow the AOG structure and user-friendly as much as I could. The current version only contains the items / tags / recipes which is craftable using union of user-hand-resources.

- templates: Jinja templates compatible with Flask.

- the rest: backend constructions.

### The Backend:

We try to make things simple, by handling abnormal events together,
and then try to resend the filtered messages to correct positions.

In the center, we "simulate** the game and interactions using
Game and Player instances to handle the possibly complicated
game-to-specific-client interactions. Broadcasting is simply 
handled in Game level.

**Concepts:**
- Player:
  - a player is the avatar of a client. A player is **created**
  when client builds a websocket-connection to server, RIGHT AFTER the login
  POST response (must be realized in frontend). This design avoids maintaining a lot of
  websocket connections with possibly a lot of clients visiting server without login
  (thus wish not to play at all!)
  - A player deals with all income messages, check content validity and send to player client (`_unicast` method, which is through correct `event_handler` automatically).
  - A player instance can be moved to other gamerooms / halls / mainentry, make sure they belong to only one room directly.
  - All players are registered using their unique username in `PLAYERS` defined at `app.py`.

- Game:
  - a game is the avatar of game. The Game / Player structure in a ongoing game works exactly the way as a real (offline) game. This reduces complexity of writing the logic.

  - [TODO] `_broadcast` can be used to send message to the whole game.
  - [TODO] A game / player deals with messages. To process a websocket event `game__xxx`, one must register it in `__init__.py` and implement method `on_xxx(msg)` in Game, similarly, for `player__xxx`, one must implement `on_xxx` in Player. All other message passings are handled automatically.

  - Game and Player instances knows and can access each other via `Game.token_to_player` and `Player.game`, mimicing the message sending (directly in memory~).

- Hall:
  - A hall is a game which may contain a lot of players but never start game. It may further manages several games
  and players, maintaining the ongoing games. A hall corresponds to all similar games: in the same rule including on playing (total player numbers) and on matching (seat selection on existing tables like QQ games or matching like StarCraft / DoTA ladder).

**Files with dependency:**

#### `utils/` and `config/`.
Suppose to be imported by all necessary other modules.
General utilities and config info for all other modules.


#### `__init__.py`. <- app.py, route.py, event_handlers.py
Exports `oai` as a module

Registers `GAME_EVENTS` and `NONGAME_EVENTS` which are legal event names
which will be sent to correct `event_handler`'s belonging to correct Game / MainEntry
instances. (Maybe we need an extra Hall level construction)

#### `app.py`.
Make basic definitions.
provides `app, socketio, logger`, etc.



#### `route.py`. <- app.py
Deal with all http requests, i.e., rendering all websites.



#### `event_handler.py`. <- app.py
Deals with all socketio interactions, simplifying and redirect them
into correct handlers.

Goal of this module is to filter abnormal activities
- `class EventHandler`
lives in every Game / Hall / MainEntry instances, dealing with
income messages / outgoing messages / database storage and game history
for observers to catch up. The setup is automatic and (almost) finished.


#### `player.py`. <- event_handler.py
- `class MessageHandler`
Base class for Player and Game
- `class Player(MessageHandler)`.
Basic avatar of a real player, unique up to username.

#### `game.py`. <- player.py
- `class Game(MessageHandler)`.
Contains game info, player info and implement the public game logic (crafting is private!)

- `class GameWithChatroom(Game)` Not in recent plans.

#### `hall.py` <- player.py, game.py
- `class Hall(Game)`.
Deal with Games and players waiting/joining the same type of games
- `class MainEntry(Hall)`.
Only one instance per server, main entry of everyone and distribute the processing of their messages to correct Halls / Games after `connect** event.

