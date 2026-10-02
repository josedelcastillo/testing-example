"""Pruebas E2E: flujos reales de usuario en el navegador contra la app desplegada.

Buenas prácticas que se muestran:
- Selectores por rol, etiqueta o data-testid (lo que ve el usuario), no por CSS.
- `expect(...)` con espera automática: nunca `sleep`.
- Datos preparados por API (rápido) y acción por UI (lo que se prueba).
- Pocas pruebas, solo flujos críticos de negocio: son lentas y costosas.
"""

import re
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def fila(page: Page, sku: str):
    return page.locator(f"#catalog tr[data-sku='{sku}']")


def comprar(page: Page, sku: str, cantidad: int, cliente: str = "REGULAR"):
    # Acotar a la sección evita ambigüedad: "Producto" también aparece en
    # "Nuevo producto" y Playwright falla en modo estricto (strict mode).
    pedido = page.get_by_role("region", name="Registrar pedido")
    pedido.get_by_label("Producto").select_option(sku)
    pedido.get_by_label("Cantidad").fill(str(cantidad))
    pedido.get_by_label("Tipo de cliente").select_option(cliente)
    pedido.get_by_role("button", name="Comprar").click()


def test_crear_producto_desde_la_ui(page: Page):
    sku = f"UI-{uuid.uuid4().hex[:8].upper()}"
    page.goto("/")
    form = page.get_by_role("region", name="Nuevo producto")

    form.get_by_label("SKU").fill(sku)
    form.get_by_label("Nombre").fill("Monitor 27")
    form.get_by_label("Precio (S/)").fill("1299.90")
    form.get_by_label("Stock").fill("4")
    form.get_by_role("button", name="Crear producto").click()

    expect(page.get_by_role("status")).to_have_text(f"Producto {sku} creado")
    expect(fila(page, sku)).to_contain_text("Monitor 27")
    expect(fila(page, sku).locator("td").last).to_have_text("4")


def test_compra_exitosa_muestra_comprobante_y_descuenta_stock(page: Page, create_product):
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


def test_stock_insuficiente_muestra_error(page: Page, create_product):
    producto = create_product(stock=1)
    page.goto("/")

    comprar(page, producto["sku"], 5)

    expect(page.get_by_role("alert")).to_contain_text("Stock insuficiente")
    expect(page.get_by_role("region", name="Comprobante")).to_be_hidden()


def test_pago_rechazado_no_descuenta_stock(page: Page, create_product):
    # 2 x 6000 + IGV supera el límite de la pasarela (PAYMENT_LIMIT=10000)
    producto = create_product(price="6000.00", stock=3)
    page.goto("/")

    comprar(page, producto["sku"], 2)

    expect(page.get_by_role("alert")).to_contain_text("excede el límite")
    expect(fila(page, producto["sku"]).locator("td").last).to_have_text("3")
