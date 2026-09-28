# backend/database/schema.py

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        run_id VARCHAR PRIMARY KEY,
        status VARCHAR NOT NULL,
        current_stage VARCHAR,
        failed_stage VARCHAR,
        error_message VARCHAR,
        start_timestamp TIMESTAMP NOT NULL,
        end_timestamp TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS run_uploads (
        run_id VARCHAR PRIMARY KEY,
        source_file VARCHAR NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ingestion_runs (
        run_id VARCHAR PRIMARY KEY,
        source_file VARCHAR NOT NULL,
        ingestion_timestamp TIMESTAMP NOT NULL,
        record_count BIGINT DEFAULT 0,
        quarantine_count BIGINT DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_records (
        run_id VARCHAR NOT NULL,
        source_file VARCHAR NOT NULL,
        source_row BIGINT NOT NULL,
        extracted_timestamp TIMESTAMP NOT NULL,
        PRIMARY KEY (run_id, source_file, source_row)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        txid VARCHAR PRIMARY KEY,
        run_id VARCHAR NOT NULL,
        source_file VARCHAR NOT NULL,
        source_row BIGINT NOT NULL,
        fee DECIMAL(38, 8),
        script_type VARCHAR,
        FOREIGN KEY (run_id, source_file, source_row) REFERENCES raw_records(run_id, source_file, source_row)
    );
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS seq_network_obs_id;
    """,
    """
    CREATE TABLE IF NOT EXISTS network_obs (
        obs_id BIGINT PRIMARY KEY DEFAULT nextval('seq_network_obs_id'),
        run_id VARCHAR NOT NULL,
        source_file VARCHAR NOT NULL,
        source_row BIGINT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        src_ip VARCHAR NOT NULL,
        dst_ip VARCHAR NOT NULL,
        src_port INTEGER NOT NULL,
        dst_port INTEGER NOT NULL,
        txid VARCHAR NOT NULL,
        FOREIGN KEY (run_id, source_file, source_row) REFERENCES raw_records(run_id, source_file, source_row),
        FOREIGN KEY (txid) REFERENCES transactions(txid)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS addresses (
        address VARCHAR PRIMARY KEY
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tx_inputs (
        txid VARCHAR NOT NULL,
        input_index INTEGER NOT NULL,
        address VARCHAR NOT NULL,
        amount DECIMAL(38, 8) NOT NULL,
        PRIMARY KEY (txid, input_index),
        FOREIGN KEY (txid) REFERENCES transactions(txid),
        FOREIGN KEY (address) REFERENCES addresses(address)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tx_outputs (
        txid VARCHAR NOT NULL,
        output_index INTEGER NOT NULL,
        address VARCHAR NOT NULL,
        amount DECIMAL(38, 8) NOT NULL,
        PRIMARY KEY (txid, output_index),
        FOREIGN KEY (txid) REFERENCES transactions(txid),
        FOREIGN KEY (address) REFERENCES addresses(address)
    );
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS seq_quarantine_id;
    """,
    """
    CREATE TABLE IF NOT EXISTS quarantine_errors (
        quarantine_id BIGINT PRIMARY KEY DEFAULT nextval('seq_quarantine_id'),
        run_id VARCHAR NOT NULL,
        source_file VARCHAR NOT NULL,
        source_row BIGINT NOT NULL,
        raw_data JSON NOT NULL,
        rejection_reason VARCHAR NOT NULL,
        quarantine_timestamp TIMESTAMP NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ip_enrichment (
        ip_address VARCHAR PRIMARY KEY,
        geo_country VARCHAR,
        asn VARCHAR,
        enrichment_timestamp TIMESTAMP NOT NULL
    );
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS seq_cluster_id;
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_clusters (
        cluster_id BIGINT PRIMARY KEY DEFAULT nextval('seq_cluster_id'),
        run_id VARCHAR NOT NULL,
        creation_timestamp TIMESTAMP NOT NULL
    );
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS seq_evidence_id;
    """,
    """
    CREATE TABLE IF NOT EXISTS clustering_evidence (
        evidence_id BIGINT PRIMARY KEY DEFAULT nextval('seq_evidence_id'),
        txid VARCHAR NOT NULL,
        address_a VARCHAR NOT NULL,
        address_b VARCHAR NOT NULL,
        heuristic_name VARCHAR NOT NULL,
        confidence VARCHAR NOT NULL,
        uncertainty VARCHAR,
        run_id VARCHAR NOT NULL,
        source_file VARCHAR NOT NULL,
        source_row BIGINT NOT NULL,
        FOREIGN KEY (txid) REFERENCES transactions(txid)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cluster_members (
        cluster_id BIGINT NOT NULL,
        address VARCHAR NOT NULL,
        PRIMARY KEY (cluster_id, address),
        FOREIGN KEY (cluster_id) REFERENCES entity_clusters(cluster_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id VARCHAR PRIMARY KEY,
        run_id VARCHAR NOT NULL,
        txid VARCHAR NOT NULL,
        anomaly_strength DOUBLE NOT NULL,
        evidential_strength_tier VARCHAR NOT NULL,
        operational_queue_rank INTEGER,
        model_version VARCHAR NOT NULL,
        dampeners_applied VARCHAR[],
        FOREIGN KEY (txid) REFERENCES transactions(txid)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS alert_reasons (
        alert_id VARCHAR NOT NULL,
        reason_text VARCHAR NOT NULL,
        signal_type VARCHAR NOT NULL,
        feature_name VARCHAR NOT NULL,
        computation_value DOUBLE NOT NULL,
        FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS alert_evidence (
        evidence_id VARCHAR PRIMARY KEY,
        alert_id VARCHAR NOT NULL,
        evidence_category VARCHAR NOT NULL,
        provenance_type VARCHAR NOT NULL,
        source_file VARCHAR,
        source_row BIGINT,
        model_version VARCHAR,
        schema_version VARCHAR,
        feature_name VARCHAR,
        underlying_evidence_references VARCHAR[],
        original_value VARCHAR,
        derived_value VARCHAR,
        uncertainty_semantics VARCHAR NOT NULL,
        FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
    );
    """
]

def initialize_schema(conn):
    """
    Executes all DDL statements to set up the canonical DuckDB tables.
    """
    for stmt in DDL_STATEMENTS:
        conn.execute(stmt)
        
    try:
        conn.execute("ALTER TABLE pipeline_runs ADD COLUMN geoip_status VARCHAR DEFAULT 'PENDING';")
    except Exception:
        pass
        
    try:
        conn.execute("ALTER TABLE pipeline_runs ADD COLUMN data_mode VARCHAR;")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE pipeline_runs ADD COLUMN worker_pid INTEGER;")
    except Exception:
        pass
