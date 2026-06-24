import os
import json
import hashlib
import subprocess
from datetime import datetime
import yaml

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
CONFIG_YAML_PATH = os.path.join(CONFIG_DIR, "config.yaml")
CONFIG_LOCK_PATH = os.path.join(CONFIG_DIR, "config.lock.json")

def get_git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "unknown"

def generate_config_lock():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    if not os.path.exists(CONFIG_YAML_PATH):
        default_config = {
            "environment": os.getenv("ENV", "development"),
            "version": "1.0",
            "model_path": "models/production",
            "kb_path": "storage/knowledge"
        }
        with open(CONFIG_YAML_PATH, "w") as f:
            yaml.dump(default_config, f)
            
    with open(CONFIG_YAML_PATH, "r") as f:
        yaml_content = f.read()
        
    config_data = yaml.safe_load(yaml_content) or {}
    config_hash = hashlib.sha256(yaml_content.encode("utf-8")).hexdigest()
    
    lock_data = {
        "Config Hash": config_hash,
        "Version": config_data.get("version", "1.0"),
        "Created Time": datetime.utcnow().isoformat() + "Z",
        "Environment": config_data.get("environment", "development"),
        "Git SHA": get_git_sha()
    }
    
    with open(CONFIG_LOCK_PATH, "w") as f:
        json.dump(lock_data, f, indent=4)
        
    return lock_data

if __name__ == "__main__":
    lock = generate_config_lock()
    print("Generated config.lock.json:", lock)
