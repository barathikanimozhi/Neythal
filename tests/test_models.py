import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.models import (ocean_risk_score, energy_estimate, blue_carbon_estimate,
                            ocean_future_scenario, tc_to_tco2e)


def raises(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


def test_ocean_risk():
    r = ocean_risk_score(1.0, 20, 10)
    assert r["score"] == 32 and r["thermal_component"] == 25


def test_energy():
    r = energy_estimate(1000, 0.20, 0.35, 30)
    assert r["methane_m3"] == 200 and round(r["electricity_kwh"], 2) == 695.8


def test_carbon():
    assert blue_carbon_estimate(10, 1, 5) == 50
    assert round(tc_to_tco2e(1), 3) == 3.667


def test_future():
    assert ocean_future_scenario(0.5, 1.0, 20, 10)["score"] == 44


def test_missing_data_is_not_zero():
    assert ocean_risk_score(None) is None and ocean_future_scenario(None, 1, 0, 0) is None


def test_validation():
    nan, inf = float("nan"), float("inf")
    assert raises(ocean_risk_score, nan)
    assert raises(ocean_risk_score, 1, 150, 0)
    assert raises(ocean_risk_score, True)
    assert raises(energy_estimate, -1, 0.2, 0.3, 10)
    assert raises(energy_estimate, 10, 0.2, 1.5, 10)
    assert raises(energy_estimate, 10, 0.2, 0.3, 0)
    assert raises(energy_estimate, inf, 0.2, 0.3, 10)
    assert raises(blue_carbon_estimate, 1, 1, 0)
    assert raises(ocean_future_scenario, 0.5, -1, 0, 0)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("All Neythal model tests passed!")
