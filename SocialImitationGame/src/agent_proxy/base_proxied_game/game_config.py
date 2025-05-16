"""
"""
from abc import ABC
from ..utils import gen_rand_str


class BaseGameConfig(ABC):

    RAND_LENGTH = 4

    def __init__(self, *args, **kwargs):
        """
        Initialize
        """
        self.server_addr = kwargs.get("addr", "localhost")
        self.server_port = kwargs.get("port", 5000)
        self.username = kwargs.get("username", self._generate_username())

    def _generate_username(self):
        """
        Generate random username
        """
        return f"base_agent_proxy_{gen_rand_str(self.RAND_LENGTH)}"

    def __getitem__(self, name):
        match name:
            case "username":
                return self.username

