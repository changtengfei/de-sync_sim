import random
import json

def generate_network_topology(num_nodes, max_neighbors):
    # Ensure each node has a symmetric link quality to its neighbors
    topology = {i: {} for i in range(num_nodes)}

    for node in range(num_nodes):
        # Randomly decide how many neighbors this node will have (at least one)
        num_neighbors = random.randint(1, min(max_neighbors, num_nodes - 1))
        neighbors = random.sample([n for n in range(num_nodes) if n != node], num_neighbors)

        for neighbor in neighbors:
            # Assign a random link quality
            link_quality = round(random.uniform(0, 1), 2)
            topology[node][neighbor] = link_quality
            topology[neighbor][node] = link_quality  # Ensure symmetry

    return topology

# Example usage
num_nodes       = 5  # Number of nodes in the network
max_neighbors   = 1  # Maximum neighbors a node can have
json_topology   = generate_network_topology(num_nodes, max_neighbors)

with open("topology_{0}_{1}.json".format(num_nodes, max_neighbors), 'w') as json_file:
    json.dump(json_topology, json_file, indent=4)
