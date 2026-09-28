import networkx as nx
from typing import List, Dict, Any, Generator
from backend.schema import TraversalPathEvidence

class GraphTraversal:
    def __init__(self, G: nx.MultiDiGraph):
        self.G = G

    def bfs_shortest_path(self, source: str, target: str, directed: bool = True) -> List[str]:
        """
        Finds the shortest topological path between source and target using BFS.
        If directed=True, follows strict topological arrows (e.g., IP -> TX, Address -> TX).
        Note: A directed path like IP -> TX -> Address is explicitly an investigative/network-observation path.
        It NEVER implies IP ownership of the address, transaction origin, or fund ownership.
        If directed=False, allows forensic backtracking (using an undirected view).
        """
        graph_to_search = self.G if directed else self.G.to_undirected(as_view=True)
        
        try:
            return nx.shortest_path(graph_to_search, source=source, target=target)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def bfs_edges(self, source: str, depth_limit: int = None, directed: bool = True) -> List[tuple]:
        """
        Yields edges in a breadth-first search order from the source node.
        Returns a list of tuples (u, v) representing the traversal tree.
        """
        if not self.G.has_node(source):
            return []
            
        graph_to_search = self.G if directed else self.G.to_undirected(as_view=True)
        return list(nx.bfs_edges(graph_to_search, source=source, depth_limit=depth_limit))

    def dfs_edges(self, source: str, depth_limit: int = None, directed: bool = True) -> List[tuple]:
        """
        Yields edges in a depth-first search order from the source node.
        Returns a list of tuples (u, v) representing the traversal tree.
        """
        if not self.G.has_node(source):
            return []
            
        graph_to_search = self.G if directed else self.G.to_undirected(as_view=True)
        return list(nx.dfs_edges(graph_to_search, source=source, depth_limit=depth_limit))

    def extract_path_evidence(self, path: List[str]) -> List[TraversalPathEvidence]:
        """
        Given a sequence of nodes representing a path, extracts the underlying edge evidence 
        and attributes (provenance, amounts, edge types) for investigator review.
        """
        evidence = []
        if len(path) < 2:
            return evidence
            
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            
            # Since it's a MultiDiGraph, there could be multiple edges between u and v.
            # We extract all of them. If the path was found on an undirected view, 
            # the edge might actually be v -> u in the directed graph.
            edge_data = self.G.get_edge_data(u, v)
            if edge_data is None:
                # Check reverse direction
                edge_data = self.G.get_edge_data(v, u)
                if edge_data:
                    for key, data in edge_data.items():
                        evidence.append(TraversalPathEvidence(
                            source=v,  # preserve exact original directed origin
                            target=u,
                            edge_type=data.get('edge_type'),
                            network_role=data.get('network_role'),
                            amount=data.get('amount'),
                            timestamp=data.get('timestamp'),
                            run_id=data.get('run_id'),
                            source_file=data.get('source_file'),
                            source_row=data.get('source_row')
                        ))
            else:
                for key, data in edge_data.items():
                    evidence.append(TraversalPathEvidence(
                        source=u,
                        target=v,
                        edge_type=data.get('edge_type'),
                        network_role=data.get('network_role'),
                        amount=data.get('amount'),
                        timestamp=data.get('timestamp'),
                        run_id=data.get('run_id'),
                        source_file=data.get('source_file'),
                        source_row=data.get('source_row')
                    ))
                    
        return evidence
