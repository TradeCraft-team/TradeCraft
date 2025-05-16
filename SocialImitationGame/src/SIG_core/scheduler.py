"""
[TODO] Perhaps all of these kind of modules should be subclasses of Headmate.
"""
import json
from queue import Queue
from abc import ABC
# from .utils import *
from .sig_config import SIGConfig


class BaseProcessor(ABC):
    """
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize
        """

        self.workers = []

    def activate_next(self):
        pass  # must be implemented


class FIFOProcessor(BaseProcessor):
    """
    Maintain a message queue, every earliest internal
    message can activate the receiver.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize
        """
        super.__init__(*args, **kwargs):

        self.message_queue = Queue()

    def activate_next(self):
        """
        """
        if len(self.message_queue)>0:
            message = self.message_queue.get()




class ClockProcessor(BaseProcessor):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize

        Activate all headmates, read messages / send messages (receive next round)
        and proceed.
        """
        super.__init__(*args, **kwargs):

        self.clock = 0
        self.message_list = []


