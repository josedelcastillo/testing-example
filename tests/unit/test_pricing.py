"""Pruebas unitarias de reglas de negocio puras.

Patrones que se muestran:
- Arrange / Act / Assert
- Parametrización (una prueba, muchos casos)
- Pruebas de valores límite (boundary testing)
- Verificación de excepciones
"""

from decimal import Decimal

import pytest

from app.pricing import calculate_subtotal, calculate_totals, discount_rate, round_money

D = Decimal


class TestCalculateSubtotal:
    def test_suma_precio_por_cantidad_de_cada_linea(self):
        # Arrange
        lines = [(D("10.00"), 2), (D("5.50"), 3)]
        # Act
        subtotal = calculate_subtotal(lines)
        # Assert
        assert subtotal == D("36.50")

    def test_pedido_vacio_lanza_error(self):
        with pytest.raises(ValueError, match="al menos una línea"):
            calculate_subtotal([])

    @pytest.mark.parametrize("quantity", [0, -1])
    def test_cantidad_no_positiva_lanza_error(self, quantity):
        with pytest.raises(ValueError, match="cantidad"):
            calculate_subtotal([(D("10.00"), quantity)])

    def test_precio_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="precio"):
            calculate_subtotal([(D("-1.00"), 1)])


class TestDiscountRate:
    @pytest.mark.parametrize(
        ("customer_type", "subtotal", "expected"),
        [
            ("REGULAR", D("100.00"), D("0.00")),
            ("FRECUENTE", D("100.00"), D("0.05")),
            ("VIP", D("100.00"), D("0.10")),
            # Valores límite del descuento por volumen (umbral = 500)
            ("REGULAR", D("499.99"), D("0.00")),
            ("REGULAR", D("500.00"), D("0.05")),
            ("FRECUENTE", D("500.00"), D("0.10")),
            # El descuento acumulado nunca supera el tope de 15 %
            ("VIP", D("9999.00"), D("0.15")),
        ],
    )
    def test_descuento_segun_cliente_y_volumen(self, customer_type, subtotal, expected):
        assert discount_rate(customer_type, subtotal) == expected

    def test_cliente_desconocido_lanza_error(self):
        with pytest.raises(ValueError, match="desconocido"):
            discount_rate("PLATINUM", D("100.00"))


class TestCalculateTotals:
    def test_cliente_regular_sin_descuento_paga_igv_18(self):
        totals = calculate_totals([(D("100.00"), 1)], "REGULAR")

        assert totals.subtotal == D("100.00")
        assert totals.discount == D("0.00")
        assert totals.igv == D("18.00")
        assert totals.total == D("118.00")

    def test_igv_se_calcula_sobre_monto_con_descuento(self):
        totals = calculate_totals([(D("250.00"), 2)], "VIP")  # 500 → 15 % dcto

        assert totals.discount == D("75.00")
        assert totals.igv == D("76.50")  # 18 % de 425
        assert totals.total == D("501.50")

    def test_total_es_coherente_con_sus_componentes(self):
        totals = calculate_totals([(D("19.99"), 7), (D("3.33"), 3)], "FRECUENTE")

        assert totals.total == totals.subtotal - totals.discount + totals.igv


@pytest.mark.parametrize(
    ("value", "expected"),
    [(D("1.005"), D("1.01")), (D("1.004"), D("1.00")), (D("2.5"), D("2.50"))],
)
def test_round_money_redondea_half_up_a_dos_decimales(value, expected):
    assert round_money(value) == expected
