import copy
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
    carrito = [item("remera")]

    resultado = calcular_total(carrito, "CABA", "EGRESADOS2026", HOY_VIGENTE)

    assert resultado == {
        "subtotal": Decimal("11999.50"),
        "descuento": Decimal("1799.93"),
        "envio": Decimal("2500.00"),
        "total": Decimal("12699.57"),
    }
    assert all(type(valor) is Decimal for valor in resultado.values())


def test_diez_prendas_de_un_mismo_item_es_una_cantidad_valida():
    carrito = [item("remera", cantidad=10)]

    subtotal = calcular_subtotal(carrito)

    assert subtotal == Decimal("119995.00")


def test_calcular_total_no_modifica_el_carrito_que_recibe():
    carrito = [item("buzo", talle="m", cantidad=2)]
    copia = copy.deepcopy(carrito)

    calcular_total(carrito, "CABA", None, HOY_VIGENTE)

    assert carrito == copia


def test_un_producto_que_no_esta_en_el_catalogo_da_error():
    carrito = [item("gorra")]

    codigo = codigo_de_error(calcular_subtotal, carrito)

    assert codigo == "PRODUCTO_INEXISTENTE"