"""Prototype model engine. Screening / scenario maths only, not validated science."""
import math

METHANE_KWH_PER_M3 = 9.94   # illustrative energy-content assumption
C_TO_CO2E = 44.0 / 12.0     # tonnes of carbon -> tonnes of CO2 equivalent
# OceanRisk model configuration
RISK_WEIGHTS = {
    "thermal": 0.60,
    "habitat": 0.25,
    "pollution": 0.15,
}

RISK_MAXIMUMS = {
    name: weight * 100
    for name, weight in RISK_WEIGHTS.items()
}

THERMAL_POINTS_PER_C = 25.0
def clip(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def _num(value, name, lo=None, hi=None):
    """Reject bool, NaN, inf, non-numbers and out-of-range values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        raise ValueError(f"{name} must be between {lo} and {hi}.")
    return float(value)



def ocean_risk_score(sst_anomaly, habitat_pressure=0, pollution_pressure=0):
    """
    Calculate an explainable environmental monitoring-priority score.

    Thermal contribution: 0-60 points
    Habitat contribution: 0-25 points
    Pollution contribution: 0-15 points

    SST anomaly is measured in degrees Celsius.
    Habitat and pollution pressures are indices from 0-100.

    Missing SST anomaly returns None.
    """

    # Step 1: Validate inputs
    if sst_anomaly is None:
        return None

    sst_anomaly = _num(sst_anomaly, "SST anomaly", -15, 15)

    habitat_pressure = _num(
        habitat_pressure, "Habitat pressure", 0, 100
    )

    pollution_pressure = _num(
        pollution_pressure, "Pollution pressure", 0, 100
    )

    # Step 2: Calculate individual contributions
    thermal = clip(
    max(0, sst_anomaly) * THERMAL_POINTS_PER_C,
    0,
    RISK_MAXIMUMS["thermal"]
)

    habitat = clip(
        habitat_pressure / 100 * RISK_MAXIMUMS["habitat"],
        0,
        RISK_MAXIMUMS["habitat"]
    )

    pollution = clip(
        pollution_pressure / 100 * RISK_MAXIMUMS["pollution"],
        0,
        RISK_MAXIMUMS["pollution"]
    )

    # Step 3: Calculate total score
    raw_score = thermal + habitat + pollution
    final_score = round(clip(raw_score))

    # Step 4: Return explainable results
    return {
        "score": final_score,
        "unrounded_score": round(raw_score, 2),
        "thermal_component": round(thermal, 2),
        "habitat_component": round(habitat, 2),
        "pollution_component": round(pollution, 2),
        "weights": RISK_WEIGHTS.copy(),
        "maximum_contributions": RISK_MAXIMUMS.copy(),
        "inputs": {
            "sst_anomaly_c": sst_anomaly,
            "habitat_pressure": habitat_pressure,
            "pollution_pressure": pollution_pressure,
        },
        "method": "Weighted additive screening score",
        "limitation": (
            "Prototype monitoring-priority index, "
            "not a validated ecological damage prediction."
        ),
    }



def energy_estimate(
    dry_biomass_kg,
    methane_yield,
    electrical_efficiency,
    days,
    parasitic_load_fraction=0.15
):
    """
    Estimate illustrative energy potential from dry seaweed biomass.

    Inputs:
    - dry_biomass_kg: dry biomass in kg
    - methane_yield: m3 methane per kg dry biomass
    - electrical_efficiency: conversion efficiency (0-1)
    - days: scenario duration
    - parasitic_load_fraction: assumed fraction of gross
      electricity consumed by processing and auxiliary systems

    Outputs distinguish gross chemical energy, gross electricity
    and net usable electricity.

    This is a scenario estimate, not actual energy production.
    """

    # Step 1: Validate inputs
    dry_biomass_kg = _num(
        dry_biomass_kg, "Dry biomass", 0
    )

    methane_yield = _num(
        methane_yield, "Methane yield", 0
    )

    electrical_efficiency = _num(
        electrical_efficiency, "Efficiency", 0, 1
    )

    days = _num(days, "Days")

    if days <= 0:
        raise ValueError("Days must be greater than zero.")

    parasitic_load_fraction = _num(
        parasitic_load_fraction,
        "Parasitic load fraction",
        0,
        1
    )

    # Step 2: Estimate methane volume
    methane_m3 = dry_biomass_kg * methane_yield

    # Step 3: Calculate gross chemical energy
    gross_energy = methane_m3 * METHANE_KWH_PER_M3

    # Step 4: Calculate gross electricity
    gross_electricity = gross_energy * electrical_efficiency

    # Step 5: Estimate auxiliary energy consumption
    parasitic_energy = (
        gross_electricity * parasitic_load_fraction
    )

    # Step 6: Calculate net usable electricity
    net_electricity = gross_electricity - parasitic_energy

    # Step 7: Calculate average power
    total_hours = days * 24

    average_gross_power = gross_electricity / total_hours
    average_net_power = net_electricity / total_hours

    return {
        "methane_m3": methane_m3,

        "gross_energy_kwh": gross_energy,

        "electricity_kwh": gross_electricity,

        "gross_electricity_kwh": gross_electricity,

        "parasitic_energy_kwh": parasitic_energy,

        "net_usable_electricity_kwh": net_electricity,

        "average_power_kw": average_gross_power,

        "average_gross_power_kw": average_gross_power,

        "average_net_power_kw": average_net_power,

        "assumptions": {
            "methane_energy_content_kwh_per_m3": METHANE_KWH_PER_M3,
            "methane_yield_m3_per_kg": methane_yield,
            "electrical_efficiency": electrical_efficiency,
            "parasitic_load_fraction": parasitic_load_fraction,
        },

        "interpretation": (
            "Illustrative scenario estimate, not measured "
            "or guaranteed energy production."
        ),
    }



def blue_carbon_estimate(area_hectares, annual_rate, years):
    """
    Estimate cumulative blue carbon accumulation.

    Parameters:
    - area_hectares: Ecosystem area in hectares.
    - annual_rate: Annual accumulation rate in either:
        tC/ha/year or tCO2e/ha/year.
    - years: Scenario duration in years.

    Returns:
    - Estimated cumulative amount in the SAME unit
      used by annual_rate.

    Important:
    This is a scenario estimate, not a measured
    carbon inventory or guaranteed sequestration.
    """

    # Step 1: Validate inputs
    area_hectares = _num(
        area_hectares, "Area", 0
    )

    annual_rate = _num(
        annual_rate, "Annual rate", 0
    )

    years = _num(
        years, "Years", 0
    )

    if years <= 0:
        raise ValueError("Years must be greater than zero.")

    # Step 2: Calculate cumulative carbon
    total_carbon = area_hectares * annual_rate * years

    return round(total_carbon, 4)


def tc_to_tco2e(tonnes_carbon):
    return _num(tonnes_carbon, "Tonnes of carbon", 0) * C_TO_CO2E


def ocean_future_scenario(
    base_anomaly,
    warming,
    habitat_pressure,
    pollution_pressure
):
    """
    Calculate a hypothetical future ocean-risk scenario.

    Parameters:
    - base_anomaly: Current SST anomaly in Celsius.
    - warming: Additional hypothetical warming in Celsius.
    - habitat_pressure: Habitat pressure index (0-100).
    - pollution_pressure: Pollution pressure index (0-100).

    Returns:
    - Explainable future risk score and scenario information.

    This is a screening scenario, not a climate forecast.
    """

    # Step 1: Handle missing temperature data
    if base_anomaly is None:
        return None

    # Step 2: Validate inputs
    base_anomaly = _num(
        base_anomaly, "Base anomaly", -15, 15
    )

    warming = _num(
        warming, "Warming", 0, 10
    )

    # Step 3: Calculate hypothetical future anomaly
    raw_future_anomaly = base_anomaly + warming

    # Keep within the supported model range
    future_anomaly = min(raw_future_anomaly, 15)

    # Step 4: Calculate future risk
    result = ocean_risk_score(
        future_anomaly,
        habitat_pressure,
        pollution_pressure
    )

    # Step 5: Add scenario transparency
    result["scenario"] = {
        "base_anomaly_c": base_anomaly,
        "additional_warming_c": warming,
        "scenario_anomaly_c": future_anomaly,
        "uncapped_anomaly_c": raw_future_anomaly,
        "was_capped": raw_future_anomaly > 15,
        "type": "Hypothetical warming scenario"
    }

    result["limitation"] = (
        "Hypothetical screening scenario, not a validated "
        "climate forecast or ecological damage prediction."
    )

    return result