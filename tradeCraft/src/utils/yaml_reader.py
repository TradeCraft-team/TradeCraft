"""
Utils :: config YAML reader
"""

import os
import argparse
import yaml
from pathlib import Path


def boolean_string(s):
    s = s.lower()
    if s not in {'false', 'true'}:
        raise ValueError(f'{s} is not a valid boolean string')
    return s == 'true'


def parse_args():
    """
    Initialize default arguments with yaml and renew values with input arguments.
    """

    default_config_file = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '../../settings.yaml'))
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file',
                        help="configuration file *.yml",
                        type=str,
                        required=False,
                        default=default_config_file)

    args, remaining_argv = parser.parse_known_args()

    opt = yaml.load(open(args.config_file, encoding="utf8"),
                    Loader=yaml.FullLoader)
    for key in opt.keys():
        # print(opt[key])
        if type(opt[key]) is dict:
            group = parser.add_argument_group(key)
            # print(key)
            for sub_key in opt[key].keys():
                assert type(
                    opt[key][sub_key]
                ) is not dict, "Config only accepts two-level of arguments"
                if type(opt[key][sub_key]) is bool:
                    group.add_argument('--' + key + '.' + sub_key,
                                       default=opt[key][sub_key],
                                       type=boolean_string)
                else:
                    group.add_argument('--' + key + '.' + sub_key,
                                       default=opt[key][sub_key],
                                       type=type(opt[key][sub_key]))
        else:
            if type(opt[key]) is bool:
                parser.add_argument('--' + key,
                                    default=opt[key],
                                    type=boolean_string)
            else:
                parser.add_argument('--' + key,
                                    default=opt[key],
                                    type=type(opt[key]))

    parser.add_argument('--fast_port',
                        help="fast way to assign port to listen",
                        type=int,
                        required=False,
                        default=8001)
    args = parser.parse_args(remaining_argv)
    return vars(args)


pr_args = parse_args()
