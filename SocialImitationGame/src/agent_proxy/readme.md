# The Agent Proxy

Agent Proxy is an alternative interface with server instead of webui.

It is useful for funtinality test or chain-hook with LLM instances.


## Modules
- Proxies: Entries of Proxy
- Fsm's: Finite State Machines controlling communications with server (may rename in the future)


## Proxies
Usage:

Proxy is a class for interface proxy creation, destroy and operation.

Proxies uses Fsm module (see Section FSM's) to handle the game process.
Proxies should have an interface to LLM's in a quite natural way. ([TODO] UNIFY it)

```
Proxy
|
|-- LLM Proxy
|   |
|   |-- DummyProxy
|
|-- ToolProxy
|
|-- Llama3Proxy
|
|-- Auto2PlayerFillerProxy
```
### Proxy
Base class

### LLMProxy / DummyProxy
Implements a basic version which can connect to LLM via API.

### ToolProxy
Tool version, which means all controls of the game via ToolProxy are provided as tool functions
which are compatible with `langchain` tool-using module. Here one can design the agent as a purely
tool-using expert, the detailed control are defined in `ToolFsm` via a transition dictionary which
is customizable.

#### ToolProxy快速上手

这个版本的语言模型proxy在文件夹tradeCraft/agent_proxy里。跑起服务器之后可以用proxy连进去，需要另一个人进去配合，可以使用浏览器访问http://localhost:5000/new。有两个入口文件可以用。一个是tests/test_tool_proxy.py。另一个是run_agent.py

test_tool_proxy.py。这个文件是工具化接口转接命令行打字操作的测试入口，可以先在这里打字玩一局（记得先去看好后面要说的输入输出翻译部分，不然这里打字真的寸步难行）
这里使用工具的格式是：
```
tool_name | tool_args
```
tool_name是工具名，tool_args是工具参数。

tool工作的原理已经用元编程的方式统一了。服务器发送给客户端的事件名都是server__xxx的形式，客户端发送给服务器的是player__xxx的形式。
ToolFsm管理着socket连接，对于server__xxx消息，都有一个默认的记录到未读消息list，并在相应事件的缓存里写入的行为。
由于ToolProxy使用工具调用模式，服务器通信类工具需要从llm处拿到工具名（函数名）和参数表，然后把经过proxy处理过之后的参数表（JSON）传输给服务器，并等待服务器回应。
确定服务器给出对这个工具的回复之后，把回复涉及的所有消息经由proxy.generate_prompt处理后作为工具的返回值送还给llm。

具体地说，ToolFsm中的行为由类参数tool_dynamics以字典形式给出，tool_dynamics的key是形如player__xxx的外发消息名，value是形如server__xxx的接收消息名。当ToolFsm发送player__xxx消息后，会根据tool_dynamics的映射关系，清除监听对应的目标消息server__xxx对应的缓存，并在缓存被写入（即发现服务器返回了对应于player__xxx的消息，应该作为工具的返回值）时，把缓存内容作为工具的返回值送还给llm。
如果希望接入一款不同的基于socketio的测试环境，完全可以在调通自动登录流程后，通过自定义调整ToolFsm.tool_dynamics的数据结构的方法完整定义工具何时返回，从而实现状态转换。配置方便很多。


## FSM's
```
BaseFsm
|
|-- ClientFsm
|
|-- ToolFsm
|
|-- Auto2PlayerFillerFsm
```

### ToolFsm
