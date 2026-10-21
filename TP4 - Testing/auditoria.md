# Parte 2 — Auditoría

## Sección 1: los tests de la IA

### Clasificación

| Test | Clasificación | Por qué |
|---|---|---|
| `test_subtotal` | Tautológico | El valor esperado sale de `CATALOGO["buzo"] * 2`, que es la misma cuenta que hace el código, así que nunca puede dar distinto. |
| `test_total_funciona` | Inútil | Solo pregunta `is not None`, y la función siempre devuelve un diccionario. |
| `test_total_positivo` | Débil | Con `> 0` pasa cualquier total, esté bien calculado o no. |
| `test_cupon_egresados` | Tautológico | Compara contra `100000 * 0.15`, la misma cuenta en `float` que hace el código. |
| `test_envio_caba` | Útil | Compara contra el 2500 que dice la spec. Igual, prueba una sola zona y no prueba el envío gratis. |
| `test_descuento_por_cantidad` | Débil | Prueba con 6 prendas en vez de 5, que es el límite, y por eso no ve que el código usa `> 5`. |
| `test_talle_valido` | Débil | No tiene assert. Solo fallaría si tira una excepción, y no se da cuenta de que el ítem queda modificado. |
| `test_no_explota_con_varios_productos` | Inútil | Tiene un `try/except: pass`, así que pasa aunque `calcular_total` explote. |

### Puntaje de mutación

Corrí `python mutar.py --tests test_checkout_ia.py`:

```
Mutantes generados : 29
Muertos            : 17
Sobrevivientes     : 12
Puntaje de mutación: 58.6%
```

### ¿Por qué cubre casi el 80 % y no encuentra ninguna falla?

Con los tests de la IA me dio 77 % de cobertura de líneas (73 % contando ramas). El problema es que la
cobertura solo mide qué líneas se ejecutaron, no si alguien controló que el resultado esté bien. Los
tests pasan por casi todo el código, pero después no verifican nada en serio: usan `is not None` o `> 0`,
no tienen assert, o calculan el esperado con la misma cuenta que el código. Además todos prueban el
caso normal y ninguno prueba los límites (cantidad 10, 5 prendas, el 30/11, los $60.000) ni datos
inválidos, que es justamente donde están los errores. Por eso el código "anda" pero nunca se compara
con la especificación.

---

## Sección 2: hallazgos

### Ruff

Corrí `ruff check checkout.py` y encontró 5 errores:

```
checkout.py:1:8:   F401 `json` imported but unused
checkout.py:50:9:  E722 Do not use bare `except`
checkout.py:57:70: B008 Do not perform function call `date.today` in argument defaults
checkout.py:63:17: E711 Comparison to `None` should be `cond is not None`
checkout.py:102:53: B008 Do not perform function call `date.today` in argument defaults
```

El E722 y los B008 terminaron siendo fallas de verdad (C8 y C11). Los otros dos son de prolijidad.

### Fallas encontradas

Primero leí los tres archivos comparando con la spec, y después probé en la consola las fallas de las
que no estaba seguro. Las numeré según el archivo: **C** = `checkout.py`, **P** = `pedidos.py`,
**A** = `api.py`.

#### `checkout.py`

**C1 — Los precios y los montos son `float`**
Línea 13-15, 21-22 y 27-30 · numéricos · R7 · leyendo el código · **alta**
El catálogo y los envíos están en `float`/`int`, y la spec dice que todo tiene que ser `Decimal`. Por
ejemplo, 3 buzos dan `74999.70000000001` antes de redondear.

**C2 — Redondea con `round()` y no con redondeo comercial**
Línea 54, 84 y 117 · numéricos · R7 · probándolo · **alta**
El 15 % de una remera tendría que dar 1799,93 (es el ejemplo de la spec) y da `1799.92`.

**C3 — Hay un cupón `DEBUG100` que no está en la spec**
Línea 23 · alucinación · R6 · leyendo el código · **alta**
La spec dice que hay solo dos cupones. Este hace el 100 % de descuento, y con 6 prendas el descuento
llega a 110000 sobre una compra de 100000.

**C4 — `validar_item` modifica el ítem que recibe**
Línea 35 · efectos laterales · R4 · probándolo · **alta**
Le pasé un ítem con talle `"m"` y después de validarlo quedó `"M"` en el carrito original.

**C5 — El talle no ignora los espacios**
Línea 35 · strings · R2 · probándolo · **media**
Hace `upper()` pero no `strip()`, así que `" m "` da `TALLE_INVALIDO`.

