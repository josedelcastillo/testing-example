"""Fixtures E2E: la app corre desplegada (docker compose) y se prueba como
caja negra, a través del navegador. No se importa nada de `app`.

A diferencia de integración, la BD NO se revierte entre pruebas: es un
entorno compartido, igual que staging. Por eso cada prueba crea sus propios
datos con identificadores únicos.
"""

import os
import uuid

import pytest
from playwright.sync_api import Playwright

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("E2E_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # Permite usar un Chromium ya instalado (p. ej. en un runner sin internet).
    path = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    return {**browser_type_launch_args, **({"executable_path": path} if path else {})}


@pytest.fixture(scope="session")
def api(playwright: Playwright, base_url):
    """Cliente HTTP para preparar datos (Arrange) sin pasar por la UI."""
    context = playwright.request.new_context(base_url=base_url)
    try:
        ok = context.get("/health").ok
    except Exception:
        ok = False
    if not ok:
        pytest.fail(
            f"La app no responde en {base_url}.\n"
            "Despliégala con: docker compose up -d --build --wait",
            pytrace=False,
        )
    yield context
    context.dispose()


def crear_producto(api, price="100.00", stock=10, name="Producto E2E"):
    """Crea un producto por API. Función normal (no fixture) para poder usarla
    desde fixtures de cualquier scope: function, class, module o session."""
    sku = f"E2E-{uuid.uuid4().hex[:8].upper()}"
    response = api.post(
        "/products", data={"sku": sku, "name": name, "price": price, "stock": stock}
    )
    assert response.status == 201, response.text()
    return response.json()


@pytest.fixture
def create_product(api):
    """Scope function (el default): datos nuevos por prueba. Úsalo cuando la
    prueba modifica el estado (p. ej. descuenta stock) y luego lo verifica."""

    def _create(**kwargs):
        return crear_producto(api, **kwargs)

    return _create
