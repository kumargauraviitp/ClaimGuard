from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Prediction, Claim, Explanation, ExplanationAuditLog
from .schemas import LocalExplanationResponse, GlobalExplanationResponse, ExportRequest
from .shap_service import SHAPService
from .visualization_service import VisualizationService
from .cache import ExplanationCacheService
from .export_service import ExportService
from .config import settings
import json
import os
import joblib


def _load_feature_names() -> List[str]:
    """Load feature names from the pipeline's own metadata (authoritative source).

    Falls back to features.json with proper unwrapping if the pipeline
    doesn't carry its own feature_names attribute.
    """
    artifacts_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "artifacts"
    )

    # Try loading the pipeline and reading feature_names from it (same as FraudModelService)
    status_path = os.path.join(artifacts_dir, "training_status.json")
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            status_data = json.load(f)
        best_model_meta = status_data.get("tuned_leaderboard", [{}])[0]
        pipeline_path = best_model_meta.get("pipeline_file", "")
        if pipeline_path:
            # Resolve relative to artifacts_dir (same logic as serving.py)
            if not os.path.exists(pipeline_path):
                pipeline_path = os.path.join(artifacts_dir, os.path.basename(pipeline_path))
            if not os.path.exists(pipeline_path):
                checkpoint = os.path.join(artifacts_dir, "tuned_checkpoints", os.path.basename(pipeline_path))
                if os.path.exists(checkpoint):
                    pipeline_path = checkpoint
            if os.path.exists(pipeline_path):
                wrapper = joblib.load(pipeline_path)
                if hasattr(wrapper, "feature_names") and wrapper.feature_names:
                    return list(wrapper.feature_names)

    # Fallback: features.json (handle both list and dict formats)
    features_path = os.path.join(artifacts_dir, "features.json")
    if os.path.exists(features_path):
        with open(features_path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("features", [])

    raise HTTPException(status_code=500, detail="Feature names not found in pipeline or features.json")

router = APIRouter(prefix="/explain", tags=["Explainability"])

@router.get("/global", response_model=GlobalExplanationResponse)
def get_global_explanation(db: Session = Depends(get_db)):
    shap_svc = SHAPService(db)
    
    # Generate background dataset from real recent claims to compute global feature importances
    import pandas as pd
    import json
    import os
    from app.ml.preprocessing import DataPreprocessor
    
    # 1. Fetch recent claims (limit to 50 for performance)
    recent_claims = db.query(Claim).order_by(Claim.created_at.desc()).limit(50).all()
    
    if not recent_claims:
        raise HTTPException(status_code=404, detail="No claims available to generate global explanation.")
        
    preprocessor = DataPreprocessor(db)
    feature_vectors = []
    
    # 2. Preprocess each claim
    for claim in recent_claims:
        try:
            vector, metrics = preprocessor.process_claim(claim.id)
            if metrics["status"] == "success" and vector:
                feature_vectors.append(vector)
        except Exception:
            continue
            
    if not feature_vectors:
        raise HTTPException(status_code=500, detail="Failed to preprocess any claims for background data.")
        
    # 3. Build DataFrame using exact feature names from the pipeline itself
    feature_names = _load_feature_names()
    df = pd.DataFrame(feature_vectors, columns=feature_names)
    
    try:
        importances = shap_svc.generate_global_importance(df)
        return GlobalExplanationResponse(
            model_version="v1.0",
            feature_importances=importances
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{claim_id}", response_model=LocalExplanationResponse)
def generate_explanation(claim_id: str, db: Session = Depends(get_db)):
    # Check if prediction exists
    prediction = db.query(Prediction).filter(Prediction.claim_id == claim_id).order_by(Prediction.created_at.desc()).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found for this claim.")
        
    cache_svc = ExplanationCacheService(db)
    cached = cache_svc.get_cached_explanation(prediction.id)
    if cached:
        return LocalExplanationResponse(
            claim_id=claim_id,
            prediction=prediction.risk_category,
            fraud_probability=cached.fraud_probability,
            base_value=cached.base_value,
            top_positive_features=cached.top_positive_features,
            top_negative_features=cached.top_negative_features,
            visualization=cached.visualization_data
        )

    # Need to generate explanation
    # Get the features used for this prediction. In a real app, this should be fetched from the Feature Store
    # or the preprocessing pipeline. Here, we must re-preprocess or load saved features.
    from app.ml.preprocessing import DataPreprocessor
    preprocessor = DataPreprocessor(db)
    
    try:
        feature_vector, metrics = preprocessor.process_claim(claim_id)
        if metrics["status"] != "success":
            raise Exception(f"Preprocessing failed: {metrics.get('errors')}")
        
        # Convert vector to DataFrame matching the expected feature names
        import pandas as pd
        feature_names = _load_feature_names()
        X = pd.DataFrame([feature_vector], columns=feature_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preprocess claim: {e}")
        
    shap_svc = SHAPService(db)
    vis_svc = VisualizationService()
    
    try:
        base_val, prob, pos_features, neg_features, raw_shap = shap_svc.generate_local_explanation(X)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SHAP values: {e}")
        
    # Generate visualization data
    feature_names = X.columns.tolist()
    feature_values = X.iloc[0].tolist()
    shap_values = [raw_shap[f] for f in feature_names]
    
    vis_data = vis_svc.generate_chart_data(base_val, feature_names, feature_values, shap_values)
    
    # Dump models to dict
    pos_features_dict = [f.dict() for f in pos_features]
    neg_features_dict = [f.dict() for f in neg_features]
    
    # Save to DB
    explanation = Explanation(
        prediction_id=prediction.id,
        claim_id=prediction.claim_id,
        model_version="unknown",
        shap_version=settings.SHAP_VERSION,
        base_value=base_val,
        fraud_probability=prob,
        top_positive_features=pos_features_dict,
        top_negative_features=neg_features_dict,
        shap_values=raw_shap,
        visualization_data=vis_data
    )
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    
    # Cache it
    cache_svc.cache_explanation(explanation)
    
    # Audit log
    audit = ExplanationAuditLog(explanation_id=explanation.id, user_id="system", action="generated")
    db.add(audit)
    db.commit()

    return LocalExplanationResponse(
        claim_id=claim_id,
        prediction=prediction.risk_category,
        fraud_probability=prob,
        base_value=base_val,
        top_positive_features=pos_features_dict,
        top_negative_features=neg_features_dict,
        visualization=vis_data
    )

@router.get("/{claim_id}", response_model=LocalExplanationResponse)
def get_explanation(claim_id: str, db: Session = Depends(get_db)):
    prediction = db.query(Prediction).filter(Prediction.claim_id == claim_id).order_by(Prediction.created_at.desc()).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found.")
        
    cache_svc = ExplanationCacheService(db)
    cached = cache_svc.get_cached_explanation(prediction.id)
    if not cached:
        # Fetch from DB if not in cache
        cached = db.query(Explanation).filter(Explanation.prediction_id == prediction.id).first()
        if not cached:
            raise HTTPException(status_code=404, detail="Explanation not found. Please generate it first.")
            
    # Audit Log
    audit = ExplanationAuditLog(explanation_id=cached.id, user_id="system", action="viewed")
    db.add(audit)
    db.commit()
            
    return LocalExplanationResponse(
        claim_id=claim_id,
        prediction=prediction.risk_category,
        fraud_probability=cached.fraud_probability,
        base_value=cached.base_value,
        top_positive_features=cached.top_positive_features,
        top_negative_features=cached.top_negative_features,
        visualization=cached.visualization_data
    )

@router.get("/{claim_id}/export")
def export_explanation(claim_id: str, format: str = "csv", db: Session = Depends(get_db)):
    prediction = db.query(Prediction).filter(Prediction.claim_id == claim_id).order_by(Prediction.created_at.desc()).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found.")
        
    explanation = db.query(Explanation).filter(Explanation.prediction_id == prediction.id).first()
    if not explanation:
        raise HTTPException(status_code=404, detail="Explanation not found.")
        
    export_svc = ExportService(db)
    
    # Audit
    audit = ExplanationAuditLog(explanation_id=explanation.id, user_id="system", action=f"exported_{format}")
    db.add(audit)
    db.commit()
    
    if format.lower() == "csv":
        csv_data = export_svc.export_csv(explanation)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=explanation_{claim_id}.csv"})
    else:
        raise HTTPException(status_code=400, detail="Only CSV export is supported right now.")

@router.post("/batch")
def batch_explain(claim_ids: List[str], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    def run_batch_explain(c_ids: List[str]):
        from app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            # We will use the existing generate_explanation endpoint logic internally
            # For simplicity, we loop and call the internal logic.
            # In a real system, you'd extract the logic into a service function to avoid HTTP overhead.
            for c_id in c_ids:
                try:
                    generate_explanation(c_id, bg_db)
                except Exception as e:
                    print(f"Batch explain failed for {c_id}: {e}")
        finally:
            bg_db.close()
            
    background_tasks.add_task(run_batch_explain, claim_ids)
    return {"status": f"Batch explanation started for {len(claim_ids)} claims."}

@router.delete("/cache")
def clear_cache(db: Session = Depends(get_db)):
    cache_svc = ExplanationCacheService(db)
    cache_svc.clear_cache()
    return {"status": "success"}


