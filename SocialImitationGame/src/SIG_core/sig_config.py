"""
Some compact format which could summarize
a SIG structure / Headmate structure.
"""


class SIGConfig:
    """
    SIG config class. Construct from config.
    """

    def __init__(self, ):
        """
        Parameters
        ----------
        : 


        Returns
        -------
        out : 
        """
        self.initial_headmates = {}
        self.static_headmates = {}
        self.structural_managers = {}
        self.permissions = {}  # authorizations?


        self.worker_list = []

        self.scheduler = None
        self.headmate_info = []

