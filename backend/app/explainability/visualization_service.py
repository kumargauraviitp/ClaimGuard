from typing import Dict, Any, List

class VisualizationService:
    def generate_chart_data(self, base_value: float, feature_names: List[str], feature_values: List[Any], shap_values: List[float]) -> Dict[str, Any]:
        """
        Generate structured JSON for frontend charts.
        The frontend will use libraries like ECharts, Recharts, or Plotly.js to render.
        """
        
        # 1. Waterfall Plot Data (Local)
        # Represents how each feature contributed to moving the base value to the final output
        waterfall_data = []
        current_val = base_value
        
        # Sort by absolute impact for waterfall
        items = list(zip(feature_names, feature_values, shap_values))
        items.sort(key=lambda x: abs(x[2]), reverse=True)
        
        for name, val, sv in items[:10]: # Top 10 for visualization
            waterfall_data.append({
                "feature": name,
                "value": val,
                "shap_value": sv,
                "start": current_val,
                "end": current_val + sv
            })
            current_val += sv
            
        # 2. Summary/Bar Data
        bar_data = [{"feature": name, "shap_value": sv} for name, val, sv in items[:10]]
        
        return {
            "summary_plot": {
                "type": "bar",
                "data": bar_data
            },
            "waterfall_plot": {
                "type": "waterfall",
                "base_value": base_value,
                "final_value": current_val,
                "data": waterfall_data
            }
        }
