from app.database import SessionLocal, engine, Base
from app.models import FeatureMetadata

def seed_features():
    db = SessionLocal()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    default_features = [
        {
            "feature_name": "claim_amount",
            "display_name": "Claim Amount",
            "category": "Financial",
            "explanation_template": "The claim amount of {value} is significantly higher than average, which {direction} the fraud probability."
        },
        {
            "feature_name": "reporting_delay_days",
            "display_name": "Reporting Delay",
            "category": "Temporal",
            "explanation_template": "The accident was reported {value} days after the incident. This delay {direction} the fraud probability."
        },
        {
            "feature_name": "police_report_available",
            "display_name": "Police Report",
            "category": "Documentation",
            "explanation_template": "The availability of a police report {direction} the fraud probability."
        },
        {
            "feature_name": "vehicle_age",
            "display_name": "Vehicle Age",
            "category": "Vehicle",
            "explanation_template": "The vehicle is {value} years old, which {direction} the fraud probability."
        },
        {
            "feature_name": "policy_age_months",
            "display_name": "Policy Duration",
            "category": "Temporal",
            "explanation_template": "The policy has been active for {value} months. This duration {direction} the fraud probability."
        },
        {
            "feature_name": "claim_premium_ratio",
            "display_name": "Claim to Premium Ratio",
            "category": "Financial",
            "explanation_template": "The ratio of the claim amount to the annual premium is {value}, which {direction} the fraud probability."
        }
    ]
    
    try:
        for feat in default_features:
            existing = db.query(FeatureMetadata).filter_by(feature_name=feat["feature_name"]).first()
            if not existing:
                new_feat = FeatureMetadata(**feat)
                db.add(new_feat)
                print(f"Added feature metadata for: {feat['feature_name']}")
        
        db.commit()
        print("Feature metadata seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding features: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_features()
