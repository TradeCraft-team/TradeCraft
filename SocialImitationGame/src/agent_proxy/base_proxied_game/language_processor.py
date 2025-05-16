"""
Base Language Processor
"""

from abc import ABC, abstractmethod
from datetime import datetime as dt

from ...utils.dbhandler import dbs, IS_CONN, save_log_to_db
from ..utils import print


class BaseLanguageProcessor(ABC):
    """
    """
    db_col = None

    def __init__(self, *args, **kwargs):
        """
        Initialize
        """

    def generate_prompt(self, event: str, *msg_lists, **kwargs) -> str:
        """
        Generate prompt for Language (SIG) Agent
        """
        msg_str = '\n'.join(str(msg_lists))
        return f"EVENT: {event}\nMESSAGE_LIST:\n{msg_str}\n"

    def parse_answer(self, answer: str, event: str = None, **kwargs) -> dict:
        """
        Parse the answer from Language (SIG) Agent
        """

        return answer

    @classmethod
    def log_output_to_db(cls, method):
        """
        Log output to DB
        """

        def inner(self, event: str, *args, **kwargs):
            """
            Inner part
            """
            output = method(self, event, *args, **kwargs)

            msg = {
                "type": "prompt",
                "player": self.user_name,
                "game": self.gamename,
                "msg": output,
                "time": dt.now().strftime("%Y%m%d-%H%M%S-%f")
            }
            collection = f"Duo_{self.gamename}_{self.user_name}"
            save_log_to_db(collection, msg)
            return output

        return inner

    @classmethod
    def log_input_to_db(cls, method):
        """
        Log output to DB
        """

        def inner(self, answer: str, event: str = "", **kwargs):
            """
            Inner part
            """
            output = method(self, answer, event=event, **kwargs)

            msg = {
                "type": "model_generation",
                "player": self.user_name,
                "game": self.gamename,
                "msg": answer,
                "time": dt.now().strftime("%Y%m%d-%H%M%S-%f")
            }
            collection = f"Duo_{self.gamename}_{self.user_name}"
            save_log_to_db(collection, msg)
            return output

        return inner
