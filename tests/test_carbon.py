
import os
import sys
import math

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.carbon import (
    blue_carbon_estimate,
    tc_to_tco2e
)


def raises(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_normal_carbon_estimate():
    assert blue_carbon_estimate(10, 1, 5) == 50


def test_zero_area():
    assert blue_carbon_estimate(0, 2, 10) == 0


def test_zero_annual_rate():
    assert blue_carbon_estimate(10, 0, 5) == 0


def test_carbon_conversion():
    assert math.isclose(
        tc_to_tco2e(1),
        44 / 12
    )


def test_invalid_inputs():
    assert raises(blue_carbon_estimate, -1, 1, 5)
    assert raises(blue_carbon_estimate, 10, -1, 5)
    assert raises(blue_carbon_estimate, 10, 1, 0)
    assert raises(blue_carbon_estimate, True, 1, 5)
    assert raises(tc_to_tco2e, -1)
    assert raises(tc_to_tco2e, float("nan"))


if __name__ == "__main__":
    tests = [
        value for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    ]

    for test in tests:
        test()

    print(f"All {len(tests)} carbon tests passed!")
