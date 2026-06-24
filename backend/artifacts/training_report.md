# Machine Learning Training & Model Selection Report
Generated: 2026-06-22 06:59:03

# Pareto Front Model Recommendations

Below is the Pareto Front of models based on the test set evaluations:

| Target Optimization | Model / Sampler | Precision | Recall | FPR | F1 | Cohen's Kappa | Brier Score | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| **Highest Precision** | TUNED SMOTE + LIGHTGBM | 0.3714 | 0.1408 | 0.0152 | 0.2042 | 0.1771 | 0.0531 | 284.69ms |
| **Highest Recall** | TUNED CTGAN + LIGHTGBM | 0.3187 | 0.2094 | 0.0285 | 0.2527 | 0.2155 | 0.0538 | 242.80ms |
| **Best Balanced (Composite)** | TUNED CTGAN + LIGHTGBM | 0.3187 | 0.2094 | 0.0285 | 0.2527 | 0.2155 | 0.0538 | 242.80ms |
| **Lowest FPR** | TUNED SMOTE + LIGHTGBM | 0.3714 | 0.1408 | 0.0152 | 0.2042 | 0.1771 | 0.0531 | 284.69ms |
| **Fastest Inference** | TUNED CTGAN + XGBOOST | 0.3094 | 0.2022 | 0.0287 | 0.2445 | 0.2070 | 0.0541 | 87.36ms |

## Stage 1: Baseline Sweep Leaderboard
Rank | Experiment ID | Sampler | Model Algorithm | Precision | FPR | ROC-AUC | Recall | Composite Score
---|---|---|---|---|---|---|---|---
1 | exp_005 | ctgan | lightgbm | 0.2462 | 0.0637 | 0.8337 | 0.3266 | 0.3406
2 | exp_002 | smote | lightgbm | 0.2490 | 0.0571 | 0.8381 | 0.2972 | 0.3319
3 | exp_006 | ctgan | xgboost | 0.2338 | 0.0604 | 0.8357 | 0.2895 | 0.3256
4 | exp_004 | ctgan | gbm | 0.2443 | 0.0488 | 0.8286 | 0.2477 | 0.3135
5 | exp_003 | smote | xgboost | 0.2807 | 0.0341 | 0.8303 | 0.2090 | 0.3089
6 | exp_001 | smote | gbm | 0.2182 | 0.0473 | 0.8122 | 0.2074 | 0.2927

## Stage 2: Tuned & Calibrated Models Leaderboard (Test Set)
Rank | Experiment ID | Sampler | Model | Precision | Recall | FPR | F1 | Cohen's Kappa | Brier | Composite Score
---|---|---|---|---|---|---|---|---|---|---
1 | exp_005_tuned | ctgan | lightgbm | 0.3187 | 0.2094 | 0.0285 | 0.2527 | 0.2155 | 0.0538 | 0.3190
2 | exp_006_tuned | ctgan | xgboost | 0.3094 | 0.2022 | 0.0287 | 0.2445 | 0.2070 | 0.0541 | 0.3080
3 | exp_002_tuned | smote | lightgbm | 0.3714 | 0.1408 | 0.0152 | 0.2042 | 0.1771 | 0.0531 | 0.3059
