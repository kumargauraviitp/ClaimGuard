def format_impact(val: float) -> str:
    """Format SHAP value into a +/- percentage impact string."""
    sign = "+" if val >= 0 else "-"
    # Multiply by 100 to show rough percentage point impact on log-odds or probability depending on base
    return f"{sign}{abs(val):.3f}"

def get_feature_display_name(feature: str, metadata: dict) -> str:
    """Fetch display name from metadata, fallback to formatted string."""
    if feature in metadata:
        return metadata[feature].get("display_name", feature)
    return feature.replace("_", " ").title()

def determine_direction(val: float) -> str:
    return "positive" if val > 0 else "negative"
