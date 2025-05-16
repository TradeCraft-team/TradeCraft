"""
Wrappers.

General purposed functional wrappers.
"""
import asyncio
import gymnasium
from gymnasium import Wrapper, Env
from langchain.tools import tool, StructuredTool
from makefun import wraps
from typing import Callable, Optional, Type, Dict
from pydantic import BaseModel
from .utils import print


class SynchronizeWrapper(Wrapper):
    """
    A wrapper which makes async into sync.
    """
    metadata = {"async": True, "render_modes": []}

    def __init__(self, base_env: Env):
        """
        Initialize
        """
        self.base_env = base_env
        super().__init__(base_env)
        setattr(self.__class__, "areset", super().reset)
        setattr(self.__class__, "astep", super().step)
        setattr(self.__class__, "aclose", super().close)

    def reset(self, *args, **kwargs):
        return asyncio.run(self.areset(*args, **kwargs))

    def step(self, action, *args, **kwargs):
        return asyncio.run(self.astep(action, *args, **kwargs))

    def close(self):
        return asyncio.run(self.aclose())


import inspect


def mark_tool_gen():
    """
    Use closure to mark tools. See doc of `TooledWrapper`.

    ([NOTE] move to TooledWrapper as static method?)
    """

    marked_tools = {"system": []}

    def outer(*args, **kwargs):
        """
        The mark_tool classmethod used outside
        """

        # print("MARK_TOOLS: ARGS =", args, s=1)
        nonlocal marked_tools
        tool_type = "system"

        marked_tools_ = kwargs.pop("marked_tools", marked_tools)

        def wrapped(tool_type, **kwargs):
            """
            Generate inner decorator, accepts extra arguments for inner one.
            """

            def inner_decorator(method):
                """
                Inner decorator

                [HACK]: set __name__, __doc__, ??? exactly
                the same as in the original method. For langchain use.
                """
                nonlocal marked_tools_, tool_type, kwargs
                if tool_type not in marked_tools_:
                    marked_tools_[tool_type] = []

                marked_tools_[tool_type].append({
                    "name": method.__name__,
                    **kwargs
                })
                return method

            return inner_decorator

        match args:
            case (func, ) if callable(func):
                tool_type = "system"
                kwargs["is_async"] = kwargs.get(
                    "is_async", inspect.iscoroutinefunction(func))
                return wrapped(tool_type, **kwargs)(func)

            case (str() as tool_type, func) if callable(func):
                kwargs["is_async"] = kwargs.get(
                    "is_async", inspect.iscoroutinefunction(func))
                return wrapped(tool_type, **kwargs)(func)

            case (str() as tool_type, ):
                kwargs["is_async"] = kwargs.get("is_async", True)
                return wrapped(tool_type, **kwargs)

            case _:
                raise Exception(
                    "Tool Marking:: Not in correct calling format.")

    return outer, marked_tools


def method_to_func(instance, method):
    """
    Converts an instance method to a standalone function with the
    instance bound to it.

    See doc of `TooledWrapper`.
    """
    # print(help(method))

    @wraps(method, remove_args="self")
    def func(*args, **kwargs):
        return method(self=instance, *args, **kwargs)

    return func


