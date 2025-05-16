"""
Headmate Recruiter
"""
from . import BaseHeadmate

class Recruiter(BaseHeadmate):


    """
    """
    def __init__(self, haddr, htype, *args, **kwargs):
        """
        Initialize
        """
        super().__init__(haddr, htype, *args, **kwargs)


    def recruite(self, config) -> BaseHeadmate:
        """
        """

