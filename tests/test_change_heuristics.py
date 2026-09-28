import unittest
from decimal import Decimal
from backend.clustering.change_heuristics import evaluate_h1, evaluate_h2, evaluate_change_heuristics

class TestChangeHeuristics(unittest.TestCase):
    def setUp(self):
        self.base_tx = {
            "txid": "tx1",
            "input_addresses": ["A", "B"],
            "output_addresses": ["C", "D"],
            "input_amounts": ["1.0", "0.8"],
            "output_amounts": ["1.5", "0.29"],
            "fee": "0.01",
            "run_id": "run1",
            "source_file": "file.csv",
            "source_row": 1
        }

    # H1 tests

    def test_h1_multiple_inputs_reused(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B"]
        tx["output_addresses"] = ["C", "B"]
        ev = evaluate_h1(tx)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].heuristic_name, "H1")
        self.assertEqual(ev[0].address_a, "A")
        self.assertEqual(ev[0].address_b, "B") # B is candidate

    def test_h1_no_reused_address(self):
        ev = evaluate_h1(self.base_tx)
        self.assertEqual(len(ev), 0)

    def test_h1_multiple_reused(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B"]
        tx["output_addresses"] = ["A", "B"]
        ev = evaluate_h1(tx)
        self.assertEqual(len(ev), 0)

    def test_h1_single_output(self):
        tx = self.base_tx.copy()
        tx["output_addresses"] = ["B"]
        ev = evaluate_h1(tx)
        self.assertEqual(len(ev), 0)

    def test_h1_collaborative(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B"]
        tx["output_addresses"] = ["C", "B"]
        tx["output_amounts"] = ["1.0", "1.0"] # Collaborative
        ev = evaluate_h1(tx)
        self.assertEqual(len(ev), 0)

    def test_h1_more_than_50_inputs(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = [f"addr{i}" for i in range(51)]
        tx["input_addresses"].append("B")
        tx["output_addresses"] = ["C", "B"]
        ev = evaluate_h1(tx)
        self.assertEqual(len(ev), 0)

    # H2 tests
    def test_h2_valid_remainder(self):
        ev = evaluate_h2(self.base_tx, [])
        self.assertEqual(len(ev), 2)
        candidates = [e.address_b for e in ev]
        self.assertEqual(candidates, ["D", "D"])
        inputs = {e.address_a for e in ev}
        self.assertEqual(inputs, {"A", "B"})

    def test_h2_h1_applies(self):
        tx = self.base_tx.copy()
        tx["output_addresses"] = ["C", "B"]
        # Technically h1 ev array would be passed
        ev1 = evaluate_h1(tx)
        ev2 = evaluate_h2(tx, ev1)
        self.assertEqual(len(ev2), 0)

    def test_h2_output_a_not_greater(self):
        tx = self.base_tx.copy()
        tx["output_amounts"] = ["0.9", "0.89"]
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_output_b_not_less(self):
        tx = self.base_tx.copy()
        tx["output_amounts"] = ["1.5", "0.8"] # 0.8 is not < 0.8
        tx["fee"] = "-0.5" # Just to make sum hold
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_more_than_2_outputs(self):
        tx = self.base_tx.copy()
        tx["output_addresses"] = ["C", "D", "E"]
        tx["output_amounts"] = ["1.5", "0.29", "0.01"]
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_fewer_than_2_inputs(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A"]
        tx["input_amounts"] = ["1.8"]
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_missing_input_amount(self):
        tx = self.base_tx.copy()
        tx["input_amounts"] = ["1.0"] # length mismatch
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_missing_output_amount(self):
        tx = self.base_tx.copy()
        tx["output_amounts"] = ["1.5"] # length mismatch
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_fee_inconsistency(self):
        tx = self.base_tx.copy()
        tx["fee"] = "0.05" # in(1.8) - out(1.79) = 0.01
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_h2_missing_fee(self):
        tx = self.base_tx.copy()
        del tx["fee"]
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 2) # Fee missing is fine if Phase 7 handles it safely, Phase 7 says "fee_missing" is unresolved?
        # Wait, Phase 7 validate_fee_semantics returns "fee_missing" if reported_fee is None.
        # But if we want it strictly economically consistent, maybe we allow fee_missing?
        # "If monetary information is incomplete: unresolved / not applicable"
        # The prompt says: "and, when fee is supplied: sum(inputs) - sum(outputs) == fee".
        # Which implies if it's NOT supplied, we just check sum(inputs) >= sum(outputs).

    def test_h2_identical_outputs(self):
        tx = self.base_tx.copy()
        tx["output_amounts"] = ["0.89", "0.89"]
        tx["fee"] = "0.02"
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 0)

    def test_no_union_find_calls(self):
        # We can prove it by asserting no imports of UnionFind exist in change_heuristics.py
        with open("backend/clustering/change_heuristics.py", "r") as f:
            content = f.read()
            self.assertNotIn("UnionFind", content)
            
    def test_provenance(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B"]
        tx["output_addresses"] = ["C", "B"]
        ev = evaluate_h1(tx)
        self.assertEqual(ev[0].txid, "tx1")
        self.assertEqual(ev[0].run_id, "run1")
        self.assertEqual(ev[0].source_file, "file.csv")
        self.assertEqual(ev[0].source_row, 1)

    def test_determinism(self):
        tx1 = self.base_tx.copy()
        tx1["input_addresses"] = ["B", "A"]
        
        tx2 = self.base_tx.copy()
        tx2["input_addresses"] = ["A", "B"]
        
        ev1 = evaluate_h2(tx1, [])
        ev2 = evaluate_h2(tx2, [])
        
        self.assertEqual(ev1[0].address_a, ev2[0].address_a)
        self.assertEqual(ev1[1].address_a, ev2[1].address_a)

    def test_h1_single_input_edge_case(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A"]
        tx["output_addresses"] = ["A", "B"]
        ev = evaluate_h1(tx)
        # Should preserve candidate result without fabricating self-edge A->A
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].address_a, "")
        self.assertEqual(ev[0].address_b, "A")
        self.assertNotIn("A -> A", ev[0].uncertainty)
        
    def test_h1_missing_output_amounts(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["A", "B"]
        tx["output_addresses"] = ["C", "B"]
        if "output_amounts" in tx:
            del tx["output_amounts"]
        ev = evaluate_h1(tx)
        # Should not falsely trigger identical-output exclusion
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].address_b, "B")
        
    def test_h2_missing_fee_semantics(self):
        tx = self.base_tx.copy()
        # in_sum = 1.8, out_sum = 1.79 -> fee = 0.01. Phase 7 allows fee missing.
        if "fee" in tx:
            del tx["fee"]
        ev = evaluate_h2(tx, [])
        self.assertEqual(len(ev), 2)
        # Verify inconsistency still fails
        tx_inconsistent = tx.copy()
        tx_inconsistent["fee"] = "0.05"
        ev_fail = evaluate_h2(tx_inconsistent, [])
        self.assertEqual(len(ev_fail), 0)
        
    def test_h2_deterministic_ordering(self):
        tx = self.base_tx.copy()
        tx["input_addresses"] = ["Z", "M", "A"]
        tx["input_amounts"] = ["1.0", "1.0", "1.0"]
        if "fee" in tx:
            del tx["fee"]
        ev1 = evaluate_h2(tx, [])
        ev2 = evaluate_h2(tx, [])
        # Ordered as A, M, Z
        self.assertEqual([e.address_a for e in ev1], ["A", "M", "Z"])
        self.assertEqual([e.address_a for e in ev1], [e.address_a for e in ev2])
        
    def test_evaluate_change_heuristics_integration(self):
        tx = self.base_tx.copy()
        # Should evaluate H1 first and return H1 evidence if it matches
        tx["output_addresses"] = ["A", "C"]
        ev = evaluate_change_heuristics(tx)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0].heuristic_name, "H1")
        
        # If no H1, should fall through to H2
        tx["output_addresses"] = ["C", "D"]
        ev2 = evaluate_change_heuristics(tx)
        self.assertEqual(len(ev2), 2)
        self.assertEqual(ev2[0].heuristic_name, "H2")

if __name__ == '__main__':
    unittest.main()
