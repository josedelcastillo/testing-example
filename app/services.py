"""Caso de uso: registrar un pedido.

Orquesta el repositorio, las reglas de precio y la pasarela de pagos.
Recibe sus dependencias por constructor, lo que permite reemplazarlas
por mocks en las pruebas unitarias.
"""

import uuid

from app.models import Order, OrderLine
from app.payments import PaymentGateway
from app.pricing import calculate_totals


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class OrderService:
    def __init__(self, repository, payment_gateway: PaymentGateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def place_order(self, customer_type: str, items: list[tuple[str, int]]) -> Order:
        products = {}
        for sku, quantity in items:
            product = self.repository.get_product(sku)
            if product is None:
                raise ProductNotFoundError(sku)
            if product.stock < quantity:
                raise InsufficientStockError(sku)
            products[sku] = product

        totals = calculate_totals(
            [(products[sku].price, quantity) for sku, quantity in items], customer_type
        )

        try:
            for sku, quantity in items:
                # Revalida en la BD: otro pedido concurrente pudo consumir el stock.
                if not self.repository.decrease_stock(sku, quantity):
                    raise InsufficientStockError(sku)
            # Se cobra al final: si algo falló antes, no se cobra al cliente.
            payment_id = self.payment_gateway.charge(totals.total, reference=str(uuid.uuid4()))
            order = self.repository.save_order(
                Order(
                    customer_type=customer_type,
                    subtotal=totals.subtotal,
                    discount=totals.discount,
                    igv=totals.igv,
                    total=totals.total,
                    payment_id=payment_id,
                    lines=[
                        OrderLine(sku=sku, quantity=quantity, unit_price=products[sku].price)
                        for sku, quantity in items
                    ],
                )
            )
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
        return order
