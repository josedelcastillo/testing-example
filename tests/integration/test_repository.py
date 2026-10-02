"""Integración repositorio ↔ PostgreSQL.

Estas pruebas verifican cosas que un mock NO puede garantizar:
mapeo ORM, constraints, tipos NUMERIC y SQL real.
"""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Order, OrderLine

pytestmark = pytest.mark.integration


def test_guarda_y_recupera_producto(repository):
    repository.add_product("LAP-01", "Laptop", Decimal("3499.90"), 5)
    repository.commit()

    product = repository.get_product("LAP-01")

    assert product.name == "Laptop"
    assert product.price == Decimal("3499.90")  # NUMERIC conserva decimales exactos
    assert product.stock == 5


def test_sku_duplicado_viola_constraint_unique(repository):
    repository.add_product("DUP-01", "Uno", Decimal("1.00"), 1)

    with pytest.raises(IntegrityError):
        repository.add_product("DUP-01", "Otro", Decimal("2.00"), 1)


def test_decrease_stock_descuenta_si_alcanza(repository):
    repository.add_product("MOU-01", "Mouse", Decimal("49.90"), 3)

    assert repository.decrease_stock("MOU-01", 2) is True
    repository.session.expire_all()
    assert repository.get_product("MOU-01").stock == 1


def test_decrease_stock_no_deja_stock_negativo(repository):
    repository.add_product("TEC-01", "Teclado", Decimal("99.00"), 1)

    assert repository.decrease_stock("TEC-01", 2) is False
    repository.session.expire_all()
    assert repository.get_product("TEC-01").stock == 1


def test_guarda_pedido_con_lineas(repository):
    order = repository.save_order(
        Order(
            customer_type="REGULAR",
            subtotal=Decimal("10.00"),
            discount=Decimal("0.00"),
            igv=Decimal("1.80"),
            total=Decimal("11.80"),
            payment_id="pay_x",
            lines=[OrderLine(sku="A", quantity=1, unit_price=Decimal("10.00"))],
        )
    )
    repository.commit()
    repository.session.expire_all()

    saved = repository.get_order(order.id)

    assert saved.total == Decimal("11.80")
    assert [(line.sku, line.quantity) for line in saved.lines] == [("A", 1)]
