
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.compare import compare_regions


def sample_regions():
    region_a = {
        "name": "Gulf of Mannar",
        "metrics": {
            "temperature_anomaly": {
                "value": 1.2,
                "unit": "°C",
                "source": "NOAA"
            }
        }
    }

    region_b = {
        "name": "Palk Bay",
        "metrics": {
            "temperature_anomaly": {
                "value": 0.8,
                "unit": "°C",
                "source": "NOAA"
            }
        }
    }

    return region_a, region_b


def test_basic_comparison():
    a, b = sample_regions()
    result = compare_regions(a, b)

    assert result["status"] == "available"
    assert result["comparisons"]["temperature_anomaly"]["higher_value_region"] == "Gulf of Mannar"


def test_difference():
    a, b = sample_regions()
    result = compare_regions(a, b)

    assert result["comparisons"]["temperature_anomaly"]["difference"] == 0.4


def test_incompatible_units():
    a, b = sample_regions()
    b["metrics"]["temperature_anomaly"]["unit"] = "K"

    result = compare_regions(a, b)

    assert result["status"] == "no comparable metrics"


def test_missing_values():
    a, b = sample_regions()
    b["metrics"]["temperature_anomaly"]["value"] = None

    result = compare_regions(a, b)

    assert result["status"] == "no comparable metrics"


def test_synthetic_flag():
    a, b = sample_regions()
    b["synthetic"] = True

    result = compare_regions(a, b)

    assert result["synthetic"] is True


def test_same_region_rejected():
    a, b = sample_regions()
    b["name"] = a["name"]

    try:
        compare_regions(a, b)
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [
        value for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]

    for test in tests:
        test()

    print(f"All {len(tests)} comparison tests passed!")
