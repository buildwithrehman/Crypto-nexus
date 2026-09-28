from decimal import Decimal
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

# 1. Network Observation
class NetworkObservation(BaseModel):
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    txid: str

# 2. Transaction
class Transaction(BaseModel):
    txid: str
    input_addresses: List[str]
    output_addresses: List[str]
    input_amounts: List[Decimal]
    output_amounts: List[Decimal]
    fee: Optional[Decimal] = None
    script_type: Optional[str] = None

    @model_validator(mode='after')
    def check_array_lengths(self) -> 'Transaction':
        if len(self.input_addresses) != len(self.input_amounts):
            raise ValueError(f"Array length mismatch: {len(self.input_addresses)} input_addresses vs {len(self.input_amounts)} input_amounts")
        if len(self.output_addresses) != len(self.output_amounts):
            raise ValueError(f"Array length mismatch: {len(self.output_addresses)} output_addresses vs {len(self.output_amounts)} output_amounts")
        return self

# 3. Address
class Address(BaseModel):
    address: str

# 4. IP/Network Enrichment
class IPEnrichment(BaseModel):
    ip_address: str
    geo_country: Optional[str] = None
    asn: Optional[str] = None

class ClusteringEvidence(BaseModel):
    txid: str
    address_a: str
    address_b: str
    heuristic_name: str
    confidence: str
    uncertainty: Optional[str] = None
    run_id: str
    source_file: str
    source_row: int

class EntityCluster(BaseModel):
    cluster_id: Optional[int] = None
    run_id: str
    creation_timestamp: datetime

class ClusterMember(BaseModel):
    cluster_id: int
    address: str

# 5. Ingestion Metadata
class IngestionMetadata(BaseModel):
    run_id: str
    source_file: str
    ingestion_timestamp: datetime
    record_count: int = 0
    quarantine_count: int = 0

# 6. Validation/Quarantine Metadata
class QuarantineRecord(BaseModel):
    run_id: str
    source_file: str
    source_row: int
    raw_data: Dict[str, Any]
    rejection_reason: str
    quarantine_timestamp: datetime
class TraversalPathEvidence(BaseModel):
    source: str
    target: str
    edge_type: str
    network_role: Optional[str] = None
    amount: Optional[Decimal] = None
    timestamp: Optional[datetime] = None
    run_id: str
    source_file: str
    source_row: int

# 7. Provenance/Evidence Metadata
class ProvenanceMetadata(BaseModel):
    run_id: str
    source_file: str
    source_row: int
    extracted_timestamp: datetime


class AlertEvidence(BaseModel):
    model_config = {'protected_namespaces': ()}
    evidence_id: str
    alert_id: str
    evidence_category: str
    provenance_type: str
    source_file: Optional[str] = None
    source_row: Optional[int] = None
    model_version: Optional[str] = None
    schema_version: Optional[str] = None
    feature_name: Optional[str] = None
    underlying_evidence_references: List[str] = Field(default_factory=list)
    original_value: Optional[str] = None
    derived_value: Optional[str] = None
    uncertainty_semantics: str

class AlertReason(BaseModel):
    alert_id: str
    reason_text: str
    signal_type: str
    feature_name: str
    computation_value: float

class Alert(BaseModel):
    model_config = {'protected_namespaces': ()}
    alert_id: str
    run_id: str
    txid: str
    anomaly_strength: float
    evidential_strength_tier: str
    operational_queue_rank: Optional[int] = None
    model_version: str
    dampeners_applied: List[str] = Field(default_factory=list)

