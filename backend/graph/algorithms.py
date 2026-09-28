import networkx as nx
from typing import Dict, Any, Tuple, List
from decimal import Decimal

class GraphAlgorithms:
    def __init__(self, G: nx.MultiDiGraph):
        self.G = G

    def compute_degree_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Computes in-degree, out-degree, and total degree for all nodes.
        Computes weighted in/out degree by summing Decimal amounts safely.
        """
        metrics = {}
        for node in self.G.nodes():
            metrics[node] = {
                "in_degree": self.G.in_degree(node),
                "out_degree": self.G.out_degree(node),
                "total_degree": self.G.degree(node),
                "weighted_in_degree": Decimal('0'),
                "weighted_out_degree": Decimal('0')
            }

        # Safely compute weighted degrees using Decimal
        for u, v, data in self.G.edges(data=True):
            amount = data.get('amount')
            if amount is not None:
                if isinstance(amount, Decimal):
                    val = amount
                else:
                    val = Decimal(str(amount))
                    
                metrics[v]["weighted_in_degree"] += val
                metrics[u]["weighted_out_degree"] += val

        for node in metrics:
            metrics[node]["weighted_total_degree"] = metrics[node]["weighted_in_degree"] + metrics[node]["weighted_out_degree"]

        return metrics

    def compute_betweenness_centrality(self, k: int = None, seed: int = 42) -> Dict[str, float]:
        """
        Computes betweenness centrality.
        - If k=None: exact betweenness centrality is computed.
        - If k=<integer>: sampled/approximate betweenness is computed.
        - If k >= number of nodes: NetworkX treats it as an exact calculation (uses all nodes).
        - If k is invalid (e.g. negative or wrong type): NetworkX raises ValueError.
        
        The `seed=42` parameter ONLY controls sampling deterministically. It does NOT make 
        exact betweenness "mathematically reproducible" (exact is inherently reproducible).
        
        Projection semantics:
        Because the foundational graph is a MultiDiGraph, `nx.DiGraph(self.G)` silently collapses
        parallel edges between the same two nodes into a single unweighted directed edge.
        For example:
        - Parallel INPUT/OUTPUT edges between the same address and TX are collapsed into one edge.
        - Multiple PROPAGATED edges (e.g., from multiple observations) are collapsed into one.
        This is intentional for betweenness, as we measure topological bottlenecks, not 
        volume-based routing.
        """
        if k is not None:
            if not isinstance(k, int):
                raise ValueError("k must be an integer or None")
            if k >= self.G.number_of_nodes():
                k = None # NetworkX raises ValueError if k > len(nodes)
            
        G_simple = nx.DiGraph(self.G)
        bc = nx.betweenness_centrality(G_simple, k=k, seed=seed)
        return bc

    def compute_temporal_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Computes temporal analysis: first-seen and last-seen timestamps for each node
        based ONLY on observed edge propagation/observation timestamps from available evidence.
        
        Note: These represent strictly observed timestamps. They are NEVER called:
        - block time
        - confirmation time
        - transaction creation time
        """
        metrics = {}
        for node in self.G.nodes():
            metrics[node] = {
                "first_seen": None,
                "last_seen": None
            }

        for u, v, data in self.G.edges(data=True):
            ts = data.get('timestamp')
            if ts is not None:
                # Update for source node
                u_first = metrics[u]["first_seen"]
                u_last = metrics[u]["last_seen"]
                
                if u_first is None or ts < u_first:
                    metrics[u]["first_seen"] = ts
                if u_last is None or ts > u_last:
                    metrics[u]["last_seen"] = ts
                    
                # Update for target node
                v_first = metrics[v]["first_seen"]
                v_last = metrics[v]["last_seen"]
                
                if v_first is None or ts < v_first:
                    metrics[v]["first_seen"] = ts
                if v_last is None or ts > v_last:
                    metrics[v]["last_seen"] = ts

        return metrics

    def compute_louvain_communities(self, random_state: int = 42) -> Dict[str, int]:
        """
        Computes Louvain communities using the python-louvain library.
        Partitions the nodes into non-overlapping communities to detect 
        behavioral or operational subnetworks.
        
        Projection semantics:
        This is a topological/structural community projection.
        The python-louvain algorithm requires an undirected simple graph. 
        `nx.Graph(self.G)` intentionally removes:
        - edge direction
        - parallel-edge multiplicity
        - transaction observation multiplicity
        - monetary weighting (unless explicitly represented)
        
        The resulting Louvain community represents structural graph proximity only.
        It MUST NOT imply:
        - IP ownership
        - address ownership
        - transaction ownership
        - transaction origin
        - fund flow
        - common control
        
        Community ID Semantics:
        Community IDs are execution-local labels. They are NOT persistent entity 
        identifiers, NOT wallet identifiers, NOT CIH clusters, and NOT ownership 
        relationships.
        
        Determinism:
        Provides deterministic algorithmic behavior for a fixed graph, library 
        implementation, and random state.
        """
        import community.community_louvain as community_louvain
        
        if len(self.G) == 0:
            return {}
            
        G_simple_undirected = nx.Graph(self.G)
        # best_partition returns a dict: {node: community_id}
        partition = community_louvain.best_partition(
            G_simple_undirected, 
            random_state=random_state
        )
        return partition

    def detect_peel_chains(self, min_length: int = 3) -> List[List[str]]:
        """
        Detects structural peel-chain candidates directly from the base topological graph.
        
        A structural peel chain is a linear sequence of transactions connected by pass-through 
        addresses. Structurally, we define a peel-chain link as:
        - A Transaction (TX) with exactly 2 distinct output addresses (structural 'peel' and 'change').
        - The 'change' Address acts strictly as a continuous link.
        
        Typed-degree semantics for pass-through Address:
        - exactly 1 OUTPUT edge enters the address
        - exactly 1 INPUT edge leaves the address
        IP propagation edges or unrelated edge types do not interfere.
          
        This is a purely topological/structural analysis. It does NOT claim to verify
        confirmed economic peel behavior (e.g. large initial UTXO, small peeled amount,
        bulk remainder). It does NOT query or rely on Phase 8 (H1/H2) clustering evidence.
        
        Returns a list of transaction chains (List[str] representing txids).
        """
        if min_length < 2:
            raise ValueError("min_length must be >= 2. A single transaction is not a chain.")
            
        peel_chains = []
        visited_txs = set()
        
        # Sort to ensure deterministic iteration
        transactions = sorted([n for n, d in self.G.nodes(data=True) if d.get('type') == 'Transaction'])
        
        for tx in transactions:
            if tx in visited_txs:
                continue
                
            current_chain = [tx]
            current_tx = tx
            
            while True:
                # Find all distinct output addresses for the current TX
                # Edge is current_tx -> addr, edge_type="OUTPUT"
                outputs = set()
                for _, v, data in self.G.out_edges(current_tx, data=True):
                    if data.get('edge_type') == 'OUTPUT':
                        outputs.add(v)
                
                # We need exactly 2 distinct output addresses
                if len(outputs) != 2:
                    break # Chain breaks
                
                # Find if any output address acts as a perfect structural link
                next_tx = None
                
                # We sort outputs to ensure deterministic tie-breaking if both act as pass-throughs
                for addr in sorted(list(outputs)):
                    # Count typed degrees
                    incoming_outputs = [u for u, v, data in self.G.in_edges(addr, data=True) if data.get('edge_type') == 'OUTPUT']
                    outgoing_inputs = [v for u, v, data in self.G.out_edges(addr, data=True) if data.get('edge_type') == 'INPUT']
                    
                    if len(incoming_outputs) == 1 and len(outgoing_inputs) == 1:
                        potential_next_tx = outgoing_inputs[0]
                        # Prevent loops
                        if potential_next_tx not in current_chain:
                            next_tx = potential_next_tx
                            break
                
                if next_tx:
                    current_chain.append(next_tx)
                    visited_txs.add(next_tx)
                    current_tx = next_tx
                else:
                    break
                    
            if len(current_chain) >= min_length:
                peel_chains.append(current_chain)
                
        # To maintain strict determinism across runs, sort the resulting chains
        peel_chains.sort(key=lambda x: (len(x), x[0]))
        return peel_chains
