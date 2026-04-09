from __future__ import annotations

from dataclasses import dataclass


class UnitConversionError(ValueError):
    pass


@dataclass(frozen=True)
class ConversionResult:
    value: float
    unit: str


def _norm_unit(unit: str) -> str:
    return unit.strip().lower()


_ENERGY_TO_KWH = {
    "kwh": 1.0,
    "wh": 1.0 / 1000.0,
    "mwh": 1000.0,
}

_DIST_TO_KM = {
    "km": 1.0,
    "m": 1.0 / 1000.0,
    "mi": 1.609344,
    "mile": 1.609344,
    "miles": 1.609344,
}

_VOLUME_TO_LITRE = {
    "l": 1.0,
    "litre": 1.0,
    "liter": 1.0,
    "litres": 1.0,
    "liters": 1.0,
    "ml": 1.0 / 1000.0,
}

_MASS_TO_KG = {
    "kg": 1.0,
    "g": 1.0 / 1000.0,
    "tonne": 1000.0,
    "tonnes": 1000.0,
    "t": 1000.0,
}


def convert_quantity(value: float, from_unit: str, to_unit: str) -> ConversionResult:
    """
    Convert between common units used in emissions activity data.
    Supported families: energy (Wh/kWh/MWh), distance (m/km/mi), volume (ml/l), mass (g/kg/tonne).
    """
    fu = _norm_unit(from_unit)
    tu = _norm_unit(to_unit)
    if fu == tu:
        return ConversionResult(value=value, unit=to_unit)

    for mapping, canonical in (
        (_ENERGY_TO_KWH, "kwh"),
        (_DIST_TO_KM, "km"),
        (_VOLUME_TO_LITRE, "litre"),
        (_MASS_TO_KG, "kg"),
    ):
        if fu in mapping and tu in mapping:
            canonical_value = value * mapping[fu]
            converted_value = canonical_value / mapping[tu]
            return ConversionResult(value=converted_value, unit=to_unit)

    raise UnitConversionError(f"Unsupported conversion: {from_unit} -> {to_unit}")


def calculate_co2e(activity_quantity: float, activity_unit: str, factor_value: float, factor_unit: str) -> float:
    """
    CO2e (kg) = activity_quantity * emission_factor (kgCO2e / factor_unit)
    If activity unit differs from factor unit, we convert quantity to factor unit first.
    """
    q = convert_quantity(activity_quantity, activity_unit, factor_unit).value
    return q * factor_value
