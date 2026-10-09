"""Feature: Catálogo › Consulta del catálogo.

Scope module: el producto se crea UNA vez para todo el archivo. Las pruebas
solo leen, nunca modifican, así que compartirlo no las hace dependientes del
orden. Compáralo con `create_product` (scope function) en compra/.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import crear_producto
from tests.e2e.helpers import fila

pytestmark = [pytest.mark.e2e, pytest.mark.catalogo]


@pytest.fixture(scope="module")
def producto(api):
    return crear_producto(api, price="49.90", stock=7, name="Teclado mecánico")


def test_muestra_nombre_precio_y_stock(page: Page, producto):
    page.goto("/")

    celdas = fila(page, producto["sku"]).locator("td")
    expect(celdas).to_have_text([producto["sku"], "Teclado mecánico", "S/ 49.90", "7"])


def test_producto_disponible_para_pedido(page: Page, producto):
    page.goto("/")

    pedido = page.get_by_role("region", name="Registrar pedido")
    opcion = pedido.get_by_label("Producto").locator(f"option[value='{producto['sku']}']")
    expect(opcion).to_have_text(f"{producto['sku']} - Teclado mecánico")


def test_catalogo_persiste_al_recargar(page: Page, producto):
    page.goto("/")
    page.reload()

    expect(fila(page, producto["sku"])).to_be_visible()
