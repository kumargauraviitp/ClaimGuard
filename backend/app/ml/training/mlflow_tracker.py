import os
import sys
import hashlib
import platform
import subprocess
from typing import Dict, Any, Optional

try:
    import mlflow
    import mlflow.sklearn
except ImportError:
    mlflow = None


def get_git_commit() -> str:
    """
    Retrieves the current git commit hash, if inside a git repository.
    """
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return commit.decode("utf-8").strip()
    except Exception:
        return "unknown"


def get_dataset_hash(file_path: str) -> str:
    """
    Computes SHA-256 hash of a file.
    """
    if not os.path.exists(file_path):
        return "none"
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_system_metadata(dataset_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregates Python, OS, package versions, and hardware info.
    """
    import sklearn
    import joblib
    import numpy as np
    import pandas as pd
    import optuna
    
    metadata = {
        "python_version": sys.version.split()[0],
        "os_platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "library_scikit_learn": sklearn.__version__,
        "library_pandas": pd.__version__,
        "library_numpy": np.__version__,
        "library_joblib": joblib.__version__,
        "library_optuna": optuna.__version__,
        "git_commit": get_git_commit()
    }
    
    # Optional libraries
    try:
        import xgboost
        metadata["library_xgboost"] = xgboost.__version__
    except Exception:
        metadata["library_xgboost"] = "not_installed"
        
    try:
        import lightgbm
        metadata["library_lightgbm"] = lightgbm.__version__
    except Exception:
        metadata["library_lightgbm"] = "not_installed"
        
    try:
        import ctgan
        metadata["library_ctgan"] = ctgan.__version__
    except Exception:
        metadata["library_ctgan"] = "not_installed"

    if mlflow is not None:
        metadata["library_mlflow"] = mlflow.__version__
    else:
        metadata["library_mlflow"] = "not_installed"
        
    if dataset_path and os.path.exists(dataset_path):
        metadata["dataset_name"] = os.path.basename(dataset_path)
        metadata["dataset_hash"] = get_dataset_hash(dataset_path)
        metadata["dataset_size_bytes"] = os.path.getsize(dataset_path)
        
    return metadata


class MLflowTracker:
    """
    MLflow tracking helper to manage experiments, runs, and model registry.
    """
    def __init__(self, experiment_name: str = "Fraud_Detection_Engine"):
        self.experiment_name = experiment_name
        self.active_run = None
        if mlflow is not None:
            try:
                mlflow.set_experiment(experiment_name)
            except Exception as e:
                print(f"Failed to set MLflow experiment: {e}")

    def start_run(self, run_name: str) -> Any:
        if mlflow is not None:
            self.active_run = mlflow.start_run(run_name=run_name)
            return self.active_run
        return None

    def log_params(self, params: Dict[str, Any]):
        if mlflow is not None and self.active_run is not None:
            # MLflow requires string/numeric values, filter/str cast complex structures
            clean_params = {k: str(v) for k, v in params.items()}
            mlflow.log_params(clean_params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        if mlflow is not None and self.active_run is not None:
            mlflow.log_metrics(metrics, step=step)

    def log_plot(self, plot_path: str, artifact_path: str = "plots"):
        if mlflow is not None and self.active_run is not None and os.path.exists(plot_path):
            mlflow.log_artifact(plot_path, artifact_path)

    def log_pipeline_model(self, pipeline: Any, registered_model_name: Optional[str] = None) -> Optional[str]:
        """
        Logs the pipeline model to the current run, and registers it if a name is provided.
        Returns the registered model version number or None.
        """
        if mlflow is not None and self.active_run is not None:
            mlflow.sklearn.log_model(
                sk_model=pipeline,
                artifact_path="model",
                registered_model_name=registered_model_name,
                serialization_format="pickle"
            )
            
            if registered_model_name:
                # Find the latest version of this model in the registry to return it
                client = mlflow.tracking.MlflowClient()
                try:
                    latest_versions = client.get_latest_versions(registered_model_name, stages=["None"])
                    if latest_versions:
                        return latest_versions[0].version
                except Exception as e:
                    print(f"Error fetching latest version: {e}")
        return None

    def end_run(self):
        if mlflow is not None and self.active_run is not None:
            mlflow.end_run()
            self.active_run = None

    def get_run_url(self) -> str:
        """
        Returns a local MLflow run tracking URL if possible.
        """
        if mlflow is not None and self.active_run is not None:
            # Return run ID
            return f"http://127.0.0.1:5000/#/experiments/1/runs/{self.active_run.info.run_id}"
        return "MLflow not running or tracking"


def promote_model_in_registry(model_name: str, version: str, stage: str = "Production"):
    """
    Transitions a registered model version to the target stage (Production, Candidate, Archived).
    """
    if mlflow is not None:
        client = mlflow.tracking.MlflowClient()
        
        # Map user-friendly stages to standard MLflow stages
        stage_mapped = stage.strip().capitalize()
        if stage_mapped in ["Candidate", "Staging"]:
            mlflow_stage = "Staging"
        elif stage_mapped in ["Production", "Active"]:
            mlflow_stage = "Production"
        elif stage_mapped in ["Archived", "Archive"]:
            mlflow_stage = "Archived"
        else:
            mlflow_stage = "None"
            
        try:
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=mlflow_stage,
                archive_existing_versions=(mlflow_stage == "Production")
            )
            # Add tag for clarity
            client.set_model_version_tag(model_name, version, "current_deployment", stage.lower())
            return True
        except Exception as e:
            print(f"Failed to transition model stage in registry to {mlflow_stage} (original: {stage}): {e}")
    return False
