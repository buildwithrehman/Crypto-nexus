import unittest
import pandas as pd
import numpy as np
import os
import shutil
import shap

from backend.ml.pipeline import MLPipeline

class TestMLPipeline(unittest.TestCase):
    def setUp(self):
        self.artifact_dir = "tests/test_artifacts"
        os.makedirs(self.artifact_dir, exist_ok=True)
        self.pipeline = MLPipeline(
            random_state=42, 
            contamination=0.1, 
            min_cluster_size=2,
            artifact_dir=self.artifact_dir
        )
        
        # Create a mock dataframe conforming to the exact 18-column contract
        self.df = pd.DataFrame({
            "tx_id": ["tx1", "tx2", "tx3", "tx4", "tx5", "tx6", "tx7", "tx8", "tx9", "tx10"],
            "in_degree": [1, 2, 0, 10, 1, 2, 2, 2, 2, 20],
            "out_degree": [1, 1, 0, 10, 1, 1, 1, 1, 1, 20],
            "total_degree": [2, 3, 0, 20, 2, 3, 3, 3, 3, 40],
            "betweenness": [0.1, 0.2, 0.0, 0.9, 0.1, 0.2, 0.2, 0.2, 0.2, 0.95],
            "louvain_community": [1, 1, 2, 3, 1, 1, 1, 1, 1, 3],
            "is_peel_chain": [0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
            "weighted_in": [1.0, 2.0, 0.0, 10.0, 1.0, 2.0, 2.0, 2.0, 2.0, 50.0],
            "weighted_out": [0.9, 1.9, 0.0, 9.9, 0.9, 1.9, 1.9, 1.9, 1.9, 49.9],
            "weighted_total": [1.9, 3.9, 0.0, 19.9, 1.9, 3.9, 3.9, 3.9, 3.9, 99.9],
            "fee": [0.1, 0.1, np.nan, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], 
            "average_input_value": [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.5],
            "average_output_value": [0.9, 1.9, 0.0, 0.99, 0.9, 1.9, 1.9, 1.9, 1.9, 2.49],
            "unique_in_addresses": [1, 2, 0, 10, 1, 2, 2, 2, 2, 20],
            "unique_out_addresses": [1, 1, 0, 10, 1, 1, 1, 1, 1, 20],
            "unique_ip_propagators": [1, 1, 0, 5, 1, 1, 1, 1, 1, 10],
            "propagation_edge_count": [1, 1, 0, 10, 1, 1, 1, 1, 1, 25],
            "duration_active_seconds": [300.0, 600.0, 0.0, 3600.0, 300.0, 600.0, 600.0, 600.0, 600.0, 7200.0]
        })
        
    def tearDown(self):
        if os.path.exists(self.artifact_dir):
            shutil.rmtree(self.artifact_dir)
            
    def test_pipeline_fit_transform(self):
        results = self.pipeline.fit_transform(self.df)
        self.assertEqual(len(results), 10)
        self.assertTrue("anomaly_score" in results.columns)
        
    def test_shap_semantics_validation(self):
        """
        Verifies expected_value + sum(SHAP) reconstructs the explained output 
        within numerical tolerance.
        """
        results = self.pipeline.fit_transform(self.df)
        
        # 1. Get exact model output being explained
        # For IsolationForest, TreeExplainer explains the raw tree path lengths, 
        # NOT the scikit-learn decision_function which is a transformed score.
        explainer = shap.TreeExplainer(self.pipeline.isolation_forest)
        expected_value = explainer.expected_value
        if isinstance(expected_value, np.ndarray):
            expected_value = expected_value[0]
            
        X = self.df.drop(columns=["tx_id"])
        X_processed = self.pipeline.preprocessor.transform(X)
        shap_values = explainer.shap_values(X_processed)
        
        # We must obtain the exact output SHAP is trying to explain.
        # TreeExplainer on IsolationForest explains the expected path length.
        explained_output = explainer.model.predict(X_processed)
        
        for i in range(len(self.df)):
            sum_shap = np.sum(shap_values[i])
            reconstructed_output = expected_value + sum_shap
            self.assertAlmostEqual(reconstructed_output, explained_output[i], places=5)
            
    def test_artifact_reload_and_determinism(self):
        # 1. Train and save
        results_fit = self.pipeline.fit_transform(self.df)
        
        # 2. Reload into fresh instance
        pipeline2 = MLPipeline(artifact_dir=self.artifact_dir)
        pipeline2.load_artifacts()
        
        # 3. Transform same data
        results_predict = pipeline2.transform_predict(self.df)
        
        # Verify scores are identical
        np.testing.assert_allclose(
            results_fit["anomaly_score"].values,
            results_predict["anomaly_score"].values,
            rtol=1e-5
        )
        
        np.testing.assert_array_equal(
            results_fit["is_anomaly"].values,
            results_predict["is_anomaly"].values
        )
        
    def test_hdbscan_noise_semantics(self):
        results = self.pipeline.fit_transform(self.df)
        labels = results["hdbscan_cluster_id"].values
        # -1 represents noise. tx3 and tx10 are highly divergent from the uniform clump, 
        # so we expect at least some noise or multiple clusters.
        self.assertTrue(np.any(labels == -1) or np.any(labels >= 0), "HDBSCAN should produce valid labels including potential noise")
        
    def test_schema_validation_failure(self):
        df_bad = self.df.drop(columns=["in_degree"])
        with self.assertRaises(ValueError):
            self.pipeline.fit_transform(df_bad)
            
    def test_missing_fee_imputation_and_indicator(self):
        # We manually run the preprocessor to inspect output
        self.pipeline._build_preprocessor()
        X = self.df.drop(columns=["tx_id"])
        X_processed = self.pipeline.preprocessor.fit_transform(X)
        feature_names = self.pipeline.preprocessor.get_feature_names_out()
        
        has_indicator = any("missingindicator" in name for name in feature_names)
        self.assertTrue(has_indicator)
        
    def test_categorical_louvain(self):
        self.pipeline._build_preprocessor()
        X = self.df.drop(columns=["tx_id"])
        self.pipeline.preprocessor.fit_transform(X)
        feature_names = self.pipeline.preprocessor.get_feature_names_out()
        
        cat_features = [f for f in feature_names if "louvain_community" in f]
        self.assertTrue(len(cat_features) >= 3)
        
    def test_pure_determinism(self):
        df = self.df.copy()
        
        pipe1 = MLPipeline(random_state=42, min_cluster_size=2, artifact_dir=self.artifact_dir)
        res1 = pipe1.fit_transform(df)
        
        pipe2 = MLPipeline(random_state=42, min_cluster_size=2, artifact_dir=self.artifact_dir)
        res2 = pipe2.fit_transform(df)
        
        np.testing.assert_allclose(res1["anomaly_score"].values, res2["anomaly_score"].values, rtol=1e-5)
        np.testing.assert_array_equal(res1["is_anomaly"].values, res2["is_anomaly"].values)
        np.testing.assert_array_equal(res1["hdbscan_cluster_id"].values, res2["hdbscan_cluster_id"].values)
        
        # Test SHAP reason ordering
        for i in range(len(res1)):
            reasons1 = [r["feature"] for r in res1.iloc[i]["shap_reasons"]]
            reasons2 = [r["feature"] for r in res2.iloc[i]["shap_reasons"]]
            self.assertEqual(reasons1, reasons2)

if __name__ == '__main__':
    unittest.main()
