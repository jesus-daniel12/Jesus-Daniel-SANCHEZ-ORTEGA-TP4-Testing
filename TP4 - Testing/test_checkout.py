import copy
from datetime import date
from decimal import Decimal

import pytest

import checkout
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


def test_si_el_item_trae_su_propio_precio_se_usa_el_del_catalogo():
    carrito = [item("buzo", precio=1)]

    subtotal = calcular_subtotal(carrito)

    assert subtotal == Decimal("24999.90")


def test_el_talle_con_espacios_alrededor_es_valido():
    carrito = [item("buzo", talle="  m ")]

    subtotal = calcular_subtotal(carrito)

    assert subtotal == Decimal("24999.90")


@pytest.mark.parametrize("cantidad", [1.5, "2"])
def test_una_cantidad_que_no_es_un_numero_entero_es_invalida(cantidad):
    un_item = item(cantidad=cantidad)

    codigo = codigo_de_error(validar_item, un_item)

    assert codigo == "CANTIDAD_INVALIDA"


def test_un_carrito_vacio_da_error():
    carrito = []

    codigo = codigo_de_error(calcular_total, carrito, "CABA")

    assert codigo == "CARRITO_VACIO"


def test_con_cinco_prendas_se_aplica_el_diez_por_ciento():
    subtotal = Decimal("100000.00")

    descuento = calcular_descuento(subtotal, 5, None, HOY_VIGENTE)

    assert descuento == Decimal("10000.00")


def test_egresados2026_vale_el_30_de_noviembre_inclusive():
    subtotal = Decimal("100000.00")

    descuento = calcular_descuento(subtotal, 1, "EGRESADOS2026", date(2026, 11, 30))

    assert descuento == Decimal("15000.00")


def test_sin_fecha_se_usa_la_fecha_del_dia_de_la_llamada(monkeypatch):
    class FechaFalsa(date):
        @classmethod
        def today(cls):
            return cls(2026, 12, 1)

    monkeypatch.setattr(checkout, "date", FechaFalsa)

    codigo = codigo_de_error(calcular_descuento, Decimal("100000.00"), 1, "EGRESADOS2026")

    assert codigo == "CUPON_VENCIDO"


def test_el_cupon_en_minuscula_y_con_espacios_es_valido():
    subtotal = Decimal("100000.00")

    descuento = calcular_descuento(subtotal, 1, "  egresados2026 ", HOY_VIGENTE)

    assert descuento == Decimal("15000.00")


@pytest.mark.parametrize("cupon", ["", "   "])
def test_un_cupon_vacio_es_como_no_usar_cupon(cupon):
    subtotal = Decimal("100000.00")

    descuento = calcular_descuento(subtotal, 1, cupon, HOY_VIGENTE)

    assert descuento == Decimal("0.00")


def test_debug100_no_es_un_cupon_valido():
    subtotal = Decimal("100000.00")

    codigo = codigo_de_error(calcular_descuento, subtotal, 1, "DEBUG100", HOY_VIGENTE)

    assert codigo == "CUPON_INVALIDO"


def test_el_cupon_no_se_suma_al_descuento_por_cantidad_se_aplica_el_mayor():
    subtotal = Decimal("100000.00")

    descuento = calcular_descuento(subtotal, 6, "EGRESADOS2026", HOY_VIGENTE)

    assert descuento == Decimal("15000.00")


def test_una_zona_que_no_existe_da_error():
    subtotal = Decimal("10000.00")

    codigo = codigo_de_error(calcular_envio, subtotal, "MARTE")

    assert codigo == "ZONA_INVALIDA"


def test_el_envio_gratis_se_calcula_con_el_subtotal_ya_descontado():
    carrito = [item("buzo", cantidad=2), item("remera")]

    resultado = calcular_total(carrito, "CABA", "BIENVENIDA", HOY_VIGENTE)

    assert resultado == {
        "subtotal": Decimal("61999.30"),
        "descuento": Decimal("3000.00"),
        "envio": Decimal("2500.00"),
        "total": Decimal("61499.30"),
    }