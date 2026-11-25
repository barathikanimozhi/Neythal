
import os
import sys
import math

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.energy import energy_estimate


def raises(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_normal_energy_estimate():
    result = energy_estimate(1000, 0.20, 0.35, 30)

    assert result["methane_m3"] == 200
    assert result["gross_energy_kwh"] == 1988
    assert result["electricity_kwh"] == 695.8

    assert math.isclose(
        result["net_usable_electricity_kwh"],
        591.43
    )


def test_zero_parasitic_load():
    result = energy_estimate(1000, 0.20, 0.35, 30, 0)

    assert result["parasitic_energy_kwh"] == 0
    assert result["net_usable_electricity_kwh"] == result["electricity_kwh"]


def test_full_parasitic_load():
    result = energy_estimate(1000, 0.20, 0.35, 30, 1)

    assert result["net_usable_electricity_kwh"] == 0


def test_dashboard_compatibility():
    result = energy_estimate(1000, 0.20, 0.35, 30)

    assert result["electricity_kwh"] == result["gross_electricity_kwh"]
    assert result["average_power_kw"] == result["average_gross_power_kw"]


def test_invalid_inputs():
    assert raises(energy_estimate, -1, 0.2, 0.3, 10)
    assert raises(energy_estimate, 10, -0.2, 0.3, 10)
    assert raises(energy_estimate, 10, 0.2, 1.5, 10)
    assert raises(energy_estimate, 10, 0.2, 0.3, 0)
    assert raises(energy_estimate, 10, 0.2, 0.3, 10, 1.5)
    assert raises(energy_estimate, True, 0.2, 0.3, 10)


if __name__ == "__main__":
    tests = [
        value for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]

    for test in tests:
        test()

    print(f"All {len(tests)} energy tests passed!")
