"""
Finite state machine
"""

from copy import deepcopy

class FiniteStateMachine:


    def __init__(self, configuration: dict):
        """
        Initialize.
        configuration:

        configuration: dict, describes the states and dynamics of state changes.
        e.g., {1:{"a1":2, "a2":3},
               2:{"b1":2, "b2":3},
               3:{"c1":3}}
        """
        self.states = list(configuration.keys())
        self.dynamics = deepcopy(configuration)



    def _next(self, action):
        """
        
        """
        

