"""Feature: Catálogo › Alta de productos desde la UI."""

import uuid

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import fila

pytestmark = [pytest.mark.e2e, pytest.mark.catalogo]


def llenar_formulario(page: Page, sku: str, nombre: str, precio: str, stock: int):
    form = page.get_by_role("region", name="Nuevo producto")
    form.get_by_label("SKU").fill(sku)
    form.get_by_label("Nombre").fill(nombre)
    form.get_by_label("Precio (S/)").fill(precio)
    form.get_by_label("Stock").fill(str(stock))
    form.get_by_role("button", name="Crear producto").click()


def test_crear_producto_desde_la_ui(page: Page):
    sku = f"UI-{uuid.uuid4().hex[:8].upper()}"
    page.goto("/")

    llenar_formulario(page, sku, "Monitor 27", "1299.90", 4)

    expect(page.get_by_role("status")).to_have_text(f"Producto {sku} creado")
    expect(fila(page, sku)).to_contain_text("Monitor 27")
    expect(fila(page, sku).locator("td").last).to_have_text("4")


def test_sku_duplicado_muestra_error(page: Page, create_product):
    existente = create_product(name="Original")
    page.goto("/")

    llenar_formulario(page, existente["sku"], "Copia", "10.00", 1)

    expect(page.get_by_role("alert")).to_have_text(f"El SKU {existente['sku']} ya existe")
    expect(fila(page, existente["sku"])).to_have_count(1)
    expect(fila(page, existente["sku"])).to_contain_text("Original")
