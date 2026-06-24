import os
import json
import shutil
import joblib
from datetime import datetime
from typing import Dict, Any, Optional

MODELS_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
PRODUCTION_DIR = os.path.join(MODELS_BASE, "production")
CANDIDATE_DIR = os.path.join(MODELS_BASE, "candidate")
ARCHIVE_DIR = os.path.join(MODELS_BASE, "archive")
METADATA_DIR = os.path.join(MODELS_BASE, "metadata")
REGISTRY_FILE = os.path.join(METADATA_DIR, "registry.json")

class ModelRegistry:
    def __init__(self):
        self.ensure_directories()
        self.registry = self.load_registry()

    def ensure_directories(self):
        for d in [MODELS_BASE, PRODUCTION_DIR, CANDIDATE_DIR, ARCHIVE_DIR, METADATA_DIR]:
            os.makedirs(d, exist_ok=True)
            
        if not os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "w") as f:
                json.dump({"production": None, "candidates": {}, "archived": {}}, f)

    def load_registry(self) -> Dict[str, Any]:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)

    def save_registry(self):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self.registry, f, indent=4)

    def register_candidate(self, version: str, metadata: Dict[str, Any], model_obj, explainer_obj=None):
        candidate_path = os.path.join(CANDIDATE_DIR, f"{version}")
        os.makedirs(candidate_path, exist_ok=True)
        
        joblib.dump(model_obj, os.path.join(candidate_path, "pipeline.joblib"))
        if explainer_obj:
            joblib.dump(explainer_obj, os.path.join(candidate_path, "explainer.joblib"))
            
        self.registry["candidates"][version] = {
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        self.save_registry()

    def promote_to_production(self, version: str):
        if version not in self.registry["candidates"]:
            raise ValueError(f"Version {version} not found in candidates.")
            
        # Archive current production if exists
        curr_prod = self.registry.get("production")
        if curr_prod:
            curr_version = curr_prod["version"]
            shutil.move(
                os.path.join(PRODUCTION_DIR, curr_version),
                os.path.join(ARCHIVE_DIR, curr_version)
            )
            self.registry["archived"][curr_version] = curr_prod
            
        # Move candidate to production
        shutil.move(
            os.path.join(CANDIDATE_DIR, version),
            os.path.join(PRODUCTION_DIR, version)
        )
        
        self.registry["production"] = {
            "version": version,
            "metadata": self.registry["candidates"].pop(version)["metadata"],
            "promoted_at": datetime.utcnow().isoformat() + "Z"
        }
        self.save_registry()

    def load_production_model(self):
        prod = self.registry.get("production")
        if not prod:
            return None, None
            
        version = prod["version"]
        prod_path = os.path.join(PRODUCTION_DIR, version)
        model_path = os.path.join(prod_path, "pipeline.joblib")
        explainer_path = os.path.join(prod_path, "explainer.joblib")
        
        model = joblib.load(model_path) if os.path.exists(model_path) else None
        explainer = joblib.load(explainer_path) if os.path.exists(explainer_path) else None
        
        return model, explainer

model_registry = ModelRegistry()
