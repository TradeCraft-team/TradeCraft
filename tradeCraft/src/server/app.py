"""
APP
"""

import os
import sys
import logging
import random

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from fractions import Fraction
from flask_socketio import SocketIO

from ..utils import (pr_args, gen_rand_str, process_item_dict, process_recipe,
                     process_proposal, element_conditioner, print, to_fraction,
                     lint_to_fullname, lint_to_simplename)
from ..craft_rules import Graph, Node, base_graph, FULL_GRAPH


class FractionJSONProvider(DefaultJSONProvider):

    def default(self, obj):
        print(obj)
        if isinstance(obj, Fraction):
            return {"n": obj.numerator, "d": obj.denominator}
        # Let the base class default method raise the TypeError
        return super().default(obj)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.json = FractionJSONProvider(app)

# app.json_decoder =
app.config['SECRET_KEY'] = 'k33p Ur s3cr3t in tradeCraft!'
# socketio = SocketIO(app, logger=True, engineio_logger=True)
socketio = SocketIO(app,
                    logger=True,
                    json=app.json,
                    ping_timeout=300,
                    ping_interval=20)
GAMES = {}  # consists of {"name": Game]
HALLS = {}  # consists of {"name": }
PLAYERS = {}  # {"username": Player}

# MOVE graph building to craft_rules
MC_GRAPH = FULL_GRAPH

print("tags:",
      len([
          node for node in FULL_GRAPH.node_dict.values()
          if node.node_type == "tag"
      ]),
      "recipes:",
      len([
          node for node in FULL_GRAPH.node_dict.values()
          if node.node_type == "recipe"
      ]),
      "items:",
      len([
          node for node in FULL_GRAPH.node_dict.values()
          if node.node_type == "item"
      ]),
      s=1)
# MC_GRAPH = base_graph(
#     os.path.join(os.path.dirname(os.path.dirname(__file__)), "craft_rules/"))
