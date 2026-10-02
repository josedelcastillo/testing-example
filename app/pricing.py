"""Reglas de negocio puras para calcular el total de un pedido.

No dependen de base de datos ni de red: son el candidato ideal para
pruebas unitarias rápidas y deterministas.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

IGV_RATE = Decimal("0.18")  # Impuesto General a las Ventas (Perú)

CUSTOMER_DISCOUNTS = {
    "REGULAR": Decimal("0.00"),
    "FRECUENTE": Decimal("0.05"),
    "VIP": Decimal("0.10"),
}
VOLUME_THRESHOLD = Decimal("500.00")
VOLUME_DISCOUNT = Decimal("0.05")
MAX_DISCOUNT = Decimal("0.15")


@dataclass(frozen=True)
class OrderTotals:
    subtotal: Decimal
    discount: Decimal
    igv: Decimal
    total: Decimal


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_subtotal(lines: list[tuple[Decimal, int]]) -> Decimal:
    """Suma precio_unitario * cantidad de cada línea."""
    if not lines:
        raise ValueError("El pedido debe tener al menos una línea")
    subtotal = Decimal("0")
    for unit_price, quantity in lines:
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        if unit_price < 0:
            raise ValueError("El precio no puede ser negativo")
        subtotal += unit_price * quantity
    return round_money(subtotal)


def discount_rate(customer_type: str, subtotal: Decimal) -> Decimal:
    """Descuento por tipo de cliente + descuento por volumen, con tope."""
    try:
        rate = CUSTOMER_DISCOUNTS[customer_type]
    except KeyError:
        raise ValueError(f"Tipo de cliente desconocido: {customer_type}") from None
    if subtotal >= VOLUME_THRESHOLD:
        rate += VOLUME_DISCOUNT
    return min(rate, MAX_DISCOUNT)


def calculate_totals(lines: list[tuple[Decimal, int]], customer_type: str) -> OrderTotals:
    subtotal = calculate_subtotal(lines)
    discount = round_money(subtotal * discount_rate(customer_type, subtotal))
    taxable = subtotal - discount
    igv = round_money(taxable * IGV_RATE)
    return OrderTotals(subtotal=subtotal, discount=discount, igv=igv, total=taxable + igv)
