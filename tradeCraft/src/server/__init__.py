"""
[TODO] the time-out mechanism on SERVER.
(in this version, they can be moved to client)
[TODO] A real reconnection mechanism:
       Plan A: frontend deal with an existing history message.
               (see handlers.EventHandler)
       Plan B: on backend, resend the messages in order using history recordings
               (to mimic what has happend from when game started)

## GAME-related EVENTS:


- player__ready_to_start
  - msg = `{"token": token,
            "username": username
            "gamename": gamename,}`
  - related responses
    - server__phase_error
    - server__player_ready_to_start
    - server__game_start


- player__submit_proposal:
  - msg = `{"token": token,
            "gamename": gamename,
               "proposal":{"self": username,
                           "partner": partner_name,
                           "offer":{},
                           "request":{}},
               "message":""}`
  - related responses:
     - server__phase_error
     - server__proposal_sent
     - server__proposal
     - server__proposal_invalid

- player__approval_or_reject
  - msg = `{"token":token,
            "gamename": gamename,
            "decision":"accept/reject",
            "message": "some sentences"}`
  - related responses
    - server__phase_error
    - server__proposal_accepted
    - server__proposal_rejected
    - server__update_all_hands?

- player__quit_game
  - msg = `{"token": token}`

- player__craft_recipe_check
  - msg = `{"token": token,
            "gamename": gamename,
            "recipe": {"input":{}, "output":{}}
              }`
  - related responses
    - server__phase_error
    - server__craft_recipe_validity

- player__craft_recipe_apply
  - msg = `{"token": token,
            "gamename": gamename,}`
  - related responses
    - server__phase_error
    - server__private_hand_change


- player__craft_done
  - msg = `{"token": token,
            "gamename": gamename,}`
  - related responses
    - server__phase_error
    - server__player_craft_done
    - server__private_hand_change
    - server__update_all_hands
    - server__start_proposal

- player__possible_recipes_from_hand
    - msg = `{gamename: gamename, token: token,
              hand:possibly other's hand(optional)}`
    - related responses
      - server__possible_recipes_from_hand

- player__item_info
    - msg = `{gamename:gamename, token:token,
              node_name: name, amount: amount}`

    - related responses
      - server__item_info

## NON-GAME-related EVENTS:


## Client to Server events:
- server__login_success
  - msg: `{}`
  - expected responses:


- server__game_over
  - msg: `{"gamename": gamename,
           "reason": "win / quit",
           "targets": [{"item":amount}],
           "win-status": [bool, win or not win]
}`
  - expected responses:

- server__phase_error
  - msg: original msg, possibly return some game status?

- server__test_response
  - msg: `{}`
  - expected responses:

- server__username_conflict
  - msg: `{}`
  - expected responses:
    - login

- server__reconnection_history
  - msg: `{"broadcast":[messages],
           "unicast":[messages]}`
  - expected responses:

- server__private_start_info
  - msg: `{"gamename": gamename,
           "index": int,
           "targets": {"item-name":{"n":int, "d":int}}}`
  - expected responses: NONE

- server__start_proposal
  - msg: `{"gamename": self.game.gamename,
           "proposer": proposer.username}`
  - expected responses:
    - player__submit_proposal

- server__proposal
  - msg: `{"gamename": gamename,
           "proposal": format_of_proposal,
           "message": str}`
  - expected responses:
    - player__approval_or_reject

- server__proposal_sent
  - msg: `{"gamename": self.game.gamename,
           "proposer": proposer.username}`
  - expected responses: NONE

- server__proposal_invalid
  - msg: `original_msg`
  - expected responses:
    - player__submit_proposal

- server__proposal_accpeted
  - msg: `{"gamename": self.game.gamename,
           "proposal": {
                        "self": proposal["self"],
                        "partner": proposal["partner"],
                        "offer": proposal["offer"],
                        "request": proposal["request"]}
           }`
  - expected responses:
    - player__possible_recipes_from_hand
    - player__craft_recipe_check
    - player__craft_done

- server__proposal_rejected
  - msg: `{"gamename": self.game.gamename,
           "proposer": proposer.username}`
  - expected responses:
    - player__possible_recipes_from_hand
    - player__craft_recipe_check
    - player__craft_done

- server__proposal_reply_message
  - msg: `{"from": username,
           "to": username,
           "message": str}`
  - expected responses: NONE

- server__craft_recipe_validity
  - msg: `{"result": bool,
           "gamename": gamename,
           "return_code": int}`
  - expected responses:
    - player__possible_recipes_from_hand
    - player__craft_recipe_apply
    - player__craft_recipe_check

- server__private_hand_change
  - msg: `{"token": self.token,
           "gamename": gamename,
           "hand": {"item_name": {n:numerator, d:denominator}}}`
  - expected responses:
    - player__possible_recipes_from_hand
    - player__craft_recipe_check
    - player__craft_done

- server__player_craft_done
  - msg: `{"gamename": the_name, "username": the_name}`
  - expected responses: NONE

- server__update_all_hands
  - msg: `{"gamename":str,
           "hands":[{"item_name":{n:int, d: int}},...]
           "player_names": [name0, name1, ...]}`
  - expected responses: NONE

- server__possible_recipes_from_hand
  - msg: `{"username": self.username,
           "gamename": self.game.gamename,
           "hand": hand,
           "recipes": possible_recipes,}`
  - expected responses:
    - player__craft_recipe_check
    - player__craft_done


- server__entry_info
- server__game_start
  - msg: `{"gamename": self.gamename,
           "player_list": [x.username for x in self.action_queue]}`
  - expected responses:
    - None


"""