**C6 — La cantidad 10 da error**
Línea 40 · lógica y límites · R3 · leyendo el código · **alta**
Usa `< 10` y tendría que ser `<= 10`.

**C7 — No controla que la cantidad sea entera**
Línea 40 · tipos · R3 · probándolo · **media**
`1.5` pasa como válida y `"2"` tira `TypeError` en vez de `CANTIDAD_INVALIDA`.

**C8 — Si el producto no existe, lo saltea**
Línea 48-51 · manejo de errores · R1 · ruff (E722) y probándolo · **alta**
El `except: continue` hace que un carrito con `"gorra"` dé subtotal 0 en vez de `PRODUCTO_INEXISTENTE`.
Además el producto se revisa último, y según la sección 3 va primero.

**C9 — Usa el precio que manda el cliente**
Línea 49 · seguridad · R1 · leyendo el código · **alta**
`item.get("precio", ...)` usa el precio del ítem si viene, y la spec dice que se ignora.

**C10 — No da error con el carrito vacío**
Línea 44-54 · lógica y límites · R4 · probándolo · **media**
`calcular_total([], "CABA")` devuelve un total de 2500 en vez de `CARRITO_VACIO`.

**C11 — La fecha de hoy queda fija**
Línea 57 y 102 · fechas · R6 · ruff (B008) · **media**
`fecha=date.today()` se calcula una sola vez cuando se importa el módulo, no cada vez que se llama.

**C12 — El descuento por cantidad arranca en 6 prendas**
Línea 60 · lógica y límites · R5 · leyendo el código · **alta**
Usa `> 5` y tendría que ser `>= 5`.

**C13 — Suma el cupón con el descuento por cantidad**
Línea 61, 74 y 82 · lógica y límites · R6 · leyendo el código · **alta**
Los dos hacen `descuento +=`, y la spec dice que se aplica solo el mayor.

**C14 — Un cupón vacío da error**
Línea 63-67 · strings · R6 · probándolo · **media**
`""` da `CUPON_INVALIDO`, y tendría que contar como que no hay cupón.

**C15 — El cupón distingue mayúsculas**
Línea 64 · strings · R6 · leyendo el código · **media**
Hace `strip()` pero no `upper()`, así que `"egresados2026"` no existe para el código.

**C16 — `EGRESADOS2026` vence un día antes**
Línea 72 · fechas · R6 · leyendo el código · **alta**
Usa `fecha < vence`, así que el 30/11 ya lo toma como vencido, y la spec dice "inclusive".

**C17 — El descuento puede ser más grande que el subtotal**
Línea 84 · lógica y límites · R6 · probándolo · **media**
No hay ningún tope. Se ve con `DEBUG100` y 6 prendas (ver C3).

**C18 — Usa `join` sobre `dict_keys`**
Línea 93 · alucinación · R8 · probándolo · **alta**
`ENVIOS.keys().join(...)` no existe en Python, así que una zona inválida tira `AttributeError` en vez de
`ZONA_INVALIDA`.

**C19 — El envío gratis se calcula sin el descuento**
Línea 110 · lógica y límites · R8 · leyendo el código · **alta**
A `calcular_envio` le pasa el `subtotal`, y tendría que ser el subtotal menos el descuento.

**C20 — Import sin usar y `!= None`**
Línea 1 y 63 · code smell · — · ruff (F401 y E711) · **baja**

#### `pedidos.py`

**P1 — Si hay un error, el pedido queda guardado igual**
Línea 39-50 · efectos laterales · R10 · probándolo · **alta**
Guarda el pedido y hace `commit` antes de llamar a `calcular_total`. Probé con talle `"XXXL"`: tiró el
error pero quedó 1 pedido en la base.

**P2 — Los ítems nunca se confirman**
Línea 52-71 · manejo de errores · R10 · probándolo · **alta**
Después del `UPDATE` y de los `INSERT` de los ítems no hay `commit`. Desde otra conexión se ven 0 ítems.

**P3 — Los montos se guardan como `REAL`**
Línea 12-15, 23, 55-58, 68 y 88-97 · numéricos · R10 · leyendo el código · **alta**
Los guarda con `float()` y los lee con `Decimal(float)`, así que pueden no ser idénticos a los que
calculó `checkout`.

**P4 — El precio unitario puede venir del cliente**
Línea 64 · seguridad · R10 · leyendo el código · **alta**
Es el mismo `item.get("precio", ...)` de C9.

