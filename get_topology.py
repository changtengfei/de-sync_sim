import random
import json

# Create a sample network topology data with 10 nodes
num_nodes = 2
network_topology = {}

# Generate network data
for node_id in range(num_nodes):
    # Each node will have between 1 to 3 neighbors randomly selected
    num_neighbors = random.randint(1, 3)
    neighbors = random.sample([n for n in range(0, num_nodes) if n != node_id], num_neighbors)
    
    # Create a dictionary of neighbors with link quality
    link_quality = {neighbor: round(random.random(), 2) for neighbor in neighbors}
    network_topology[node_id] = link_quality

with open("topology.json", 'w') as json_file:
    json.dump(network_topology, json_file, indent=4)
