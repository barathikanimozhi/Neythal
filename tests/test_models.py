
import os
import sys
import math

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from modules.models import (
    ocean_risk_score,
    energy_estimate,
    blue_carbon_estimate,
    ocean_future_scenario,
    tc_to_tco2e
)


def raises(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return True
    return False


# 1. OceanRisk tests

def test_ocean_risk():
    result = ocean_risk_score(1.0, 20, 10)

    assert result["score"] == 32
    assert result["thermal_component"] == 25
    assert result["habitat_component"] == 5
    assert result["pollution_component"] == 1.5
    assert result["unrounded_score"] == 31.5


def test_ocean_risk_boundaries():
    result = ocean_risk_score(-2, 0, 0)
    assert result["score"] == 0

    result = ocean_risk_score(15, 100, 100)
    assert result["score"] == 100


# 2. BlueEnergy tests

def test_energy():
    result = energy_estimate(1000, 0.20, 0.35, 30)

    assert result["methane_m3"] == 200
    assert result["gross_energy_kwh"] == 1988
    assert result["electricity_kwh"] == 695.8
    assert math.isclose(
        result["net_usable_electricity_kwh"],
        591.43
    )


def test_energy_zero_parasitic_load():
    result = energy_estimate(1000, 0.20, 0.35, 30, 0)

    assert result["parasitic_energy_kwh"] == 0
    assert result["net_usable_electricity_kwh"] == result["electricity_kwh"]


def test_energy_full_parasitic_load():
    result = energy_estimate(1000, 0.20, 0.35, 30, 1)

    assert result["net_usable_electricity_kwh"] == 0
    assert result["parasitic_energy_kwh"] == result["electricity_kwh"]


def test_energy_compatibility():
    result = energy_estimate(1000, 0.20, 0.35, 30)

    assert result["electricity_kwh"] == result["gross_electricity_kwh"]
    assert result["average_power_kw"] == result["average_gross_power_kw"]


# 3. BlueCarbon tests

def test_carbon():
    assert blue_carbon_estimate(10, 1, 5) == 50
    assert math.isclose(tc_to_tco2e(1), 44 / 12)


def test_carbon_zero_area():
    assert blue_carbon_estimate(0, 2, 10) == 0


# 4. OceanFuture tests

def test_future():
    result = ocean_future_scenario(0.5, 1.0, 20, 10)

    assert result["score"] == 44
    assert result["scenario"]["scenario_anomaly_c"] == 1.5


def test_future_temperature_cap():
    result = ocean_future_scenario(14, 5, 20, 10)

    assert result["scenario"]["scenario_anomaly_c"] == 15
    assert result["scenario"]["uncapped_anomaly_c"] == 19
    assert result["scenario"]["was_capped"] is True


# 5. Missing data tests

def test_missing_data_is_not_zero():
    assert ocean_risk_score(None) is None
    assert ocean_future_scenario(None, 1, 0, 0) is None


# 6. Input validation tests

def test_validation():
    nan = float("nan")
    inf = float("inf")

    assert raises(ocean_risk_score, nan)
    assert raises(ocean_risk_score, 1, 150, 0)
    assert raises(ocean_risk_score, True)

    assert raises(energy_estimate, -1, 0.2, 0.3, 10)
    assert raises(energy_estimate, 10, 0.2, 1.5, 10)
    assert raises(energy_estimate, 10, 0.2, 0.3, 0)
    assert raises(energy_estimate, inf, 0.2, 0.3, 10)
    assert raises(energy_estimate, 10, 0.2, 0.3, 10, 1.5)

    assert raises(blue_carbon_estimate, 1, 1, 0)
    assert raises(blue_carbon_estimate, -1, 1, 5)

    assert raises(tc_to_tco2e, -1)

    assert raises(ocean_future_scenario, 0.5, -1, 0, 0)
    assert raises(ocean_future_scenario, 0.5, 1, 150, 0)


if __name__ == "__main__":
    test_functions = [
        value for name, value in list(globals().items())
        if name.startswith("test_") and callable(value)
    ]

    for test in test_functions:
        test()

    print(f"All {len(test_functions)} Neythal model tests passed!")
