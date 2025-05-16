from pyvis.network import Network

OPTIONS = """
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
"""

COLOR = {"tag": "#00ff1e", "item": "#ee9999", "recipe": "#8888ee"}


def viz_net(node_dict: dict, graph_name: str = "graph.html"):

    net = Network(height="1500px",
                  width="100%",
                  directed=True,
                  bgcolor="#222222",
                  font_color="white")

    for name, node in node_dict.items():
        net.add_node(name, label=name, color=COLOR[node.node_type])
        # for child, weight in node.children.items():
        #     net.add_node(child.node_name, label=name)

    for name, node in node_dict.items():
        # node.fully_reconstruct(node_dict)
        for child, weight in node.children.items():
            # net.add_edge(name, child.node_name, weight=weight)
            net.add_edge(child.node_name, name, weight=weight)

    net.set_options(options=OPTIONS)
    net.show(graph_name, notebook=False)
    return net
