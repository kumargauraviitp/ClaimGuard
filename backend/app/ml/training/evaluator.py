import os
import json
import time
import psutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    matthews_corrcoef,
    balanced_accuracy_score,
    average_precision_score,
    classification_report,
    brier_score_loss,
    cohen_kappa_score
)
from typing import Dict, Any, Tuple


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray, start_inference_time: float = 0.0) -> Dict[str, float]:
    """
    Computes all Stage 9 classification metrics.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # False Positive Rate (FPR)
    fpr = float(fp) / float(fp + tn) if (fp + tn) > 0 else 0.0
    # False Negative Rate (FNR)
    fnr = float(fn) / float(fn + tp) if (fn + tp) > 0 else 0.0
    
    # Sensitivity (Same as Recall)
    sensitivity = float(tp) / float(tp + fn) if (tp + fn) > 0 else 0.0
    # Specificity
    specificity = float(tn) / float(tn + fp) if (tn + fp) > 0 else 0.0
    
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5
        
    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except Exception:
        pr_auc = 0.0
        
    mcc = float(matthews_corrcoef(y_true, y_pred))
    balanced_accuracy = float(balanced_accuracy_score(y_true, y_pred))
    
    try:
        brier = float(brier_score_loss(y_true, y_prob))
    except Exception:
        brier = 1.0
        
    try:
        kappa = float(cohen_kappa_score(y_true, y_pred))
    except Exception:
        kappa = 0.0
        
    # Inference Time calculation
    inference_time_ms = 0.0
    if start_inference_time > 0.0:
        inference_time_ms = (time.time() - start_inference_time) * 1000.0
        
    # Memory Usage calculation
    process = psutil.Process(os.getpid())
    memory_usage_mb = float(process.memory_info().rss) / (1024 * 1024)
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "sensitivity": sensitivity,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "fpr": fpr,
        "fnr": fnr,
        "mcc": mcc,
        "balanced_accuracy": balanced_accuracy,
        "brier": brier,
        "kappa": kappa,
        "inference_time_ms": inference_time_ms,
        "memory_usage_mb": memory_usage_mb
    }


def generate_plots(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    feature_names: list,
    model: Any,
    save_dir: str
) -> Dict[str, str]:
    """
    Generates Confusion Matrix, ROC, PR, and Feature Importance plots.
    """
    os.makedirs(save_dir, exist_ok=True)
    plot_paths = {}
    
    # 1. Confusion Matrix
    cm_path = os.path.join(save_dir, "confusion_matrix.png")
    plt.figure(figsize=(6, 5))
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Not Fraud", "Fraud"],
                yticklabels=["Not Fraud", "Fraud"])
    plt.title("Confusion Matrix")
    plt.ylabel("Actual Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=100)
    plt.close()
    plot_paths["confusion_matrix"] = cm_path
    
    # 2. ROC Curve
    roc_path = os.path.join(save_dir, "roc_curve.png")
    plt.figure(figsize=(6, 5))
    fpr_vals, tpr_vals, _ = roc_curve(y_true, y_prob)
    auc_score = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.5
    plt.plot(fpr_vals, tpr_vals, label=f"AUC = {auc_score:.4f}", color="darkorange", lw=2)
    plt.plot([0, 1], [0, 1], color="navy", linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic (ROC)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(roc_path, dpi=100)
    plt.close()
    plot_paths["roc_curve"] = roc_path

    # 3. Precision-Recall Curve
    pr_path = os.path.join(save_dir, "precision_recall_curve.png")
    plt.figure(figsize=(6, 5))
    p_vals, r_vals, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_score = average_precision_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0
    plt.plot(r_vals, p_vals, color="purple", lw=2, label=f"PR-AUC = {pr_auc_score:.4f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(pr_path, dpi=100)
    plt.close()
    plot_paths["pr_curve"] = pr_path

    # 4. Feature Importance Plot
    fi_path = os.path.join(save_dir, "feature_importance.png")
    importance = None
    actual_model = model
    if hasattr(model, "steps"):
        actual_model = model.steps[-1][1]
        
    if hasattr(actual_model, "feature_importances_"):
        importance = actual_model.feature_importances_
    elif hasattr(actual_model, "coef_"):
        importance = np.abs(actual_model.coef_[0])

    if importance is not None and feature_names is not None:
        n_features = min(len(feature_names), len(importance))
        indices = np.argsort(importance)[::-1][:15]
        
        plt.figure(figsize=(8, 6))
        sns.barplot(
            x=[importance[i] for i in indices],
            y=[feature_names[i] for i in indices],
            hue=[feature_names[i] for i in indices],
            legend=False,
            palette="viridis"
        )
        plt.title("Top Feature Importances")
        plt.xlabel("Importance Score")
        plt.tight_layout()
        plt.savefig(fi_path, dpi=100)
        plt.close()
        plot_paths["feature_importance"] = fi_path
    else:
        plt.figure(figsize=(6, 5))
        plt.text(0.5, 0.5, "Feature Importance not supported", ha="center", va="center")
        plt.tight_layout()
        plt.savefig(fi_path, dpi=100)
        plt.close()
        plot_paths["feature_importance"] = fi_path

    return plot_paths