from .app import (app as server_app, socketio, logger, GAMES, HALLS, PLAYERS,
                  print)
from .game import Game
from .route import *
from .hall import Hall, MainEntry

MAIN_ENTRY_HANDLER = MainEntry(num_players=100, gamename="mainEntry")

################################################################################
GAME_EVENTS = {
    "game__no_more_crafting", "player__ready_to_start",
    "player__submit_proposal", "player__approval_or_reject",
    "player__quit_game", "player__craft_recipe_check",
    "player__craft_recipe_apply", "player__craft_done",
    "player__possible_recipes_from_hand", "player__crafting_node_nonredirect",
    "player__crafting_node", "player__load_items_from_tag",
    "player__item_info", "player__gym_observation", "player__gym_action"
}

# connect (from web front emit) => on_connect (backend callback),
# auto registered in MainEntry/Game
NONGAME_EVENTS = {
    "connect", "disconnect", "connect_to_server", "test", "test_status",
    "get_halls", "enter_hall", "hall__get_games", "hall__enter_game", "login",
    "get_entry_info", "get_hall_info", "restored_proof", ""
}
# "hall__get_detailed_info"


def regularize_msg(raw: list):
    """
    Deal with multiple message styles from flask-socketio events.

    Events such as `connect` `disconnect` has None as input,
    Others are required in this application to be a dictionary itself.
    This function rewrites the messages into standard dictionary format.
    """
    match raw:
        case [] | [None]:
            return {"raw_list": raw}
        case [dict() as first, *others]:
            return {**first, "raw_list": others}
        case _:
            return {"raw_list": raw}


def create_game_event_distributer(event_name):

    def game_event_distributer(*raw):
        msg = regularize_msg(raw)
        print(f'create_game_event_distributer: {event_name}, {raw}, {msg}',
              s=12)
        gamename = msg.get("gamename", "")
        if gamename not in GAMES:
            logger.info(
                "Event %s requests a gamename %s to respond, but the game does not exist.",
                event_name, gamename)
        else:
            print("GAMES:", GAMES)
            game = GAMES[gamename]
            game.event_handler.handle(event_name, msg)

    return game_event_distributer


def create_nongame_event_distributer(event_name):

    def nongame_event_distributer(*raw):
        msg = regularize_msg(raw)
        print(f'create_nongame_event_distributer: {event_name}, {raw}, {msg}',
              s=13)
        if "hallname" not in msg:
            MAIN_ENTRY_HANDLER.event_handler.handle(event_name, msg)
        else:
            HALLS[msg['hallname']].event_handler.handle(event_name, msg)

    return nongame_event_distributer


for e_name in GAME_EVENTS:
    socketio.on(e_name)(create_game_event_distributer(e_name))
for e_name in NONGAME_EVENTS:
    socketio.on(e_name)(create_nongame_event_distributer(e_name))
