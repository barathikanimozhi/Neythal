
"""Pollution Watch: preliminary water-quality indicator analysis.

Chlorophyll-a is an indicator of algal biomass, not a direct
measurement of pollution or water toxicity.
"""
from .data_sources import fetch_chlorophyll

def analyse_chlorophyll(values):
    """Summarise valid chlorophyll-a measurements in mg/m³."""

    if values is None:
        return {
            "status": "unavailable",
            "message": "No chlorophyll measurements available."
        }

    clean_values = []

    for value in values:
        if value is None or isinstance(value, bool):
            continue

        if not isinstance(value, (int, float)):
            continue

        if value <= 0 or value == float("inf") or value != value:
            continue

        clean_values.append(float(value))

    if not clean_values:
        return {
            "status": "unavailable",
            "message": "No valid chlorophyll measurements found."
        }

    average = sum(clean_values) / len(clean_values)

    return {
        "status": "available",
        "measurement_count": len(clean_values),
        "minimum": round(min(clean_values), 4),
        "maximum": round(max(clean_values), 4),
        "average": round(average, 4),
        "unit": "mg/m³",
        "indicator": "Chlorophyll-a (algal biomass)",
        "interpretation": (
            "Elevated chlorophyll-a may indicate increased algal biomass. "
            "Further investigation is needed to identify the cause."
        ),
        "limitation": (
            "This measurement alone cannot establish pollution, "
            "toxicity or the cause of algal growth."
        )
    }

def analyse_region_chlorophyll(lat, lon):
    """Fetch and analyse real chlorophyll-a measurements."""

    try:
        data = fetch_chlorophyll(lat, lon)
        df = data["df"]

        result = analyse_chlorophyll(
            df["chlorophyll"].dropna().tolist()
        )

        result["metadata"] = data["meta"]

        return result

    except Exception as exc:
        return {
            "status": "unavailable",
            "message": str(exc)
        }