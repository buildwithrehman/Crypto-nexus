from decimal import Decimal
from typing import List, Dict, Any, Optional
from backend.schema import ClusteringEvidence
from backend.correlation.service import CorrelationService

def evaluate_h1(tx_data: dict) -> List[ClusteringEvidence]:
    """
    CryptoNexus Engineering Heuristic — not specified by PS26146.
    H1_Address_Reuse:
    Detect a candidate change address when exactly one output address is also present in the transaction's input addresses.
    """
    input_addresses = tx_data.get('input_addresses', [])
    output_addresses = tx_data.get('output_addresses', [])
    
    unique_inputs = sorted(list(set(input_addresses)))
    unique_outputs = sorted(list(set(output_addresses)))
    
    # Preconditions
    if len(input_addresses) < 1 or len(output_addresses) < 2:
        return []
        
    # Exclusions - Collaborative Indicators
    if len(unique_inputs) > 50:
        return [] # dampened / excluded completely per instructions
        
    output_amounts = tx_data.get('output_amounts', [])
    if len(output_amounts) > 1 and len(set(output_amounts)) < len(output_amounts):
        # Existing CIH logic identifies them as a collaborative indicator
        return []
        
    # Candidate condition
    intersections = [addr for addr in unique_outputs if addr in unique_inputs]
    
    if len(intersections) != 1:
        return [] # exactly one intersection required
        
    candidate = intersections[0]
    
    evidence = []
    # Create pairwise evidence linking the candidate change address to all OTHER distinct input addresses
    other_inputs = [addr for addr in unique_inputs if addr != candidate]
    
    if not other_inputs:
        # Preserve the candidate result without fabricating a self-referential relationship (A -> A)
        evidence.append(ClusteringEvidence(
            txid=tx_data['txid'],
            address_a="", # No other input to connect to
            address_b=candidate,
            heuristic_name="H1",
            confidence="Medium",
            uncertainty="Provides a heuristic signal consistent with possible change-address reuse. No other inputs to correlate.",
            run_id=tx_data['run_id'],
            source_file=tx_data['source_file'],
            source_row=tx_data['source_row']
        ))
    else:
        for in_addr in sorted(other_inputs):
            evidence.append(ClusteringEvidence(
                txid=tx_data['txid'],
                address_a=in_addr,
                address_b=candidate,
                heuristic_name="H1",
                confidence="Medium",
                uncertainty="Provides a heuristic signal consistent with possible change-address reuse.",
                run_id=tx_data['run_id'],
                source_file=tx_data['source_file'],
                source_row=tx_data['source_row']
            ))
        
    return evidence


def evaluate_h2(tx_data: dict, h1_evidence: List[ClusteringEvidence]) -> List[ClusteringEvidence]:
    """
    CryptoNexus Engineering Heuristic — not specified by PS26146.
    H2_Combinatorial:
    Identify a candidate change output under the approved remainder heuristic.
    """
    # Preconditions
    if h1_evidence:
        return []
        
    input_addresses = tx_data.get('input_addresses', [])
    output_addresses = tx_data.get('output_addresses', [])
    
    if len(input_addresses) < 2 or len(output_addresses) != 2:
        return []
        
    # Complete amounts
    input_amounts = tx_data.get('input_amounts', [])
    output_amounts = tx_data.get('output_amounts', [])
    
    if len(input_amounts) != len(input_addresses) or len(output_amounts) != len(output_addresses):
        return [] # incomplete data
        
    if any(amt is None for amt in input_amounts) or any(amt is None for amt in output_amounts):
        return []

    unique_inputs = sorted(list(set(input_addresses)))
    
    # Exclusions - Collaborative Indicators
    if len(output_amounts) > 1 and len(set(output_amounts)) < len(output_amounts):
        return []
        
    # Economic Consistency (Phase 7 semantics)
    in_sum = sum(Decimal(str(a)) for a in input_amounts)
    out_sum = sum(Decimal(str(a)) for a in output_amounts)
    
    if in_sum < out_sum:
        return [] # Economically inconsistent
        
    reported_fee = tx_data.get('fee')
    if reported_fee is not None:
        fee_check = CorrelationService.validate_fee_semantics(reported_fee, in_sum, out_sum)
        if fee_check.get("status") != "consistent":
            return [] # Failed Phase 7 fee consistency

    dec_in = [Decimal(str(a)) for a in input_amounts]
    dec_out = [Decimal(str(a)) for a in output_amounts]
    
    max_in = max(dec_in)
    min_in = min(dec_in)
    
    # Check Candidate condition
    # Exactly 2 outputs. 
    out_0 = dec_out[0]
    out_1 = dec_out[1]
    
    candidate = None
    if out_0 > max_in and out_1 < min_in:
        candidate = output_addresses[1]
    elif out_1 > max_in and out_0 < min_in:
        candidate = output_addresses[0]
        
    if not candidate:
        return []
        
    evidence = []
    other_inputs = [addr for addr in unique_inputs if addr != candidate]
    for in_addr in sorted(other_inputs):
        evidence.append(ClusteringEvidence(
            txid=tx_data['txid'],
            address_a=in_addr,
            address_b=candidate,
            heuristic_name="H2",
            confidence="Medium",
            uncertainty="Candidate change output under the remainder heuristic.",
            run_id=tx_data['run_id'],
            source_file=tx_data['source_file'],
            source_row=tx_data['source_row']
        ))
        
    return evidence


def evaluate_change_heuristics(tx_data: dict) -> List[ClusteringEvidence]:
    """
    Evaluates both H1 and H2.
    """
    ev = evaluate_h1(tx_data)
    if not ev:
        ev = evaluate_h2(tx_data, ev)
    return ev
