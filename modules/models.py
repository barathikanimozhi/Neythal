"""Prototype model engine. Screening / scenario maths only, not validated science."""
import math

METHANE_KWH_PER_M3 = 9.94   # illustrative energy-content assumption
C_TO_CO2E = 44.0 / 12.0     # tonnes of carbon -> tonnes of CO2 equivalent


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
    """Prototype monitoring-priority score (0-100). Missing anomaly -> None, never 0."""
    if sst_anomaly is None:
        return None
    sst_anomaly = _num(sst_anomaly, "SST anomaly", -15, 15)
    habitat_pressure = _num(habitat_pressure, "Habitat pressure", 0, 100)
    pollution_pressure = _num(pollution_pressure, "Pollution pressure", 0, 100)

    thermal = clip(max(0, sst_anomaly) * 25, 0, 60)
    habitat = clip(habitat_pressure * 0.25, 0, 25)
    pollution = clip(pollution_pressure * 0.15, 0, 15)
    return {
        "score": round(clip(thermal + habitat + pollution)),
        "thermal_component": round(thermal, 2),
        "habitat_component": round(habitat, 2),
        "pollution_component": round(pollution, 2),
    }


def energy_estimate(dry_biomass_kg, methane_yield, electrical_efficiency, days):
    """Gross electricity BEFORE parasitic loads. methane_yield is m3 per kg dry biomass."""
    dry_biomass_kg = _num(dry_biomass_kg, "Dry biomass", 0)
    methane_yield = _num(methane_yield, "Methane yield", 0)
    electrical_efficiency = _num(electrical_efficiency, "Efficiency", 0, 1)
    days = _num(days, "Days")
    if days <= 0:
        raise ValueError("Days must be greater than zero.")

    methane_m3 = dry_biomass_kg * methane_yield
    gross = methane_m3 * METHANE_KWH_PER_M3
    electricity = gross * electrical_efficiency
    return {
        "methane_m3": methane_m3,
        "gross_energy_kwh": gross,
        "electricity_kwh": electricity,
        "average_power_kw": electricity / (days * 24),
    }


def blue_carbon_estimate(area_hectares, annual_rate, years):
    """Scenario total in the SAME unit as annual_rate (tC or tCO2e). Never mix them."""
    area_hectares = _num(area_hectares, "Area", 0)
    annual_rate = _num(annual_rate, "Annual rate", 0)
    years = _num(years, "Years")
    if years <= 0:
        raise ValueError("Years must be greater than zero.")
    return area_hectares * annual_rate * years


def tc_to_tco2e(tonnes_carbon):
    return _num(tonnes_carbon, "Tonnes of carbon", 0) * C_TO_CO2E


def ocean_future_scenario(base_anomaly, warming, habitat_pressure, pollution_pressure):
    if base_anomaly is None:
        return None
    base_anomaly = _num(base_anomaly, "Base anomaly", -15, 15)
    warming = _num(warming, "Warming", 0, 10)
    return ocean_risk_score(min(base_anomaly + warming, 15), habitat_pressure, pollution_pressure)
