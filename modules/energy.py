
"""BlueEnergy: illustrative seaweed-to-biogas energy calculations.

These are scenario estimates, not measured or guaranteed energy production.
"""

import math

METHANE_KWH_PER_M3 = 9.94


def _validate_number(value, name, minimum=None, maximum=None):
    """Validate numeric inputs and reject bool, NaN and infinity."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must not exceed {maximum}.")

    return float(value)


def energy_estimate(
    dry_biomass_kg,
    methane_yield,
    electrical_efficiency,
    days,
    parasitic_load_fraction=0.15
):
    """
    Estimate illustrative energy potential from dry seaweed biomass.

    Parameters:
    - dry_biomass_kg: Dry biomass in kg.
    - methane_yield: Methane yield in m3 per kg dry biomass.
    - electrical_efficiency: Electrical conversion efficiency (0-1).
    - days: Scenario duration in days.
    - parasitic_load_fraction: Fraction of gross electricity
      consumed by processing and auxiliary systems (0-1).

    Returns gross and net energy estimates and their assumptions.
    """

    # 1. Validate inputs
    dry_biomass_kg = _validate_number(
        dry_biomass_kg, "Dry biomass", 0
    )

    methane_yield = _validate_number(
        methane_yield, "Methane yield", 0
    )

    electrical_efficiency = _validate_number(
        electrical_efficiency, "Efficiency", 0, 1
    )

    days = _validate_number(days, "Days", 0)

    if days <= 0:
        raise ValueError("Days must be greater than zero.")

    parasitic_load_fraction = _validate_number(
        parasitic_load_fraction,
        "Parasitic load fraction",
        0,
        1
    )

    # 2. Estimate methane production
    methane_m3 = dry_biomass_kg * methane_yield

    # 3. Calculate gross chemical energy
    gross_energy = methane_m3 * METHANE_KWH_PER_M3

    # 4. Calculate gross electricity
    gross_electricity = gross_energy * electrical_efficiency

    # 5. Estimate auxiliary energy consumption
    parasitic_energy = (
        gross_electricity * parasitic_load_fraction
    )

    # 6. Calculate net usable electricity
    net_electricity = gross_electricity - parasitic_energy

    # 7. Calculate average power
    total_hours = days * 24

    average_gross_power = gross_electricity / total_hours
    average_net_power = net_electricity / total_hours

    return {
        "methane_m3": methane_m3,
        "gross_energy_kwh": gross_energy,

        # Legacy dashboard compatibility
        "electricity_kwh": gross_electricity,
        "average_power_kw": average_gross_power,

        "gross_electricity_kwh": gross_electricity,
        "parasitic_energy_kwh": parasitic_energy,
        "net_usable_electricity_kwh": net_electricity,
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
