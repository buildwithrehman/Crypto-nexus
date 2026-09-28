from typing import Dict, Set, List, Any
import pandas as pd
from backend.scoring.alerts import AlertEngine
from backend.database.repository import CryptoNexusRepository

def fetch_tx_input_clusters(repo: CryptoNexusRepository, run_id: str, txids: List[str]) -> Dict[str, Set[int]]:
    """
    Fetches the distinct Phase 8 CIH cluster IDs for the INPUT addresses of the given transactions,
    scoped strictly to the specified run_id.
    """
    if not txids:
        return {}
        
    placeholders = ",".join(["?"] * len(txids))
    query = f"""
        SELECT i.txid, m.cluster_id
        FROM tx_inputs i
        JOIN cluster_members m ON i.address = m.address
        JOIN entity_clusters c ON m.cluster_id = c.cluster_id
        WHERE i.txid IN ({placeholders})
        AND c.run_id = ?
    """
    # Append run_id to the parameters list
    params = list(txids) + [run_id]
    rows = repo.conn.execute(query, params).fetchall()
    
    result = {}
    for txid, cid in rows:
        if txid not in result:
            result[txid] = set()
        result[txid].add(cid)
    return result

