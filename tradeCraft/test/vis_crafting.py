"""
Load the crafting graph and visualize.
[TODO] move to test
"""
import pickle
from pyvis.network import Network
from graph import Graph

# File path to your data
file_path = './temp_data/graph_structure.pkl'

# Create a new interactive network graph
# Create a new interactive network graph
net = Network(height="1500px",
              width="100%",
              directed=True,
              bgcolor="#222222",
              font_color="white")

COLOR = {"tag": "#00ff1e", "item": "#ee9999", "recipe": "#8888ee"}
# Read the file and construct the graph for Pyvis
with open(file_path, 'rb') as fptr:
    # node_dict = pickle.load(fptr)
    graph = Graph()
    graph.load_pickle(file_path)
    node_dict = graph.node_dict
    for name, node in node_dict.items():
        net.add_node(name, label=name, color=COLOR[node.node_type])

    for name, node in node_dict.items():
        for child, weight in node.children.items():
            net.add_edge(child, name, weight=weight)

# Set options for the network
net.set_options("""
var options = {
  "nodes": {
    "font": {
      "size": 12
    }
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "smooth": false
  },
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -100,
      "centralGravity": 0.01,
      "springLength": 100,
      "springConstant": 0.08
    },
    "maxVelocity": 50,
    "minVelocity": 0.1,
    "solver": "forceAtlas2Based",
    "timestep": 0.35,
    "stabilization": {
      "enabled": true,
      "iterations": 1000
    }
  }
}
""")

# Generate and display the interactive graph in an HTML file
net.show("./temp_data/dependency_graph.html", notebook=False)
