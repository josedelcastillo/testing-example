"""Feature: Compra › Descuentos por tipo de cliente y por volumen, vistos en el comprobante.

Scope class: todas las pruebas de la clase comparten UN producto con stock
de sobra. Es seguro porque solo verifican los montos del comprobante, no el
stock. Ahorra una llamada a la API por cada caso parametrizado.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import crear_producto
from tests.e2e.helpers import comprar

pytestmark = [pytest.mark.e2e, pytest.mark.compra]


class TestDescuentosEnComprobante:
    @pytest.fixture(scope="class")
    def producto(self, api):
        return crear_producto(api, price="100.00", stock=100, name="Producto descuentos")

    @pytest.mark.parametrize(
        ("cliente", "cantidad", "descuento", "igv", "total"),
        [
            ("REGULAR", 1, "0.00", "18.00", "118.00"),
            ("FRECUENTE", 1, "5.00", "17.10", "112.10"),
            ("VIP", 1, "10.00", "16.20", "106.20"),
            # subtotal >= 500: +5 % por volumen
            ("REGULAR", 5, "25.00", "85.50", "560.50"),
            # VIP 10 % + volumen 5 % = 15 % (tope)
            ("VIP", 5, "75.00", "76.50", "501.50"),
        ],
    )
    def test_montos_del_comprobante(
        self, page: Page, producto, cliente, cantidad, descuento, igv, total
    ):
        page.goto("/")

        comprar(page, producto["sku"], cantidad, cliente=cliente)

        expect(page.get_by_role("status")).to_have_text("Pedido registrado")
        expect(page.get_by_test_id("discount")).to_have_text(f"S/ {descuento}")
        expect(page.get_by_test_id("igv")).to_have_text(f"S/ {igv}")
        expect(page.get_by_test_id("total")).to_have_text(f"S/ {total}")