class TooledWrapper(Wrapper):
    """
    Register tools.

    How it works:
    -------------
    As Langchain does not support registering class methods as tools,
    `method(self, *args, **args)` must be turned into `f_method(*args, **args)`
    in a function closure so that `self` could be added when it is called.
    To achieve this, the tool registration in langchain must happen in Runtime.

    Here we choose the TooledWrapper instantiation time, and expose
    `register_tools()` for a dynamic registration possibility (adding it into
    Agent is a problem though).

    `method_to_func` above works by turning method to func.
    `mark_tool_gen` provides a closure storing tool marking wrapper and
    tool mark storage, so that when register_tools() is called, the marked
    tools will be registered.
        `mark_tool_gen` returns a decorator func: `mark_tool` saved as class
            method of TooledWrapper (and any subclasses, manually). mark_tool
            accepts a tag and decorates a method, marking it in marked_tools,
        `marked_tools` is a dict, storing the marked-tool names in their tags.


    """
    metadata = {"render_modes": []}
    mark_tool, marked_tools = mark_tool_gen()

    def __init__(self, base_env: Env):
        self.tools_ = {}
        self.base_env = base_env
        super().__init__(base_env)
        self.__class__.metadata["async"] = base_env.metadata["async"]
        self.register_tools()

    def get_tools(self, refresh: bool = False):
        """
        Get registered tools.

        If refresh==True, re-register all marked tools.
        """

        if refresh:
            self.tools_ = {}
            self.register_tools()
        return self.tools_

    @property
    def tools(self):
        return list(self.get_tools().values())

    def register_tool(
            self,
            t,
            is_async: bool = True,
            return_direct: bool = False,
            args_schema: Optional[Type[BaseModel]] = None,
            infer_schema: bool = True,
            tags: Optional[tuple[str]] = None,
            handle_tool_errors: bool | Callable = True) -> StructuredTool:
        """
        Making tool-calling work.


        Parameters
        ----------
        *args: Either the name of the tool and the method, or just the method.
        return_direct (bool): If True, the tool will directly return the
                result instead of continuing the agent loop.
        args_schema (Optional[Type[BaseModel]]): An optional Pydantic schema
                to enforce the argument structure.
        infer_schema (bool): If True, infer the argument schema from the
                function's signature.
        tags (Optional[list[str]]): A list of tags for categorizing or
                labeling the tool.
        handle_tool_errors (bool | Callable): Indicate whether raise errors or
                return exceptions as string. Pass a callalble to handle errors
                in a custom way.

        Return
        ------
        StructuredTool: A wrapped tool ready to be used by LangChain agents.

        Examples
        --------
        ```python
        # Inside definition of a class inheriting from Toolkit
        @register_tool
        def some_function(self, input_str: str) -> str:
            \"\"\"A simple example function\"\"\"
            return f"Processed {input_str}"

        @register_tool
        def another_function(self, input_str: str) -> str:
            \"\"\"Another function with a custom tool name\"\"\"
            return f"Custom processed {input_str}"
        ```
        """
        if is_async:
            wrapped = StructuredTool.from_function(
                coroutine=method_to_func(self, t),
                name=t.__name__,
                description=t.__doc__,
                return_direct=return_direct,
                # parse_docstring=True,
            )
        else:
            wrapped = StructuredTool.from_function(
                func=method_to_func(self, t),
                name=t.__name__,
                description=t.__doc__,
                return_direct=return_direct,
                # parse_docstring=True,
            )
        wrapped.tags = tags
        self.tools_[t.__name__] = wrapped
        return wrapped

    def register_tools(self,
                       is_async: dict[str, bool] = {},
                       return_direct: dict[str, bool] = {},
                       args_schema: Optional[dict[str, Type[BaseModel]]] = {},
                       infer_schema: dict[str, bool] = {},
                       tags: Optional[Dict[str, tuple[str]]] = {},
                       handle_tool_errors: dict[str, bool | Callable] = {}):
        """
        Register all tools as langchain-tools.

        **Runtime** logic: use langchain.tools.tool decorate all
        marked methods.

        Auto-run at the end of instantiation (__init__).
        """
        print(self.marked_tools)
        for tag, tools in self.marked_tools.items():
            for t in tools:
                _t = t["name"]
                if _t in self.tools_:
                    continue
                self.register_tool(getattr(self.__class__, _t),
                                   t.get("is_async", True),
                                   return_direct.get(_t, False),
                                   args_schema.get(_t),
                                   infer_schema.get(_t, True),
                                   tags.get(_t, tag),
                                   handle_tool_errors.get(_t, True))

    def flatten(self, nested: dict, tag: str):
        """
        Flatten the nested dictionary.

        Simplify the function call generation difficulty.
        """
