# How does a Social Imitation Game run: The Pipeline


## Components

### The SIG-player

A single Social imitation game could include many players, either human beings or AI models.

They will receive processed observation info from the game environment(server), think thoroughly, and make decisions & take actions by calling different pre-defined tools. 



### The Proxy

Each player owns its proxy, which receives the 'JSON information from the environment(game server).
The proxy will store messages from the server and decide whether the info should be sent to its master(player)

Also, the proxy is in charge of delivering players' decisions (calling tools) to the server. 


### The Game Server
The game server will respond to the tool-calling info and return the calling result to the proxy in the form of: [event, message]



## Procedure

The whole process can be considered as a loop: 
1) SIG-player takes action by calling a tool, it sends the [toolname, tool-message] to its proxy
2) Proxy deliver the calling info to the server
3) The server handles the calling request and returns info to the proxy
4) The proxy will receive info from the server, and rewrite it in natural language, but won't send it to the player directly, instead, the processed info will be appended into the 'unread-message' stack of the proxy. 
5) The proxy keeps monitoring info from the server, once it gets the wanted one, sent all information in the 'unread-message stack' to the SIG-player. 



To be continued...