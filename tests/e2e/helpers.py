"""Acciones de UI reutilizadas por varios features."""

from playwright.sync_api import Page


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
