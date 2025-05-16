"""
"""

from abc import ABC
from .sig_config import SIGConfig
from .headmate import BaseHeadmate, DemoHeadmate, ParallelSchedulerHeadmate


class BaseSIGModel:
    """
    """

    def __init__(self,
                 sig_config: SIGConfig | dict = None,
                 debug=False,
                 *args,
                 **kwargs):
        """
        """
        self.headmates = {}  # haddr: headmate
        self.first_speaker = ""
        self.time_step = 0
        # time step upper bound, mudify it latter
        self.max_time_step = 10

        self.config = sig_config
        self.scheduler = None
        self.cache = []

        self.debug = debug

    def load_head_mates(self):
        """
        Load all headmates
        """
        for adds, heads in self.config.Headmates:
            self.headmates[adds] = heads

    def activate_SIG(self, ):
        """
        Activate all headmates
        """

    def deactivate_SIG(self, ):
        """
        Maybe required, if we force all headmates to sleep at once.
        """

    def step(self, ):
        self.scheduler.global_time += 1
        self.time_step += 1


# class SIGModel(BaseSIGModel):
#     """
#     """
#     intrinstic_headmates = {"tool_manager": ToolManager}

#     def __init__(self, sig_config: SIGConfig | dict = None, *args, **kwargs):
#         """
#         Initialize
#         """
#         super().__init__(sig_config, *args, **kwargs)
#         self.headmates.update(self.intrinstic_headmates)


class DemoSIGModel(BaseSIGModel):
    """
    A simple model for demonstration
    Just show the workflow instead of any tool-calling
    """

    def __init__(self, sig_config: SIGConfig, debug=False, *args, **kwargs):
        """
        Initialize
        """
        super().__init__(sig_config, debug, *args, **kwargs)

        # Building up the headmate lists
        self.config = sig_config
        if sig_config.scheduler == 'parallel':
            self.scheduler = ParallelSchedulerHeadmate('demo-scheduler',
                                                       debug=debug)
        else:
            raise NotImplementedError(
                "The scheduler you assigned haven't been implemented yet....")

        if self.debug:
            print(f"Initializing the headmates for the SIG model....")
        for id, headmate in enumerate(sig_config.headmate_info):
            self.headmates[str(id)] = DemoHeadmate(haddr=str(id),
                                                   htype="demo",
                                                   scheduler=self.scheduler,
                                                   debug=debug)

            if self.debug:
                print(
                    f"Headmate {id} is initialized, with debug mode set to {debug}."
                )

    def run_SIG(self, input):

        while self.time_step < self.max_time_step:
            # arrange and send msg for time step = self.time_step
            for addr in self.headmates:
                self.headmates[addr].step(input, self.headmates)

            request = self.scheduler.step()

            if self.debug:
                # print(f"At time step {self.time_step}, the requests are:\n {request}")
                pass
            # Dict Request: [target_head_address][msg]
            if self.debug:
                print(f"DemoSIG start running...")
            # print(f"requests are {request}")

            for item in request:
                required_time = item['time']
                contents = item['request']

                if required_time == self.time_step:
                    source = contents['source']
                    target = contents['target']
                    msg = contents
                    if self.debug:
                        print(
                            f"At time step {self.time_step}, headmate {source} sends msg to headmate {target}: {msg['msg']}"
                        )
                    self.headmates[target].step(msg, self.headmates)
            self.step()
