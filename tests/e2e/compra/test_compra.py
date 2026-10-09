"""Feature: Compra. Flujo de pedido completo en el navegador contra la app desplegada.

Buenas prácticas que se muestran:
- Selectores por rol, etiqueta o data-testid (lo que ve el usuario), no por CSS.
- `expect(...)` con espera automática: nunca `sleep`.
- Datos preparados por API (rápido) y acción por UI (lo que se prueba).
- Pocas pruebas, solo flujos críticos de negocio: son lentas y costosas.
- Clases para agrupar escenarios del mismo feature (camino feliz / errores).
- Scope function (`create_product`): cada prueba verifica el stock, así que
  necesita su propio producto; compartirlo haría que dependan del orden.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import comprar, fila

pytestmark = [pytest.mark.e2e, pytest.mark.compra]


class TestCompraExitosa:
    def test_muestra_comprobante_y_descuenta_stock(self, page: Page, create_product):
        producto = create_product(price="300.00", stock=5)
        page.goto("/")

        comprar(page, producto["sku"], 2, cliente="VIP")

        expect(page.get_by_role("status")).to_have_text("Pedido registrado")
        # 600 → VIP 10 % + volumen 5 % = 90 de descuento; IGV 18 % de 510 = 91.80
        expect(page.get_by_test_id("subtotal")).to_have_text("S/ 600.00")
        expect(page.get_by_test_id("discount")).to_have_text("S/ 90.00")
        expect(page.get_by_test_id("igv")).to_have_text("S/ 91.80")
        expect(page.get_by_test_id("total")).to_have_text("S/ 601.80")
        expect(page.get_by_test_id("order-id")).to_have_text(re.compile(r"#\d+"))
        expect(fila(page, producto["sku"]).locator("td").last).to_have_text("3")


class TestCompraRechazada:
    def test_stock_insuficiente_muestra_error(self, page: Page, create_product):
        producto = create_product(stock=1)
        page.goto("/")

        comprar(page, producto["sku"], 5)

        expect(page.get_by_role("alert")).to_contain_text("Stock insuficiente")
        expect(page.get_by_role("region", name="Comprobante")).to_be_hidden()

    def test_pago_rechazado_no_descuenta_stock(self, page: Page, create_product):
        # 2 x 6000 + IGV supera el límite de la pasarela (PAYMENT_LIMIT=10000)
        producto = create_product(price="6000.00", stock=3)
        page.goto("/")

        comprar(page, producto["sku"], 2)

        expect(page.get_by_role("alert")).to_contain_text("excede el límite")
        expect(fila(page, producto["sku"]).locator("td").last).to_have_text("3")
