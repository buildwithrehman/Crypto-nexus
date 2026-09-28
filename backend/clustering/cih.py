import itertools
from typing import List, Dict, Set, Optional
from backend.schema import ClusteringEvidence

class CIHEngine:
    def evaluate_transaction(self, tx_data: dict) -> List[ClusteringEvidence]:
        """
        Takes transaction data dict with txid, input_addresses, output_amounts (optional), 
        run_id, source_file, source_row.
        Returns pairwise CIH relationships. 
        Confidence indicates heuristic structural reliability only, NOT probability of ownership or identity.
        """
        input_addresses = tx_data.get('input_addresses', [])
        # Deterministic sorting to ensure A < B pairwise stability
        unique_inputs = sorted(list(set(input_addresses)))
        
        if len(unique_inputs) < 2:
            return []
            
        uncertainty = None
        
        # 1. CoinJoin / Collaborative Transaction Safety
        # Flag suspicious identical output amounts common in standard CoinJoins
        output_amounts = tx_data.get('output_amounts', [])
        if len(output_amounts) > 1 and len(set(output_amounts)) < len(output_amounts):
            uncertainty = "Identical output amounts observed - potential CoinJoin-like/collaborative indicator"
        elif len(unique_inputs) > 50:
            uncertainty = "High input count observed - potential exchange batching indicator"
            
        evidence = []
        # Pairwise deterministic combinations
        for a, b in itertools.combinations(unique_inputs, 2):
            evidence.append(ClusteringEvidence(
                txid=tx_data['txid'],
                address_a=a,
                address_b=b,
                heuristic_name="CIH",
                confidence="High" if not uncertainty else "Low",
                uncertainty=uncertainty,
                run_id=tx_data['run_id'],
                source_file=tx_data['source_file'],
                source_row=tx_data['source_row']
            ))
        return evidence

class UnionFind:
    """
    Deterministic Union-Find implementation.
    """
    def __init__(self):
        self.parent = {}
        
    def find(self, i: str) -> str:
        if i not in self.parent:
            self.parent[i] = i
        if self.parent[i] == i:
            return i
        root = self.find(self.parent[i])
        self.parent[i] = root
        return root

    def union(self, i: str, j: str) -> None:
        if i not in self.parent:
            self.parent[i] = i
        if j not in self.parent:
            self.parent[j] = j
            
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # Deterministic union: lexically smaller root becomes parent
            if root_i < root_j:
                self.parent[root_j] = root_i
            else:
                self.parent[root_i] = root_j

    def get_clusters(self) -> Dict[str, List[str]]:
        clusters = {}
        for node in sorted(self.parent.keys()):
            root = self.find(node)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(node)
        return clusters

    def generate_cluster_records(self, run_id: str, timestamp) -> List[tuple]:
        """
        Generates (EntityCluster, list[ClusterMember]) for all roots.
        """
        import hashlib
        from backend.schema import EntityCluster, ClusterMember
        
        clusters = self.get_clusters()
        results = []
        for root, members in clusters.items():
            # Deterministic ID using SHA256 of root address truncated to fit BIGINT
            # 15 hex chars = 60 bits, fits safely in signed 64-bit int
            cluster_id = int(hashlib.sha256(root.encode('utf-8')).hexdigest()[:15], 16)
            
            ec = EntityCluster(
                cluster_id=cluster_id,
                run_id=run_id,
                creation_timestamp=timestamp
            )
            cm_list = [ClusterMember(cluster_id=cluster_id, address=m) for m in members]
            results.append((ec, cm_list))
        return results
