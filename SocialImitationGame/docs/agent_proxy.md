# Agent Proxy

This module provides interface to communicate with environment, the server, via websocket messages. A proxied game interface.



## Proxied Game
It is a system consist of sevearl base classes.
Together, they provide necessary information about game message processing methods together with translating rules.

There might be multiple ways to define the dynamics in a turn-based model of the game, meanwhile, there are also multiple ways to translate the messages for the use of SIG system. It is obvious that one may choose one dynamics intepretation strategy, and choose one translating strategy to form their own Proxied Game.


## Design

### File Structure
```
fsm.py

BaseFsm
|- ToolFsm
|- TurnBasedFsm
|
|- [All Others]

proxy.py
BaseProxy
|- ToolProxy
|- TurnBasedProxy
|
|- [All Others]
```

### Procedure
```
Proxy Instantiate: proxy
|
|- proxy.run
   |
   FSM initialte: proxy.fsm (aka fsm)
   |
   await fsm.connect
   |
   await fsm.sio.connect
   |
   fsm.register_sio_callbacks
   |
   fsm.load_game_dynamics

|
await fsm.game_dynamics.pregame(fsm.sio, etc)
|
|- Customized login / entergame behavoirs
|
fsm.run_game
|
...
|
fsm.end_game
```
