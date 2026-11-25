
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.alerts import classify_risk, generate_alert


def test_risk_classification():
    assert classify_risk(10) == "Low"
    assert classify_risk(40) == "Moderate"
    assert classify_risk(60) == "High"
    assert classify_risk(90) == "Critical"


def test_boundary_values():
    assert classify_risk(25) == "Low"
    assert classify_risk(50) == "Moderate"
    assert classify_risk(75) == "High"
    assert classify_risk(100) == "Critical"


def test_alert_generation():
    alert = generate_alert(85, "Gulf of Mannar")

    assert alert["region"] == "Gulf of Mannar"
    assert alert["alert_level"] == "Critical"
    assert alert["requires_attention"] is True


def test_low_risk_alert():
    alert = generate_alert(15)

    assert alert["alert_level"] == "Low"
    assert alert["requires_attention"] is False


def test_invalid_scores():
    for score in [-1, 101, True, "high"]:
        try:
            classify_risk(score)
            assert False, f"Expected ValueError for {score}"
        except ValueError:
            pass


if __name__ == "__main__":
    tests = [
        value for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]

    for test in tests:
        test()

    print(f"All {len(tests)} alert tests passed!")
