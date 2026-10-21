from datetime import date
from decimal import Decimal

import pytest

import pedidos
from checkout import CheckoutError

HOY_VIGENTE = date(2026, 10, 1)


@pytest.fixture
def ruta(tmp_path):
    return str(tmp_path / "tienda.db")


@pytest.fixture
def con(ruta):
    conexion = pedidos.conectar(ruta)
    pedidos.crear_esquema(conexion)
    yield conexion
    conexion.close()


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def contar(ruta, tabla):
    assert tabla in ("pedidos", "items")
    otra = pedidos.conectar(ruta)
    try:
        return otra.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    finally:
        otra.close()


def test_un_id_inexistente_devuelve_none(con):
    assert pedidos.obtener_pedido(con, 999) is None


def test_si_checkout_tira_error_no_queda_nada_guardado(con, ruta):
    carrito = [item(talle="XXXL")]

    with pytest.raises(CheckoutError) as error:
        pedidos.guardar_pedido(con, "ana@mail.com", carrito, "CABA", None, HOY_VIGENTE)

    assert error.value.code == "TALLE_INVALIDO"
    assert contar(ruta, "pedidos") == 0
    assert contar(ruta, "items") == 0


def test_otra_conexion_ve_el_pedido_completo_con_sus_items(con, ruta):
    carrito = [item("buzo"), item("remera", cantidad=2)]

    pedidos.guardar_pedido(con, "ana@mail.com", carrito, "CABA", None, HOY_VIGENTE)

    assert contar(ruta, "pedidos") == 1
    assert contar(ruta, "items") == 2


def test_los_montos_guardados_son_decimal_y_no_pierden_precision(con):
    carrito = [item("remera")]

    pedido_id = pedidos.guardar_pedido(con, "ana@mail.com", carrito, "CABA", "EGRESADOS2026", HOY_VIGENTE)
    pedido = pedidos.obtener_pedido(con, pedido_id)

    assert pedido["subtotal"] == Decimal("11999.50")
    assert pedido["descuento"] == Decimal("1799.93")
    assert pedido["envio"] == Decimal("2500.00")
    assert pedido["total"] == Decimal("12699.57")
    assert pedido["items"][0]["precio_unitario"] == Decimal("11999.50")


def test_pedidos_de_no_se_puede_alterar_con_inyeccion_sql(con):
    pedidos.guardar_pedido(con, "beto@mail.com", [item()], "CABA", None, HOY_VIGENTE)

    resultado = pedidos.pedidos_de(con, "x' OR '1'='1")

    assert resultado == []