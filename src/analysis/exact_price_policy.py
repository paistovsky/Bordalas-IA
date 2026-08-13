from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def exact_euro(value: Any) -> int:
    """
    Importe económico al euro más cercano.

    No redondea a miles/10.000 y no añade ruido pseudoaleatorio.
    """
    value = max(_decimal(value), Decimal("0"))
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def floor_euro(value: Any) -> int:
    """
    Techo económico conservador: nunca supera el valor matemático.

    Útil para max_rational, de forma que el redondeo no rompa el ROI mínimo.
    """
    value = max(_decimal(value), Decimal("0"))
    return int(value.quantize(Decimal("1"), rounding=ROUND_FLOOR))


def apply_percent_exact(base_amount: int, percent: Any) -> int:
    """
    Aplica un porcentaje exacto y devuelve euros enteros.

    Ejemplo:
      1.350.000 * 1,03 = 1.390.500
    """
    base = _decimal(base_amount)
    pct = _decimal(percent)
    return exact_euro(base * (Decimal("1") + pct / Decimal("100")))


def apply_ratio_exact(base_amount: int, ratio: Any) -> int:
    """
    Aplica un ratio decimal (0.03 == 3%) con precisión al euro.
    """
    base = _decimal(base_amount)
    ratio_dec = _decimal(ratio)
    return exact_euro(base * (Decimal("1") + ratio_dec))
