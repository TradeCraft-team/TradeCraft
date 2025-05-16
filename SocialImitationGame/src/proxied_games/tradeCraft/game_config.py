"""
"""
from ...agent_proxy.base_proxied_game import BaseGameConfig


class BasicTCGameConfig(BaseGameConfig):

    tool_docs = {
        "item_info":
        """
        Get crafting recipes related to `item_name`.
        The return is in format of a string.
        First line of return is the recipes which can output the item ({input: ingredients, output: results}),
        each item is given as `item_name:item_value` pair, where item_value is a fraction of form {n: number, d: number}
        where n s numerator and d represents denominator.
        Second line of the return is the recipes where item can be used as input.

        Args:
            messages:str = "item_name"
        """,
        "submit_proposal":
        """
        Submit proposal to game. Only available when `server__start_proposal` is received.

        Args:
        messages:dict = {"proposal":{"offer": {"item_name": amount},
                               "request": {"item_name": amount},
                               "self": your_username,
                               "partner": username_of_partner},
                   "message":"a message to partner to convince her/him."}
        }
        """,
        "approval_or_reject":
        """
        Decide to approve or reject a proposal. Only available when `server__proposal` is received.

        Args:
            messages:dict = {"decision": "`accept` or `reject`",
                     "message":"a message to partner to convince her/him."}
        """,
        "craft_done":
        """
        Done with the crafting, tell host to be ready for next trading.

        Args:
            messages:dict = {"username": your username}
        """,
        "craft_recipe_apply":
        """
        After recipe is checked and is valid, you may use this tool to apply the recipe you
        have just checked.

        Args:
            messages:dict = {"username": your username}
        """,
        "possible_recipes_from_hand":
        """
        Get the list of possible craft recipes affordable by your hand resources.

        Args:
            messages:dict = {"username": your username}
        """,
        "check_event_history":
        """
        Check all the incoming / outgoing messages.

        Args:
            messages:dict = {"username": your username}
        """,
        "craft_recipe_check":
        """
        Check whether a recipe is correct and affordable by self's resources.

        Args:
            message:dict = {"recipe":{"input": {"item_name": amount},
                               "output":  {"item_name": amount},}}
        """
    }

    pass
