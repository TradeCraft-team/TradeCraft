"""
[TODO] move to tets
"""

from pyvis.network import Network

# File path to your data
file_path = './solven_tags.txt'

# Create a new interactive network graph
# Create a new interactive network graph
net = Network(height="1500px",
              width="100%",
              directed=True,
              bgcolor="#222222",
              font_color="white")

# Read the file and construct the graph for Pyvis
with open(file_path, 'r') as file:
    while True:
        key = file.readline().strip()
        if not key:
            break
        values = eval(file.readline().strip())
        net.add_node(key, label=key)
        for value in values:
            net.add_node(value, label=value)
            net.add_edge(key, value)

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
net.show("dependency_graph.html", notebook=False)
