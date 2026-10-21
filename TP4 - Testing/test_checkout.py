from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CheckoutError,
    calcular_descuento,
    calcular_envio,
    calcular_subtotal,
    calcular_total,
    validar_item,
)

HOY_VIGENTE = date(2026, 10, 1)


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def codigo_de_error(funcion, *args):
    with pytest.raises(CheckoutError) as error:
        funcion(*args)
    return error.value.code


def test_cantidad_cero_es_invalida():
    assert codigo_de_error(validar_item, item(cantidad=0)) == "CANTIDAD_INVALIDA"


def test_total_con_cupon_usa_decimal_y_redondea_el_medio_centavo_para_arriba():
    # Arrange
    carrito = [item("remera")]

    # Act
    resultado = calcular_total(carrito, "CABA", "EGRESADOS2026", HOY_VIGENTE)

    # Assert
    assert resultado == {
        "subtotal": Decimal("11999.50"),
        "descuento": Decimal("1799.93"),
        "envio": Decimal("2500.00"),
        "total": Decimal("12699.57"),
    }
    assert all(type(valor) is Decimal for valor in resultado.values())


def test_diez_prendas_de_un_mismo_item_es_una_cantidad_valida():
    # Arrange
    carrito = [item("remera", cantidad=10)]

    # Act
    subtotal = calcular_subtotal(carrito)

    # Assert
    assert subtotal == Decimal("119995.00")