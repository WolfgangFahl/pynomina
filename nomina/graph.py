"""
Created on 2024-10-09

@author: wf
"""

import json

import networkx as nx


class Graph:
    """
    graph handling library
    """

    def __init__(self):
        self.graph = nx.Graph()

    def add_nodes_from_json(self, file_name, file_content):
        """
        Add nodes from JSON data to the graph
        """
        table_name = file_name.split(".")[0]  # Remove the .json extension

        for line in file_content:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    json_data = json.loads(line)
                    self.add_node(table_name, json_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON object in file {file_name}: {e}")

    def add_node(self, table_name, data):
        """
        Add a single node to the graph
        """
        node_id = data.get("id", str(len(self.graph)))
        self.graph.add_node(node_id, type=table_name, **data)

    def dump(self, node_types=None, limit: int = 10):
        """
        Dump the content of the graph for investigation.

        Args:
            node_types (list): List of node types to dump. If None, dump all types.
            limit (int): Maximum number of nodes to dump for each node type. Default is 10.
        """
        self._print_graph_summary()
        node_types = self._get_node_types_to_dump(node_types)
        self._dump_nodes(node_types, limit)
        self._dump_edges(limit)

    def _print_graph_summary(self):
        print(f"Total nodes in graph: {len(self.graph.nodes)}")
        print(f"Total edges in graph: {len(self.graph.edges)}")

        all_node_types = set(
            data.get("type", "Unknown") for _, data in self.graph.nodes(data=True)
        )
        print(f"All node types: {all_node_types}")

    def _get_node_types_to_dump(self, requested_types):
        all_node_types = set(
            data.get("type", "Unknown") for _, data in self.graph.nodes(data=True)
        )
        if requested_types is None:
            return all_node_types
        return (
            set(requested_types) & all_node_types
        )  # Ensure we only dump existing types

    def _dump_nodes(self, node_types, limit):
        print(f"Dumping node types: {node_types}")
        for node_type in node_types:
            self._dump_nodes_of_type(node_type, limit)

    def _dump_nodes_of_type(self, node_type, limit):
        print(f"\nDumping up to {limit} nodes of type '{node_type}':")
        count = 0
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == node_type:
                self._print_node(node, data)
                count += 1
                if count >= limit:
                    break
        if count >= limit:
            remaining = (
                sum(
                    1
                    for _, d in self.graph.nodes(data=True)
                    if d.get("type") == node_type
                )
                - limit
            )
            print(f"  ... and {remaining} more")

    def _print_node(self, node, data):
        print(f"  Node: {node}")
        for key, value in data.items():
            if key != "type":
                print(f"    {key}: {value}")

    def _dump_edges(self, limit):
        if self.graph.edges:
            print("\nSample of edges:")
            for i, (u, v, data) in enumerate(self.graph.edges(data=True)):
                print(f"  Edge {i}: {u} -> {v}")
                for key, value in data.items():
                    print(f"    {key}: {value}")
                if i >= limit - 1:
                    remaining = len(self.graph.edges) - limit
                    if remaining > 0:
                        print(f"  ... and {remaining} more")
                    break
        else:
            print("\nNo edges in the graph.")
