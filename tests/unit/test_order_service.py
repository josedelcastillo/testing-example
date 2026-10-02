"""Pruebas unitarias del caso de uso con dobles de prueba (mocks/stubs).

El repositorio y la pasarela de pagos se reemplazan por `Mock`, así la
prueba no toca la base de datos ni la red: corre en milisegundos y solo
puede fallar por un error en `OrderService`.
"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.payments import PaymentDeclinedError
from app.services import InsufficientStockError, OrderService, ProductNotFoundError


def make_product(sku="SKU-1", price="100.00", stock=10):
    return SimpleNamespace(sku=sku, price=Decimal(price), stock=stock)


@pytest.fixture
def repository():
    repo = Mock()
    repo.get_product.side_effect = lambda sku: {"SKU-1": make_product()}.get(sku)
    repo.decrease_stock.return_value = True
    repo.save_order.side_effect = lambda order: order
    return repo


@pytest.fixture
def gateway():
    gw = Mock()
    gw.charge.return_value = "pay_123"
    return gw


@pytest.fixture
def service(repository, gateway):
    return OrderService(repository, gateway)


def test_pedido_valido_cobra_descuenta_stock_y_confirma(service, repository, gateway):
    order = service.place_order("REGULAR", [("SKU-1", 2)])

    assert order.total == Decimal("236.00")
    assert order.payment_id == "pay_123"
    gateway.charge.assert_called_once()
    assert gateway.charge.call_args.args[0] == Decimal("236.00")
    repository.decrease_stock.assert_called_once_with("SKU-1", 2)
    repository.commit.assert_called_once()
    repository.rollback.assert_not_called()


def test_producto_inexistente_no_cobra(service, gateway):
    with pytest.raises(ProductNotFoundError):
        service.place_order("REGULAR", [("NO-EXISTE", 1)])

    gateway.charge.assert_not_called()


def test_stock_insuficiente_no_cobra(service, gateway):
    with pytest.raises(InsufficientStockError):
        service.place_order("REGULAR", [("SKU-1", 11)])

    gateway.charge.assert_not_called()


def test_stock_consumido_por_otro_pedido_hace_rollback(service, repository, gateway):
    # Simula una condición de carrera: al leer había stock, al descontar ya no.
    repository.decrease_stock.return_value = False

    with pytest.raises(InsufficientStockError):
        service.place_order("REGULAR", [("SKU-1", 1)])

    gateway.charge.assert_not_called()
    repository.rollback.assert_called_once()
    repository.commit.assert_not_called()


def test_pago_rechazado_hace_rollback_y_no_guarda(service, repository, gateway):
    gateway.charge.side_effect = PaymentDeclinedError("fondos insuficientes")

    with pytest.raises(PaymentDeclinedError):
        service.place_order("VIP", [("SKU-1", 1)])

    repository.save_order.assert_not_called()
    repository.rollback.assert_called_once()
    repository.commit.assert_not_called()
