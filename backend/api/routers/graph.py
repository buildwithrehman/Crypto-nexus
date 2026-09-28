from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.dependencies import get_case_repository
from backend.api.services.query_service import QueryService
from backend.database.repository import CryptoNexusRepository
from backend.api.schemas.api_models import (
    GraphResponse, GraphNodeResponse, GraphEdgeResponse,
    TransactionInvestigationResponse, TransactionIO, ObservedPeer,
    ExplanationResponse, KeyDriverResponse
)
from backend.graph.builder import GraphBuilder
import networkx as nx

router = APIRouter(prefix="/runs/{run_id}/transactions", tags=["Graph"])

@router.get("/{txid}", response_model=TransactionInvestigationResponse)
def get_transaction_detail(run_id: str, txid: str, repo: CryptoNexusRepository = Depends(get_case_repository)):
    svc = QueryService(repo)
        
    tx_row = repo.conn.execute("""
        SELECT t.source_file, t.source_row, t.fee, t.script_type 
        FROM transactions t
        WHERE t.txid = ? AND EXISTS (
            SELECT 1 FROM network_obs n WHERE n.run_id = ? AND n.txid = ?
        )
    """, [txid, run_id, txid]).fetchone()
    if not tx_row:
        raise HTTPException(status_code=404, detail="Transaction not found in this run")
        
    source_file, source_row, fee, script_type = tx_row
    
    # Inputs
    inputs_rows = repo.conn.execute("SELECT address, amount FROM tx_inputs WHERE txid = ? ORDER BY input_index ASC", [txid]).fetchall()
    inputs = [TransactionIO(address=r[0], amount=float(r[1])) for r in inputs_rows]
    
    # Outputs
    outputs_rows = repo.conn.execute("SELECT address, amount FROM tx_outputs WHERE txid = ? ORDER BY output_index ASC", [txid]).fetchall()
    outputs = [TransactionIO(address=r[0], amount=float(r[1])) for r in outputs_rows]
    
    # Network obs & GeoIP
    obs_rows = repo.conn.execute("""
        SELECT n.timestamp, n.src_ip, n.src_port, i.geo_country, i.asn
        FROM network_obs n
        LEFT JOIN ip_enrichment i ON n.src_ip = i.ip_address
        WHERE n.run_id = ? AND n.txid = ?
        ORDER BY n.timestamp ASC
    """, [run_id, txid]).fetchall()
    
    first_obs = obs_rows[0][0] if obs_rows else None
    last_obs = obs_rows[-1][0] if obs_rows else None
    
    peers = [ObservedPeer(ip_address=r[1], port=r[2], geo_country=r[3], asn=r[4]) for r in obs_rows]
    
    # Entity clusters
    cluster_rows = repo.conn.execute("""
        SELECT DISTINCT e.cluster_id
        FROM tx_inputs i
        JOIN cluster_members m ON i.address = m.address
        JOIN entity_clusters e ON m.cluster_id = e.cluster_id
        WHERE i.txid = ? AND e.run_id = ?
        ORDER BY e.cluster_id ASC
    """, [txid, run_id]).fetchall()
    clusters = [r[0] for r in cluster_rows]
    
    # Alerts
    alerts_rows = repo.conn.execute("""
        SELECT alert_id FROM alerts 
        WHERE run_id = ? AND txid = ? 
        ORDER BY operational_queue_rank ASC, alert_id ASC
    """, [run_id, txid]).fetchall()
    
    tx_alerts = []
    tx_explanation = None
    for r in alerts_rows:
        alert_detail = svc.get_alert_detail(run_id, r[0])
        if alert_detail:
            from backend.api.schemas.api_models import AlertSummary
            tx_alerts.append(AlertSummary(**alert_detail.model_dump(exclude={'reasons', 'evidence', 'summary', 'key_drivers', 'investigation_caveats', 'provenance', 'human_readable_lead'})))
            if tx_explanation is None:
                # Use the explanation of the first (highest priority) alert
                tx_explanation = ExplanationResponse(
                    summary=alert_detail.summary,
                    key_drivers=alert_detail.key_drivers,
                    investigation_caveats=alert_detail.investigation_caveats,
                    provenance=alert_detail.provenance,
                    human_readable_lead=alert_detail.human_readable_lead
                )
            
    return TransactionInvestigationResponse(
        txid=txid,
        run_id=run_id,
        source_file=source_file,
        source_row=source_row,
        fee=float(fee) if fee is not None else None,
        script_type=script_type,
        inputs=inputs,
        outputs=outputs,
        first_observed_network_timestamp=first_obs,
        last_observed_network_timestamp=last_obs,
        observed_peers=peers,
        entity_clusters=clusters,
        alerts=tx_alerts,
        explanation=tx_explanation
    )
@router.get("/{txid}/neighbors", response_model=GraphResponse)
def get_graph_neighbors(run_id: str, txid: str, depth: int = Query(1, ge=1, le=2), repo: CryptoNexusRepository = Depends(get_case_repository)):
    svc = QueryService(repo)
        
    row = repo.conn.execute("SELECT 1 FROM network_obs WHERE run_id = ? AND txid = ?", [run_id, txid]).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found in this run")
        
    builder = GraphBuilder(repo.conn)
    G = builder.build_multidigraph(run_id)
    
    if not G.has_node(txid):
        raise HTTPException(status_code=404, detail="Transaction not in graph")
        
    subgraph = nx.ego_graph(G, txid, radius=depth, undirected=True)
    
    nodes = []
    edges = []
    
    sorted_nodes = sorted(subgraph.nodes(data=True), key=lambda x: (x[1].get("type", ""), str(x[0])))
    for n, data in sorted_nodes:
        nodes.append(GraphNodeResponse(
            id=str(n), 
            node_type=data.get("type", "unknown"), 
            run_id=run_id,
            metadata=data
        ))
        
    sorted_edges = sorted(subgraph.edges(keys=True, data=True), key=lambda x: (str(x[0]), str(x[1]), x[3].get("edge_type", "")))
    for u, v, k, data in sorted_edges:
        prov = None
        if "run_id" in data and "source_file" in data and "source_row" in data:
            prov = f"{data['run_id']}|{data['source_file']}|{data['source_row']}"
            
        amt = float(data["amount"]) if data.get("amount") is not None else None
        
        edges.append(GraphEdgeResponse(
            source=str(u), 
            target=str(v), 
            edge_type=data.get("edge_type", "unknown"),
            network_role=data.get("network_role", "unknown"),
            provenance=prov,
            amount=amt,
            timestamp=data.get("timestamp", None)
        ))
        
    return GraphResponse(nodes=nodes, edges=edges, run_id=run_id, depth=depth)
