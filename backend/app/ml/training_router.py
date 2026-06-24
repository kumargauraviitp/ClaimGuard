import os
import json
import shutil
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app import schemas
from app.ml.training.orchestrator import MLTrainingOrchestrator, get_latest_status, update_status
from app.ml.training.mlflow_tracker import promote_model_in_registry

router = APIRouter(prefix="/api/training", tags=["training"])

def run_training_task():
    orchestrator = MLTrainingOrchestrator()
    orchestrator.run_pipeline()


@router.post("/start", response_model=schemas.TrainingStatusResponse)
def start_training(background_tasks: BackgroundTasks):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    artifacts_dir = os.path.join(base_dir, "artifacts")
    
    status = get_latest_status(artifacts_dir)
    if status.get("status") == "running":
        raise HTTPException(status_code=400, detail="Training is already in progress.")
        
    update_status(artifacts_dir, {
        "status": "running",
        "progress": 0.0,
        "current_step": "Starting training job...",
        "errors": [],
        "leaderboard": [],
        "tuned_leaderboard": []
    })
    
    background_tasks.add_task(run_training_task)
    
    return schemas.TrainingStatusResponse(
        status="running",
        progress=0.0,
        current_step="Training started in background.",
        errors=[]
    )


@router.get("/status", response_model=schemas.TrainingStatusResponse)
def get_training_status():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    artifacts_dir = os.path.join(base_dir, "artifacts")
    status = get_latest_status(artifacts_dir)
    return status


@router.get("/results")
def get_results():
    """
    Stage 15 spec: GET /api/training/results
    Returns the leaderboard.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    artifacts_dir = os.path.join(base_dir, "artifacts")
    
    status = get_latest_status(artifacts_dir)
    leaderboard = status.get("leaderboard", [])
    tuned_leaderboard = status.get("tuned_leaderboard", [])
    
    if not leaderboard:
        leaderboard_path = os.path.join(artifacts_dir, "leaderboard.json")
        if os.path.exists(leaderboard_path):
            with open(leaderboard_path, "r") as f:
                leaderboard = json.load(f)
                
        tuned_path = os.path.join(artifacts_dir, "tuned_leaderboard.json")
        if os.path.exists(tuned_path):
            with open(tuned_path, "r") as f:
                tuned_leaderboard = json.load(f)
                
    return {
        "leaderboard": leaderboard,
        "tuned_leaderboard": tuned_leaderboard
    }


@router.get("/experiment/{experiment_id}")
def get_experiment_details(experiment_id: str):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    experiments_dir = os.path.join(base_dir, "experiments")
    
    meta_path = os.path.join(experiments_dir, f"{experiment_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Experiment metadata for '{experiment_id}' not found.")
        
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    # Read metrics file if available
    exp_dir = os.path.join(experiments_dir, experiment_id)
    metrics_path = os.path.join(exp_dir, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            meta["detailed_metrics"] = json.load(f)
            
    # Read classification report
    report_path = os.path.join(exp_dir, "classification_report.txt")
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            meta["classification_report"] = f.read()

    # Read plots
    plots = {}
    for p_name in ["confusion_matrix", "roc_curve", "precision_recall_curve", "feature_importance"]:
        p_file = f"{p_name}.png"
        p_path = os.path.join(exp_dir, p_file)
        if os.path.exists(p_path):
            plots[p_name] = f"/api/training/plots/{experiment_id}/{p_file}"
                
    meta["plots"] = plots
    return meta


@router.get("/plots/{experiment_id}/{plot_file}")
def get_experiment_plot(experiment_id: str, plot_file: str):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    plot_path = os.path.join(base_dir, "experiments", experiment_id, plot_file)
    if not os.path.exists(plot_path):
        # Fallback to plots subfolder
        plot_path_sub = os.path.join(base_dir, "experiments", experiment_id, "plots", plot_file)
        if os.path.exists(plot_path_sub):
            return FileResponse(plot_path_sub)
        raise HTTPException(status_code=404, detail="Plot file not found.")
    return FileResponse(plot_path)


@router.post("/promote", response_model=schemas.ModelSelectionResponse)
def promote_model(payload: schemas.ModelSelectionRequest):
    """
    Stage 15 spec: POST /api/training/promote
    Promotes the selected model.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    experiments_dir = os.path.join(base_dir, "experiments")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    
    exp_id = payload.experiment_id
    model_src_path = os.path.join(experiments_dir, f"{exp_id}.pkl")
    
    if not os.path.exists(model_src_path):
        raise HTTPException(status_code=404, detail=f"Model artifact for experiment '{exp_id}' not found.")
        
    prod_path = os.path.join(artifacts_dir, "production.pkl")
    shutil.copy(model_src_path, prod_path)
    
    meta_path = os.path.join(experiments_dir, f"{exp_id}_meta.json")
    version = None
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
            version = meta.get("model_registry_version")
            if version:
                promote_model_in_registry("FraudDetectionEngine", str(version), "Production")
                
    return schemas.ModelSelectionResponse(
        status="success",
        message=f"Model from experiment {exp_id} successfully promoted to Production.",
        experiment_id=exp_id,
        model_registry_version=version
    )


@router.get("/report")
def download_report():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    report_path = os.path.join(base_dir, "artifacts", "training_report.md")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Training report not found. Train models first.")
    return FileResponse(report_path, media_type="text/markdown", filename="training_report.md")


@router.get("/models")
def list_models():
    """
    Stage 15 spec: GET /api/training/models
    Lists all trained models/experiments.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    experiments_dir = os.path.join(base_dir, "experiments")
    
    models_list = []
    if os.path.exists(experiments_dir):
        for f in os.listdir(experiments_dir):
            if f.endswith("_meta.json"):
                try:
                    with open(os.path.join(experiments_dir, f), "r") as meta_f:
                        meta = json.load(meta_f)
                        models_list.append({
                            "id": meta.get("id"),
                            "label": meta.get("label"),
                            "sampler": meta.get("sampler"),
                            "model": meta.get("model"),
                            "is_tuned": meta.get("is_tuned", False),
                            "metrics": meta.get("metrics", {})
                        })
                except Exception:
                    pass
    return models_list
