import pandas as pd
import numpy as np
import joblib
import json
import os
import sys
from datetime import datetime, timezone
import sklearn
import hdbscan
import shap
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import IsolationForest

class MLPipeline:
    def __init__(self, random_state=42, contamination=0.05, min_cluster_size=5, artifact_dir="backend/ml/artifacts"):
        self.random_state = random_state
        self.contamination = contamination
        self.min_cluster_size = min_cluster_size
        self.artifact_dir = artifact_dir
        
        os.makedirs(self.artifact_dir, exist_ok=True)
        
        self.expected_columns = [
            "in_degree", "out_degree", "total_degree", "betweenness",
            "louvain_community", "is_peel_chain",
            "weighted_in", "weighted_out", "weighted_total", "fee",
            "average_input_value", "average_output_value",
            "unique_in_addresses", "unique_out_addresses",
            "unique_ip_propagators", "propagation_edge_count",
            "duration_active_seconds"
        ]
        
        self.continuous_features = [
            "in_degree", "out_degree", "total_degree", "betweenness",
            "weighted_in", "weighted_out", "weighted_total", "fee",
            "average_input_value", "average_output_value",
            "unique_in_addresses", "unique_out_addresses",
            "unique_ip_propagators", "propagation_edge_count",
            "duration_active_seconds"
        ]
        
        self.categorical_features = ["louvain_community"]
        self.binary_features = ["is_peel_chain"]
        
        # We will build the preprocessor dynamically to handle 'fee' imputation explicitly
        self.preprocessor = None
        self.isolation_forest = None
        self.hdbscan_clusterer = None
        
    def _validate_schema(self, df: pd.DataFrame):
        missing_cols = [col for col in self.expected_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required canonical features: {missing_cols}")

    def _build_preprocessor(self):
        # 1. Continuous Pipeline (includes fee which might have NaNs)
        continuous_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median', add_indicator=True)),
            ('scaler', RobustScaler())
        ])
        
        # 2. Categorical Pipeline
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        # 3. Binary Pipeline (passthrough)
        binary_transformer = Pipeline(steps=[
            ('passthrough', 'passthrough')
        ])
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('cont', continuous_transformer, self.continuous_features),
                ('cat', categorical_transformer, self.categorical_features),
                ('bin', binary_transformer, self.binary_features)
            ],
            remainder='drop' # Drop tx_id if accidentally included
        )
        
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fits the ML models and preprocessing pipeline, transforms the data, and returns
        a DataFrame containing tx_id, anomaly scores, hdbscan labels, and SHAP values.
        
        HDBSCAN Semantics:
        - Cluster IDs are execution/model-local behavioral groupings.
        - ID '-1' represents HDBSCAN noise (transactions that do not fit into any dense cluster).
        - Cluster IDs are NOT persistent entity IDs.
        - Cluster IDs are NOT evidence of suspiciousness by themselves.
        
        SHAP Semantics:
        - SHAP TreeExplainer evaluates the IsolationForest's internal tree path lengths, NOT the transformed scikit-learn decision_function directly.
        - In an Isolation Forest, anomalies are isolated faster, resulting in shorter path lengths.
        - Therefore, negative SHAP values (which pull the path length lower than the expected baseline) are the active drivers pushing the model toward classifying a transaction as anomalous.
        - The anomaly_score reported here is inverted (-decision_function) so that higher positive scores intuitively represent greater anomaly severity.
        - The top_feature_reasons strictly pull the most negative SHAP values (the strongest anomaly drivers).
        - SHAP contributions denote topological divergence from the median forest path, NOT a probability of crime.
        """
        if df.empty:
            return pd.DataFrame()
            
        self._validate_schema(df)
        self._build_preprocessor()
        
        # 1. Preprocess
        X = df.drop(columns=["tx_id"]) if "tx_id" in df.columns else df
        X_processed = self.preprocessor.fit_transform(X)
        
        feature_names = self.preprocessor.get_feature_names_out()
        X_processed_df = pd.DataFrame(X_processed, columns=feature_names, index=df.index)
        
        # 2. Isolation Forest (Primary Anomaly Model)
        self.isolation_forest = IsolationForest(
            random_state=self.random_state, 
            contamination=self.contamination
        )
        self.isolation_forest.fit(X_processed_df)
        
        # decision_function: Lower values are more anomalous.
        raw_decision_scores = self.isolation_forest.decision_function(X_processed_df)
        
        # Invert so higher score = more anomalous
        anomaly_scores = -raw_decision_scores
        is_anomaly = self.isolation_forest.predict(X_processed_df)
        is_anomaly_binary = (is_anomaly == -1).astype(int)
        
        # 3. HDBSCAN (Secondary Behavioral Clustering)
        self.hdbscan_clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            prediction_data=True
        )
        hdbscan_labels = self.hdbscan_clusterer.fit_predict(X_processed_df)
        
        # 4. SHAP Explanations
        explainer = shap.TreeExplainer(self.isolation_forest)
        
        # Optimize SHAP: Only compute for anomalous transactions
        anomaly_indices = np.where(is_anomaly_binary == 1)[0]
        top_feature_reasons = [[] for _ in range(len(X_processed_df))]
        
        if len(anomaly_indices) > 0:
            X_anomalies = X_processed_df.iloc[anomaly_indices]
            shap_values = explainer.shap_values(X_anomalies)
            
            for local_idx, global_idx in enumerate(anomaly_indices):
                instance_shap = shap_values[local_idx]
                sorted_idx = np.argsort(instance_shap) # Most negative first
                top_3_idx = sorted_idx[:3]
                
                reasons = []
                for idx in top_3_idx:
                    reasons.append({
                        "feature": feature_names[idx],
                        "contribution": float(instance_shap[idx]),
                        "value": float(X_processed_df.iloc[global_idx, idx])
                    })
                top_feature_reasons[global_idx] = reasons
            
        # 5. Compile Results
        results = pd.DataFrame({
            "tx_id": df["tx_id"] if "tx_id" in df.columns else df.index,
            "anomaly_score": anomaly_scores,
            "is_anomaly": is_anomaly_binary,
            "hdbscan_cluster_id": hdbscan_labels,
            "shap_reasons": top_feature_reasons,
            "raw_decision_score": raw_decision_scores # Hidden internally for testing/validation
        })
        
        # 6. Persist Artifacts
        self.save_artifacts(feature_names.tolist())
        np.save(os.path.join(self.artifact_dir, "reference_scores.npy"), anomaly_scores)
        
        return results

    def load_artifacts(self):
        """Loads the preprocessor and models from disk for inference."""
        self.preprocessor = joblib.load(os.path.join(self.artifact_dir, "preprocessor.joblib"))
        self.isolation_forest = joblib.load(os.path.join(self.artifact_dir, "isolation_forest.joblib"))
        self.hdbscan_clusterer = joblib.load(os.path.join(self.artifact_dir, "hdbscan.joblib"))
        with open(os.path.join(self.artifact_dir, "metadata.json"), "r") as f:
            self.metadata = json.load(f)

    def transform_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Runs offline prediction using loaded artifacts."""
        if df.empty:
            return pd.DataFrame()
            
        self._validate_schema(df)
        X = df.drop(columns=["tx_id"]) if "tx_id" in df.columns else df
        
        X_processed = self.preprocessor.transform(X)
        feature_names = self.preprocessor.get_feature_names_out()
        X_processed_df = pd.DataFrame(X_processed, columns=feature_names, index=df.index)
        
        raw_decision_scores = self.isolation_forest.decision_function(X_processed_df)
        anomaly_scores = -raw_decision_scores
        is_anomaly = self.isolation_forest.predict(X_processed_df)
        is_anomaly_binary = (is_anomaly == -1).astype(int)
        
        # HDBSCAN approximate predict for unseen data
        # approximate_predict returns (labels, probabilities)
        hdbscan_labels, _ = hdbscan.approximate_predict(self.hdbscan_clusterer, X_processed_df.values)
        

        explainer = shap.TreeExplainer(self.isolation_forest)
        
        # Optimize SHAP: Only compute for anomalous transactions
        anomaly_indices = np.where(is_anomaly_binary == 1)[0]
        top_feature_reasons = [[] for _ in range(len(X_processed_df))]
        
        if len(anomaly_indices) > 0:
            X_anomalies = X_processed_df.iloc[anomaly_indices]
            shap_values = explainer.shap_values(X_anomalies)
            
            for local_idx, global_idx in enumerate(anomaly_indices):
                instance_shap = shap_values[local_idx]
                sorted_idx = np.argsort(instance_shap) # Most negative first
                top_3_idx = sorted_idx[:3]
                
                reasons = []
                for idx in top_3_idx:
                    reasons.append({
                        "feature": feature_names[idx],
                        "contribution": float(instance_shap[idx]),
                        "value": float(X_processed_df.iloc[global_idx, idx])
                    })
                top_feature_reasons[global_idx] = reasons

            
        results = pd.DataFrame({
            "tx_id": df["tx_id"] if "tx_id" in df.columns else df.index,
            "anomaly_score": anomaly_scores,
            "is_anomaly": is_anomaly_binary,
            "hdbscan_cluster_id": hdbscan_labels,
            "shap_reasons": top_feature_reasons,
            "raw_decision_score": raw_decision_scores
        })
        return results

    def save_artifacts(self, feature_names):
        joblib.dump(self.preprocessor, os.path.join(self.artifact_dir, "preprocessor.joblib"))
        joblib.dump(self.isolation_forest, os.path.join(self.artifact_dir, "isolation_forest.joblib"))
        joblib.dump(self.hdbscan_clusterer, os.path.join(self.artifact_dir, "hdbscan.joblib"))
        
        metadata = {
            "model_version": "1.0",
            "schema_version": "1.0",
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "scikit_learn_version": sklearn.__version__,
            "hdbscan_version": hdbscan.__version__ if hasattr(hdbscan, '__version__') else "unknown",
            "shap_version": shap.__version__,
            "random_state": self.random_state,
            "contamination": self.contamination,
            "min_cluster_size": self.min_cluster_size,
            "feature_names_out": feature_names,
            "exact_canonical_feature_order": self.expected_columns,
            "preprocessing_config": {
                "continuous_features": self.continuous_features,
                "categorical_features": self.categorical_features,
                "binary_features": self.binary_features,
                "imputation_strategy": "median_with_indicator",
                "scaling": "RobustScaler",
                "categorical_encoding": "OneHotEncoder_ignore_unknown"
            },
            "model_config": {
                "primary": "IsolationForest",
                "secondary": "HDBSCAN"
            }
        }
        with open(os.path.join(self.artifact_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
