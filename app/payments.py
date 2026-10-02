"""Pasarela de pagos. En producción sería un servicio externo (HTTP)."""

import uuid
from decimal import Decimal
from typing import Protocol


class PaymentDeclinedError(Exception):
    pass


class PaymentGateway(Protocol):
    def charge(self, amount: Decimal, reference: str) -> str:
        """Cobra el monto y devuelve el id de la transacción."""


class FakePaymentGateway:
    """Simulador usado en desarrollo y pruebas de integración.

    Rechaza montos mayores al límite para poder probar el camino de error.
    """

    def __init__(self, limit: Decimal = Decimal("10000.00")):
        self.limit = limit
        self.charges: list[tuple[Decimal, str]] = []

    def charge(self, amount: Decimal, reference: str) -> str:
        if amount > self.limit:
            raise PaymentDeclinedError(f"Monto {amount} excede el límite")
        self.charges.append((amount, reference))
        return f"pay_{uuid.uuid4().hex[:12]}"
