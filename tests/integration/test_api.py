"""Integración de punta a punta dentro del servicio:
HTTP (FastAPI) → servicio → repositorio → PostgreSQL.

Solo la pasarela de pagos es simulada (FakePaymentGateway), porque es un
sistema externo que no controlamos.
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def producto(client):
    response = client.post(
        "/products", json={"sku": "CEL-01", "name": "Celular", "price": "800.00", "stock": 5}
    )
    assert response.status_code == 201
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_crear_y_consultar_producto(client, producto):
    response = client.get("/products/CEL-01")

    assert response.status_code == 200
    assert response.json()["name"] == "Celular"


def test_producto_inexistente_devuelve_404(client):
    assert client.get("/products/NADA").status_code == 404


def test_sku_duplicado_devuelve_409(client, producto):
    response = client.post(
        "/products", json={"sku": "CEL-01", "name": "Otro", "price": "1.00", "stock": 1}
    )

    assert response.status_code == 409


def test_validacion_de_entrada_devuelve_422(client):
    response = client.post("/products", json={"sku": "X", "name": "X", "price": "-5", "stock": 1})

    assert response.status_code == 422


def test_pedido_exitoso_descuenta_stock_y_cobra(client, producto, gateway):
    response = client.post(
        "/orders", json={"customer_type": "REGULAR", "items": [{"sku": "CEL-01", "quantity": 1}]}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["discount"] == "40.00"  # 5 % por volumen (subtotal >= 500)
    assert body["total"] == "896.80"  # (800 - 40) + 18 % IGV
    assert body["payment_id"].startswith("pay_")
    assert client.get("/products/CEL-01").json()["stock"] == 4
    assert len(gateway.charges) == 1


def test_pedido_sin_stock_devuelve_409_y_no_cobra(client, producto, gateway):
    response = client.post("/orders", json={"items": [{"sku": "CEL-01", "quantity": 99}]})

    assert response.status_code == 409
    assert gateway.charges == []


def test_pago_rechazado_devuelve_402_y_no_descuenta_stock(client, producto):
    # 2 x 800 + IGV = 1888 > límite de 1000 del gateway de prueba
    response = client.post("/orders", json={"items": [{"sku": "CEL-01", "quantity": 2}]})

    assert response.status_code == 402
    assert client.get("/products/CEL-01").json()["stock"] == 5


def test_tipo_de_cliente_invalido_devuelve_422(client, producto):
    response = client.post(
        "/orders", json={"customer_type": "XYZ", "items": [{"sku": "CEL-01", "quantity": 1}]}
    )

    assert response.status_code == 422


def test_listar_productos_ordenados_por_sku(client, producto):
    client.post(
        "/products", json={"sku": "AUD-01", "name": "Audífonos", "price": "99.00", "stock": 2}
    )

    skus = [p["sku"] for p in client.get("/products").json()]

    assert skus == ["AUD-01", "CEL-01"]
