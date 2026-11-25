
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.pollution import analyse_chlorophyll


def test_normal_values():
    result = analyse_chlorophyll([0.2, 0.4, 0.6])

    assert result["status"] == "available"
    assert result["average"] == 0.4
    assert result["measurement_count"] == 3


def test_minimum_and_maximum():
    result = analyse_chlorophyll([0.1, 0.5, 1.0])

    assert result["minimum"] == 0.1
    assert result["maximum"] == 1.0


def test_missing_values():
    result = analyse_chlorophyll([None, None])

    assert result["status"] == "unavailable"


def test_empty_values():
    result = analyse_chlorophyll([])

    assert result["status"] == "unavailable"


def test_invalid_values():
    result = analyse_chlorophyll([-1, True, "high", float("nan")])

    assert result["status"] == "unavailable"


def test_scientific_limitation():
    result = analyse_chlorophyll([0.3, 0.5])

    assert "cannot establish pollution" in result["limitation"]


if __name__ == "__main__":
    tests = [
        value for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]

    for test in tests:
        test()

    print(f"All {len(tests)} pollution tests passed!")
