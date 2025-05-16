"""
[TODO] move to test
"""

import networkx as nx
import matplotlib.pyplot as plt

# File path
file_path = './solven_tags.txt'

# Create a directed graph
G = nx.DiGraph()

# Read the file and construct the graph
with open(file_path, 'r') as file:
    while True:
        key = file.readline().strip()
        if not key:
            break
        values = eval(file.readline().strip())
        for value in values:
            G.add_edge(key, value)

# Draw the graph
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G, seed=42)  # Positions for all nodes
nx.draw(G,
        pos,
        with_labels=True,
        node_color='lightblue',
        edge_color='gray',
        node_size=5000,
        font_size=9)
plt.title('Dependency Graph Visualization')
plt.show()
