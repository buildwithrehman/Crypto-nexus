import duckdb
from backend.database.schema import initialize_schema

def get_connection(db_path: str = "cryptonexus.duckdb") -> duckdb.DuckDBPyConnection:
    """
    Returns a connection to the DuckDB database, initializing the schema
    if this is a new database.
    """
    conn = duckdb.connect(db_path)
    # Ensure JSON extension is loaded/available (natively bundled in 0.10.0)
    # conn.install_extension("json")
    # conn.load_extension("json")
    
    # Initialize tables
    initialize_schema(conn)
    return conn
