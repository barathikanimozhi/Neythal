
"""BlueCarbon: illustrative blue-carbon scenario calculations."""

import math

C_TO_CO2E = 44.0 / 12.0


def _validate_number(value, name, minimum=None):
    """Validate numeric inputs."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    return float(value)


def blue_carbon_estimate(area_hectares, annual_rate, years):
    """
    Estimate cumulative blue-carbon accumulation.

    Parameters:
    - area_hectares: Ecosystem area in hectares.
    - annual_rate: Annual accumulation rate in either
      tC/ha/year or tCO2e/ha/year.
    - years: Scenario duration in years.

    Returns:
    Estimated cumulative amount in the same unit as annual_rate.

    This is a scenario estimate, not a measured carbon inventory.
    """

    area_hectares = _validate_number(
        area_hectares, "Area", 0
    )

    annual_rate = _validate_number(
        annual_rate, "Annual rate", 0
    )

    years = _validate_number(
        years, "Years", 0
    )

    if years <= 0:
        raise ValueError("Years must be greater than zero.")

    total_carbon = area_hectares * annual_rate * years

    return round(total_carbon, 4)


def tc_to_tco2e(tonnes_carbon):
    """
    Convert tonnes of carbon into tonnes of CO2 equivalent.

    Uses the molecular mass ratio 44/12.
    """

    tonnes_carbon = _validate_number(
        tonnes_carbon, "Tonnes of carbon", 0
    )

    return tonnes_carbon * C_TO_CO2E
