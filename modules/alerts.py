
"""Neythal Early Warning Centre.

Converts ocean-risk scores into understandable warning alerts.
"""


ALERT_LEVELS = [
    (25, "Low"),
    (50, "Moderate"),
    (75, "High"),
    (100, "Critical"),
]


def classify_risk(score):
    """Classify a risk score between 0 and 100."""

    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("Risk score must be a number.")

    if not 0 <= score <= 100:
        raise ValueError("Risk score must be between 0 and 100.")

    if score <= 25:
        return "Low"
    elif score <= 50:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Critical"


def generate_alert(score, region="Unknown region"):
    """Generate an early warning based on an ocean-risk score."""

    level = classify_risk(score)

    messages = {
        "Low": "Ocean conditions are relatively stable.",
        "Moderate": "Some environmental stress is detected. Continue monitoring.",
        "High": "Significant environmental stress detected. Further assessment is recommended.",
        "Critical": "Very high environmental risk detected. Prompt expert assessment is recommended.",
    }

    return {
        "region": region,
        "risk_score": round(float(score), 2),
        "alert_level": level,
        "message": messages[level],
        "requires_attention": level in ("High", "Critical"),
    }
