import duckdb
from typing import List, Dict, Any
from decimal import Decimal

class CorrelationService:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_ip_to_tx_correlation(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        Retrieves evidence-preserving IP ──[PROPAGATED]──► Transaction correlations.
        Never asserts ownership.
        """
        query = """
            SELECT n.txid, n.timestamp as observation_timestamp, n.run_id, n.source_file, n.source_row
            FROM network_obs n
            WHERE n.src_ip = ? OR n.dst_ip = ?
            ORDER BY n.timestamp ASC
        """
        results = self.conn.execute(query, [ip_address, ip_address]).fetchall()
        return [
            {
                "txid": row[0],
                "observation_timestamp": row[1],
                "run_id": row[2],
                "source_file": row[3],
                "source_row": row[4]
            }
            for row in results
        ]

    def get_tx_propagations(self, txid: str) -> List[Dict[str, Any]]:
        """
        Returns all network observations for a given TXID.
        """
        query = """
            SELECT n.src_ip, n.dst_ip, n.timestamp as observation_timestamp, 
                   n.run_id, n.source_file, n.source_row
            FROM network_obs n
            WHERE n.txid = ?
            ORDER BY n.timestamp ASC
        """
        results = self.conn.execute(query, [txid]).fetchall()
        return [
            {
                "src_ip": row[0],
                "dst_ip": row[1],
                "observation_timestamp": row[2],
                "run_id": row[3],
                "source_file": row[4],
                "source_row": row[5]
            }
            for row in results
        ]

    def get_address_inputs(self, address: str) -> List[Dict[str, Any]]:
        """
        Address ──[INPUT]──► Transaction correlations
        """
        query = """
            SELECT t.txid, t.input_index, t.amount, tr.run_id, tr.source_file, tr.source_row
            FROM tx_inputs t
            JOIN transactions tr ON t.txid = tr.txid
            WHERE t.address = ?
        """
        results = self.conn.execute(query, [address]).fetchall()
        return [
            {
                "txid": row[0],
                "input_index": row[1],
                "amount": Decimal(str(row[2])),
                "run_id": row[3],
                "source_file": row[4],
                "source_row": row[5]
            }
            for row in results
        ]

    def get_address_outputs(self, address: str) -> List[Dict[str, Any]]:
        """
        Transaction ──[OUTPUT]──► Address correlations
        """
        query = """
            SELECT t.txid, t.output_index, t.amount, tr.run_id, tr.source_file, tr.source_row
            FROM tx_outputs t
            JOIN transactions tr ON t.txid = tr.txid
            WHERE t.address = ?
        """
        results = self.conn.execute(query, [address]).fetchall()
        return [
            {
                "txid": row[0],
                "output_index": row[1],
                "amount": Decimal(str(row[2])),
                "run_id": row[3],
                "source_file": row[4],
                "source_row": row[5]
            }
            for row in results
        ]

    def get_tx_timeline(self, txid: str) -> Dict[str, Any]:
        """
        Exposes temporal correlations between the blockchain representation
        and the earliest network observation.
        """
        # Right now transactions don't have block_timestamp in our canonical schema.
        # We only have network_obs timestamps.
        query = """
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*) 
            FROM network_obs 
            WHERE txid = ?
        """
        row = self.conn.execute(query, [txid]).fetchone()
        
        # Verify transaction actually exists (prevent fabricating UTXO lineage etc)
        tx_check = self.conn.execute("SELECT run_id FROM transactions WHERE txid = ?", [txid]).fetchone()
        if not tx_check:
            return {}
            
        return {
            "txid": txid,
            "first_observed": row[0],
            "last_observed": row[1],
            "observation_count": row[2]
        }

    @staticmethod
    def validate_fee_semantics(reported_fee, in_sum, out_sum) -> Dict[str, Any]:
        """
        Phase 7 fee-validation logic.
        """
        if in_sum is None or out_sum is None:
            return {
                "status": "incomplete_data", 
                "reported_fee": Decimal(str(reported_fee)) if reported_fee is not None else None
            }
            
        calculated_fee = Decimal(str(in_sum)) - Decimal(str(out_sum))
        
        result = {
            "reported_fee": Decimal(str(reported_fee)) if reported_fee is not None else None,
            "calculated_fee": calculated_fee
        }
        
        if reported_fee is None:
            result["status"] = "fee_missing"
        elif Decimal(str(reported_fee)) == calculated_fee:
            result["status"] = "consistent"
        else:
            result["status"] = "inconsistent"
            
        return result

    def validate_transaction_fee(self, txid: str) -> Dict[str, Any]:
        """
        Calculates consistency between reported fee and sum(inputs) - sum(outputs).
        Does not invent a missing fee.
        Returns a dictionary with consistency status.
        """
        tx_row = self.conn.execute("SELECT fee FROM transactions WHERE txid = ?", [txid]).fetchone()
        if not tx_row:
            return {"status": "unknown_txid"}
            
        reported_fee = tx_row[0]
        
        in_sum_row = self.conn.execute("SELECT SUM(amount) FROM tx_inputs WHERE txid = ?", [txid]).fetchone()
        out_sum_row = self.conn.execute("SELECT SUM(amount) FROM tx_outputs WHERE txid = ?", [txid]).fetchone()
        
        in_sum = in_sum_row[0] if in_sum_row and in_sum_row[0] is not None else None
        out_sum = out_sum_row[0] if out_sum_row and out_sum_row[0] is not None else None
        
        return self.validate_fee_semantics(reported_fee, in_sum, out_sum)
