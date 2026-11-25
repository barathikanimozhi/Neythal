
"""OceanCompare: compare environmental measurements across regions."""


def compare_regions(region_a, region_b):
    """
    Compare two regional metric summaries.

    Expected structure:
    {
        "name": "Region name",
        "metrics": {
            "temperature_anomaly": {
                "value": 0.8,
                "unit": "°C",
                "source": "NOAA"
            }
        },
        "synthetic": False
    }
    """

    if not isinstance(region_a, dict) or not isinstance(region_b, dict):
        raise ValueError("Both regions must be dictionaries.")

    name_a = region_a.get("name")
    name_b = region_b.get("name")

    if not name_a or not name_b:
        raise ValueError("Both regions must have names.")

    if name_a == name_b:
        raise ValueError("Choose two different regions.")

    metrics_a = region_a.get("metrics", {})
    metrics_b = region_b.get("metrics", {})

    if not isinstance(metrics_a, dict) or not isinstance(metrics_b, dict):
        raise ValueError("Region metrics must be dictionaries.")

    results = {}

    common_metrics = set(metrics_a) & set(metrics_b)

    for metric in sorted(common_metrics):
        a = metrics_a[metric]
        b = metrics_b[metric]

        if not isinstance(a, dict) or not isinstance(b, dict):
            continue

        value_a = a.get("value")
        value_b = b.get("value")
        unit_a = a.get("unit")
        unit_b = b.get("unit")

        if value_a is None or value_b is None:
            continue

        if isinstance(value_a, bool) or isinstance(value_b, bool):
            continue

        if not isinstance(value_a, (int, float)):
            continue

        if not isinstance(value_b, (int, float)):
            continue

        if unit_a != unit_b:
            continue

        if not unit_a:
            continue

        if value_a > value_b:
            higher = name_a
        elif value_b > value_a:
            higher = name_b
        else:
            higher = "Equal"

        results[metric] = {
            "region_a_value": value_a,
            "region_b_value": value_b,
            "unit": unit_a,
            "difference": round(abs(value_a - value_b), 4),
            "higher_value_region": higher,
            "region_a_source": a.get("source", "Not specified"),
            "region_b_source": b.get("source", "Not specified"),
        }

    return {
        "region_a": name_a,
        "region_b": name_b,
        "comparisons": results,
        "synthetic": bool(
            region_a.get("synthetic", False)
            or region_b.get("synthetic", False)
        ),
        "status": "available" if results else "no comparable metrics",
    }