**P5 — Inyección SQL en `pedidos_de`**
Línea 107 · seguridad · R10 · probándolo · **alta**
Arma la consulta con un f-string. Con el email `x' OR '1'='1` me devolvió los pedidos de todos.

#### `api.py`

**A1 — Cualquier error devuelve 500**
Línea 53-54 y 67-68 · manejo de errores · R11 · probándolo · **alta**
Hay un solo `except Exception` que responde 500. Nunca devuelve 422 ni 400: por ejemplo, un JSON mal
escrito da 500 en vez de `JSON_INVALIDO`.

**A2 — El error no tiene el formato de la spec**
Línea 54 y 68 · manejo de errores · R11 · probándolo · **media**
Responde `{"error": "texto"}` en vez de `{"error": {"code", "message"}}`.

**A3 — Los montos viajan como número**
Línea 18 · tipos · R11 · probándolo · **alta**
`default=float` hace que salga `"subtotal": 11999.5` en vez de `"11999.50"`.

**A4 — La fecha le llega como texto a `checkout`**
Línea 41 · tipos · R11 · probándolo · **alta**
No convierte `"2026-11-01"` a `date`. Con cupón da 500 porque compara un `str` con un `date`, y nunca
devuelve `FECHA_INVALIDA`.

**A5 — Un pedido que no existe devuelve 200**
Línea 64-66 · manejo de errores · R11 · probándolo · **media**
`GET /api/v1/pedidos/999` responde `200` con `null` en vez de `404` `PEDIDO_INEXISTENTE`.

**A6 — La conexión no se cierra si hay un error**
Línea 34-44 y 63-65 · manejo de errores · — · leyendo el código · **baja**
El `con.close()` no está en un `finally`.

### Tabla de fallas (de la más grave a la menos grave)

| # | Archivo | Línea | Categoría | Regla | Severidad |
|---|---|---|---|---|---|
| C1 | `checkout.py` | 13-15, 21-22, 27-30 | numéricos | R7 | alta |
| C2 | `checkout.py` | 54, 84, 117 | numéricos | R7 | alta |
| C3 | `checkout.py` | 23 | alucinación | R6 | alta |
| C4 | `checkout.py` | 35 | efectos laterales | R4 | alta |
| C6 | `checkout.py` | 40 | lógica y límites | R3 | alta |
| C8 | `checkout.py` | 48-51 | manejo de errores | R1 | alta |
| C9 | `checkout.py` | 49 | seguridad | R1 | alta |
| C12 | `checkout.py` | 60 | lógica y límites | R5 | alta |
| C13 | `checkout.py` | 61, 74, 82 | lógica y límites | R6 | alta |
| C16 | `checkout.py` | 72 | fechas | R6 | alta |
| C18 | `checkout.py` | 93 | alucinación | R8 | alta |
| C19 | `checkout.py` | 110 | lógica y límites | R8 | alta |
| P1 | `pedidos.py` | 39-50 | efectos laterales | R10 | alta |
| P2 | `pedidos.py` | 52-71 | manejo de errores | R10 | alta |
| P3 | `pedidos.py` | 12-15, 23, 55-58, 68, 88-97 | numéricos | R10 | alta |
| P4 | `pedidos.py` | 64 | seguridad | R10 | alta |
| P5 | `pedidos.py` | 107 | seguridad | R10 | alta |
| A1 | `api.py` | 53-54, 67-68 | manejo de errores | R11 | alta |
| A3 | `api.py` | 18 | tipos | R11 | alta |
| A4 | `api.py` | 41 | tipos | R11 | alta |
| C5 | `checkout.py` | 35 | strings | R2 | media |
| C7 | `checkout.py` | 40 | tipos | R3 | media |
| C10 | `checkout.py` | 44-54 | lógica y límites | R4 | media |
| C11 | `checkout.py` | 57, 102 | fechas | R6 | media |
| C14 | `checkout.py` | 63-67 | strings | R6 | media |
| C15 | `checkout.py` | 64 | strings | R6 | media |
| C17 | `checkout.py` | 84 | lógica y límites | R6 | media |
| A2 | `api.py` | 54, 68 | manejo de errores | R11 | media |
| A5 | `api.py` | 64-66 | manejo de errores | R11 | media |
| C20 | `checkout.py` | 1, 63 | code smell | — | baja |
| A6 | `api.py` | 34-44, 63-65 | manejo de errores | — | baja |