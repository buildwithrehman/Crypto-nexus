from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"

class RunCreateRequest(BaseModel):
    run_id: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    current_stage: Optional[str] = None
    failed_stage: Optional[str] = None
    error_message: Optional[str] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    geoip_status: Optional[str] = "PENDING"
    data_mode: Optional[str] = None
    
    @computed_field
    @property
    def is_demo(self) -> bool:
        return self.run_id == "run_e2e_phase_b"

    @computed_field
    @property
    def case_id(self) -> str:
        return "DEMO_V1" if self.is_demo else self.run_id

class PaginatedResponse(BaseModel):
    limit: int
    offset: int
    total: int
    data: list

class AlertSummary(BaseModel):
    model_config = {'protected_namespaces': ()}
    alert_id: str
    txid: str
    anomaly_strength: float
    evidential_strength_tier: str
    operational_queue_rank: Optional[int]
    model_version: str
    dampeners_applied: List[str]

class AlertReasonResponse(BaseModel):
    reason_text: str
    signal_type: str
    feature_name: str
    computation_value: float

class AlertEvidenceResponse(BaseModel):
    model_config = {'protected_namespaces': ()}
    evidence_id: str
    evidence_category: str
    provenance_type: str
    source_file: Optional[str]
    source_row: Optional[int]
    model_version: Optional[str]
    schema_version: Optional[str]
    feature_name: Optional[str]
    underlying_evidence_references: List[str]
    original_value: Optional[str]
    derived_value: Optional[str]
    uncertainty_semantics: Optional[str]

class KeyDriverResponse(BaseModel):
    feature: str
    value: Optional[float] = None
    shap_value: float
    direction: str
    meaning: str
    evidence_tier: str

class ExplanationResponse(BaseModel):
    summary: str
    key_drivers: List[KeyDriverResponse]
    investigation_caveats: List[str]
    provenance: List[str]
    human_readable_lead: str

class AlertDetail(AlertSummary):
    reasons: List[AlertReasonResponse]
    evidence: List[AlertEvidenceResponse]
    summary: Optional[str] = None
    key_drivers: Optional[List[KeyDriverResponse]] = None
    investigation_caveats: Optional[List[str]] = None
    provenance: Optional[List[str]] = None
    human_readable_lead: Optional[str] = None

class GraphNodeResponse(BaseModel):
    id: str
    node_type: str
    run_id: str
    metadata: Optional[dict] = None

class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    edge_type: str
    network_role: str
    provenance: Optional[str] = None
    amount: Optional[float] = None
    timestamp: Optional[datetime] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    run_id: str
    depth: int

class TransactionIO(BaseModel):
    address: str
    amount: float

class ObservedPeer(BaseModel):
    ip_address: str
    port: int
    geo_country: Optional[str] = None
    asn: Optional[str] = None

class TransactionInvestigationResponse(BaseModel):
    txid: str
    run_id: str
    source_file: str
    source_row: int
    fee: Optional[float] = None
    script_type: Optional[str] = None
    inputs: List[TransactionIO]
    outputs: List[TransactionIO]
    first_observed_network_timestamp: Optional[datetime] = None
    last_observed_network_timestamp: Optional[datetime] = None
    observed_peers: List[ObservedPeer]
    entity_clusters: List[int]
    alerts: List[AlertSummary]
    explanation: Optional[ExplanationResponse] = None

class SearchResult(BaseModel):
    record_type: str
    primary_identifier: str
    display_name: str
    run_id: Optional[str] = None
    txid: Optional[str] = None
    alert_id: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    limit: int
