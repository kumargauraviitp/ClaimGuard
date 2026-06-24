import os
import json
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder

def generate_mock_artifacts():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # 1. Feature Order (Metadata)
    features = [
        "age",
        "vehicle_speed",
        "number_of_vehicles_involved",
        "number_of_injured",
        "claim_amount",
        "repair_estimate",
        "medical_expenses",
        "reporting_delay_days",
        "vehicle_age",
        "policy_age",
        "claim_ratio",
        "police_report_available",
        "witness_present",
        "weekend_accident",
        "night_accident",
        "peak_traffic_accident"
    ]
    # In a real model, there'd be encoded features too
    categorical_features = ["gender", "policy_type", "accident_type", "weather_condition"]
    
    # Fit a dummy encoder
    df_cat = pd.DataFrame({
        "gender": ["male", "female", "other"],
        "policy_type": ["comprehensive", "third_party", "own_damage"],
        "accident_type": ["own_damage", "third_party", "theft"],
        "weather_condition": ["clear", "rainy", "foggy"]
    })
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    encoder.fit(df_cat)
    
    encoded_feature_names = encoder.get_feature_names_out(categorical_features).tolist()
    all_features = features + encoded_feature_names
    
    with open(os.path.join(artifacts_dir, "features.json"), "w") as f:
        json.dump(all_features, f)
        
    # Fit a dummy scaler on ALL features
    df_num = pd.DataFrame({col: [0, 10, 100] for col in all_features})
    scaler = StandardScaler()
    scaler.fit(df_num)
    
    joblib.dump(encoder, os.path.join(artifacts_dir, "encoder.pkl"))
    joblib.dump(scaler, os.path.join(artifacts_dir, "scaler.pkl"))
    
    print("Mock artifacts generated successfully in", artifacts_dir)
    print(f"Total features: {len(all_features)}")

if __name__ == "__main__":
    generate_mock_artifacts()
