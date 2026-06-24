from typing import List, Dict, Any

class RankingEngine:
    """
    Computes a composite weighted score for each trained model combination
    to produce the leaderboard ranking. Supports custom configurations.
    """
    def __init__(self, weights: Dict[str, float] = None):
        # Default weights matching insurance multi-objective criteria
        self.weights = weights or {
            "precision": 0.40,
            "fpr": 0.30,       # Note: FPR should be minimized, so we score (1 - FPR)
            "roc_auc": 0.20,
            "recall": 0.10
        }
        # Normalize weights to sum to 1.0 if not already
        total_weight = sum(self.weights.values())
        if total_weight > 0 and abs(total_weight - 1.0) > 1e-5:
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

    def calculate_score(self, metrics: Dict[str, float]) -> float:
        """
        Computes weighted score for a dictionary of metrics.
        FPR is minimized, so we use (1.0 - FPR).
        All other metrics are maximized.
        """
        p = metrics.get("precision", 0.0)
        fpr = metrics.get("fpr", 0.0)
        auc = metrics.get("roc_auc", 0.5)
        rec = metrics.get("recall", 0.0)
        
        # 1 - FPR is used to score how low the FPR is (closer to 0 is better)
        fpr_score = 1.0 - fpr
        
        score = (
            self.weights.get("precision", 0.0) * p +
            self.weights.get("fpr", 0.0) * fpr_score +
            self.weights.get("roc_auc", 0.0) * auc +
            self.weights.get("recall", 0.0) * rec
        )
        return float(score)

    def rank_models(self, experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of experiment runs with their validation metrics,
        computes their composite score, and sorts them.
        """
        ranked_list = []
        for exp in experiments:
            metrics = exp.get("metrics", {})
            score = self.calculate_score(metrics)
            
            # Create a copy with the score added
            ranked_exp = exp.copy()
            ranked_exp["score"] = score
            ranked_list.append(ranked_exp)
            
        # Sort by score descending (highest score first)
        ranked_list.sort(key=lambda x: x["score"], reverse=True)
        
        # Assign rank indices
        for i, item in enumerate(ranked_list):
            item["rank"] = i + 1
            
        return ranked_list
