import ipaddress
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from pydantic import ValidationError

from backend.schema import (
    NetworkObservation,
    Transaction,
    QuarantineRecord,
    ProvenanceMetadata
)

class DataValidator:
    def __init__(self, run_id: str, source_file: str):
        self.run_id = run_id
        self.source_file = source_file
        self.seen_txids = set()

    def _validate_ip(self, ip_str: str, field_name: str) -> None:
        if not ip_str:
            raise ValueError(f"Missing {field_name}")
        try:
            ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValueError(f"Invalid IP address format in {field_name}: {ip_str}")

    def _validate_port(self, port: Any, field_name: str) -> None:
        if port is None:
            raise ValueError(f"Missing {field_name}")
        try:
            port_num = int(port)
        except ValueError:
            raise ValueError(f"Invalid port format in {field_name}: {port}")
        
        if not (0 <= port_num <= 65535):
            raise ValueError(f"Port {field_name} out of range: {port_num}")

    def _validate_monetary(self, amounts: list) -> None:
        if not amounts:
            return
        for val in amounts:
            try:
                dec_val = Decimal(val)
                if dec_val < 0:
                    raise ValueError(f"Negative monetary value detected: {dec_val}")
            except Exception as e:
                raise ValueError(f"Invalid monetary value: {val} - {str(e)}")

    def validate_record(self, raw_data: Dict[str, Any], source_row: int) -> Tuple[bool, Any]:
        """
        Returns a tuple: (is_valid, record_or_quarantine)
        If valid, record_or_quarantine is a tuple (NetworkObservation, Transaction, ProvenanceMetadata)
        If invalid, record_or_quarantine is a QuarantineRecord
        """
        try:
            # 1. Duplicate TXID validation
            txid = raw_data.get("txid")
            if not txid:
                raise ValueError("Missing txid")
            if txid in self.seen_txids:
                raise ValueError(f"Duplicate txid: {txid}")

            # 2. IP and Port Validation
            self._validate_ip(raw_data.get("src_ip"), "src_ip")
            self._validate_ip(raw_data.get("dst_ip"), "dst_ip")
            self._validate_port(raw_data.get("src_port"), "src_port")
            self._validate_port(raw_data.get("dst_port"), "dst_port")

            # 3. Monetary Validation
            input_amounts = raw_data.get("input_amounts", [])
            output_amounts = raw_data.get("output_amounts", [])
            self._validate_monetary(input_amounts)
            self._validate_monetary(output_amounts)
            
            fee_str = raw_data.get("fee")
            if fee_str is not None and fee_str != "":
                self._validate_monetary([fee_str])
                
            # 4. Schema instantiation (handles required fields, timestamp parsing, array alignment)
            obs = NetworkObservation(**raw_data)
            tx = Transaction(**raw_data)
            
            # Record txid as seen only if successful
            self.seen_txids.add(txid)

            prov = ProvenanceMetadata(
                run_id=self.run_id,
                source_file=self.source_file,
                source_row=source_row,
                extracted_timestamp=datetime.utcnow()
            )
            
            return True, (obs, tx, prov)

        except ValidationError as e:
            reason = f"Schema validation failed: {str(e)}"
            return False, self._create_quarantine(raw_data, source_row, reason)
        except ValueError as e:
            reason = str(e)
            return False, self._create_quarantine(raw_data, source_row, reason)

    def validate_transaction(self, raw_data: Dict[str, Any], source_row: int) -> Tuple[bool, Any]:
        """Validates canonical transaction semantics (rejects duplicates)."""
        try:
            txid = raw_data.get("txid")
            if not txid:
                raise ValueError("Missing txid")
            if txid in self.seen_txids:
                raise ValueError(f"Duplicate txid: {txid}")

            input_amounts = raw_data.get("input_amounts", [])
            output_amounts = raw_data.get("output_amounts", [])
            self._validate_monetary(input_amounts)
            self._validate_monetary(output_amounts)
            
            fee_str = raw_data.get("fee")
            if fee_str is not None and fee_str != "":
                self._validate_monetary([fee_str])
                
            tx = Transaction(**raw_data)
            self.seen_txids.add(txid)

            prov = ProvenanceMetadata(
                run_id=self.run_id,
                source_file=self.source_file,
                source_row=source_row,
                extracted_timestamp=datetime.utcnow()
            )
            
            return True, (tx, prov)

        except ValidationError as e:
            reason = f"Schema validation failed: {str(e)}"
            return False, self._create_quarantine(raw_data, source_row, reason)
        except ValueError as e:
            reason = str(e)
            return False, self._create_quarantine(raw_data, source_row, reason)

    def validate_observation(self, raw_data: Dict[str, Any], source_row: int) -> Tuple[bool, Any]:
        """Validates run-scoped network observation semantics (allows duplicate TXIDs)."""
        try:
            txid = raw_data.get("txid")
            if not txid:
                raise ValueError("Missing txid")
                
            # DO NOT check self.seen_txids. Multiple observations for the same TXID are valid.

            self._validate_ip(raw_data.get("src_ip"), "src_ip")
            self._validate_ip(raw_data.get("dst_ip"), "dst_ip")
            self._validate_port(raw_data.get("src_port"), "src_port")
            self._validate_port(raw_data.get("dst_port"), "dst_port")

            obs = NetworkObservation(**raw_data)

            prov = ProvenanceMetadata(
                run_id=self.run_id,
                source_file=self.source_file,
                source_row=source_row,
                extracted_timestamp=datetime.utcnow()
            )
            
            return True, (obs, prov)

        except ValidationError as e:
            reason = f"Schema validation failed: {str(e)}"
            return False, self._create_quarantine(raw_data, source_row, reason)
        except ValueError as e:
            reason = str(e)
            return False, self._create_quarantine(raw_data, source_row, reason)

    def _create_quarantine(self, raw_data: Dict[str, Any], source_row: int, reason: str) -> QuarantineRecord:
        return QuarantineRecord(
            run_id=self.run_id,
            source_file=self.source_file,
            source_row=source_row,
            raw_data=raw_data,
            rejection_reason=reason,
            quarantine_timestamp=datetime.utcnow()
        )
