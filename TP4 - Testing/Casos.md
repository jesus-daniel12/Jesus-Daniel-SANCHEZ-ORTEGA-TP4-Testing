# Parte 1 — Casos de caja negra

Estos casos los armé leyendo solamente `ESPECIFICACION.md`, sin mirar cómo está hecho el código.
Para cada regla separé los datos en grupos (particiones) que deberían comportarse igual, busqué los
valores límite (el borde y un valor de cada lado) y puse por lo menos un caso para cada grupo.

Aclaraciones:

- `item(...)` es un ítem del carrito. Si no digo nada, es un buzo talle M, cantidad 1.
- Los montos están en pesos y se manejan con `Decimal`, por eso los escribo con dos decimales.
- Cuando el resultado es un error, pongo el `code` que tiene que tener el `CheckoutError`.
- Nivel: de R1 a R9 son tests unitarios, R10 es integración y R11 es end-to-end (E2E).

---

## R1 — Catálogo y precios

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Producto que está en el catálogo | — | Subtotal de 1 buzo | `24999.90` | Unitario |
| Producto que está en el catálogo | — | Subtotal de 1 remera | `11999.50` | Unitario |
| Producto que está en el catálogo | — | Subtotal de 1 campera | `47999.99` | Unitario |
| Varios ítems | — | 1 buzo + 2 remeras | `48998.90` | Unitario |
| El ítem trae un precio propio | — | 1 buzo con `"precio": 1` | `24999.90` (se usa el del catálogo) | Unitario |
| El ítem trae otra clave | — | 1 buzo con `"color": "rojo"` | `24999.90` (la clave se ignora) | Unitario |
| Producto que no existe | — | `"gorra"` | `PRODUCTO_INEXISTENTE` | Unitario |
| Producto con mayúscula | — | `"Buzo"` | `PRODUCTO_INEXISTENTE` (tiene que ir en minúscula) | Unitario |
| Producto vacío | — | `""` | `PRODUCTO_INEXISTENTE` | Unitario |

## R2 — Talles

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Talle válido | El primero y el último de la lista | `"XS"` y `"XXL"` | No da error | Unitario |
| Talle válido | — | `"S"`, `"M"`, `"L"`, `"XL"` | No da error | Unitario |
| Talle en minúscula | — | `"m"` | No da error | Unitario |
| Talle con espacios adelante y atrás | — | `"  M "` | No da error | Unitario |
| Talle que no existe | Uno "más grande" que XXL | `"XXXL"` | `TALLE_INVALIDO` | Unitario |
| Talle vacío | — | `""` | `TALLE_INVALIDO` | Unitario |
| Talle con solo espacios | — | `"   "` | `TALLE_INVALIDO` | Unitario |

## R3 — Cantidad

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Menor a 1 | Justo abajo del mínimo | `0` | `CANTIDAD_INVALIDA` | Unitario |
| Menor a 1 | — | `-1` | `CANTIDAD_INVALIDA` | Unitario |
| Entre 1 y 10 | El mínimo | `1` | No da error | Unitario |
| Entre 1 y 10 | Justo arriba del mínimo | `2` | No da error | Unitario |
| Entre 1 y 10 | Justo abajo del máximo | `9` | No da error | Unitario |
| Entre 1 y 10 | El máximo (incluido) | `10` | No da error | Unitario |
| Mayor a 10 | Justo arriba del máximo | `11` | `CANTIDAD_INVALIDA` | Unitario |
| No es un número entero | — | `1.5` | `CANTIDAD_INVALIDA` | Unitario |
| No es un número entero | — | `2.0` | `CANTIDAD_INVALIDA` | Unitario |

| Es texto | — | `"2"` | `CANTIDAD_INVALIDA` | Unitario |

## R4 — Carrito

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Carrito vacío | 0 ítems | `calcular_total([], "CABA")` | `CARRITO_VACIO` | Unitario |
| Carrito con ítems | 1 ítem | `calcular_total([item()], "CABA")` | No da error, subtotal `24999.90` | Unitario |
| No se modifica el carrito | — | Hago una copia (`deepcopy`) de un carrito con talle `" m "` y `"precio": 1`, llamo a `calcular_total` y comparo | El carrito queda igual que la copia | Unitario |
| No se modifica el ítem | — | Lo mismo pero con `validar_item` | El ítem queda igual que la copia | Unitario |

## R5 — Descuento por cantidad

Para estos casos uso `calcular_descuento` con un subtotal de `100000.00` y sin cupón.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Menos de 5 prendas | Justo abajo del límite | 4 prendas | `0.00` | Unitario |
| 5 prendas o más | El límite (incluido) | 5 prendas | `10000.00` | Unitario |
| 5 prendas o más | Justo arriba del límite | 6 prendas | `10000.00` | Unitario |
| Prendas repartidas en varios ítems | Suman 5 | 2 buzos + 3 remeras, zona CABA | Subtotal `85998.30`, descuento `8599.83`, envío `0.00`, total `77398.47` | Unitario |
| Prendas repartidas en varios ítems | Suman 4 | 2 buzos + 2 remeras, zona CABA | Descuento `0.00` | Unitario |

## R6 — Cupones

Si no digo otra cosa, uso 1 prenda y la fecha `01/10/2026`.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| EGRESADOS2026 vigente | — | Subtotal `100000.00` | `15000.00` | Unitario |
| EGRESADOS2026 vigente | El último día (incluido) | Fecha `30/11/2026` | `15000.00` | Unitario |
| EGRESADOS2026 vigente | Un día antes del último | Fecha `29/11/2026` | `15000.00` | Unitario |
| EGRESADOS2026 vencido | Un día después | Fecha `01/12/2026` | `CUPON_VENCIDO` | Unitario |
| BIENVENIDA sin llegar al mínimo | Un centavo abajo | Subtotal `19999.99` | `CUPON_MINIMO_NO_ALCANZADO` | Unitario |
| BIENVENIDA válido | Justo el mínimo | Subtotal `20000.00` | `3000.00` | Unitario |
| BIENVENIDA válido | Un centavo arriba | Subtotal `20000.01` | `3000.00` | Unitario |
| Cupón en minúscula | — | `"egresados2026"` | `15000.00` | Unitario |
| Cupón con espacios | — | `"  BIENVENIDA "` con subtotal `20000.00` | `3000.00` | Unitario |
| Sin cupón | — | `None` | `0.00` (no es un error) | Unitario |
| Sin cupón | — | `""` | `0.00` (no es un error) | Unitario |
| Sin cupón | — | `"   "` | `0.00` (no es un error) | Unitario |
| Cupón que no existe | — | `"OTRO"` | `CUPON_INVALIDO` | Unitario |
| Cupón que no existe | — | `"DEBUG100"` (la spec dice que hay solo dos) | `CUPON_INVALIDO` | Unitario |
| Cupón + descuento por cantidad | Gana el cupón | 6 prendas, EGRESADOS2026, subtotal `100000.00` | `15000.00` (no se suman) | Unitario |
| Cupón + descuento por cantidad | Gana el 10 % | 6 prendas, BIENVENIDA, subtotal `100000.00` | `10000.00` (no se suman) | Unitario |
| Sin pasar fecha | Hoy es `30/11/2026` | EGRESADOS2026 sin fecha | `15000.00` | Unitario |
| Sin pasar fecha | Hoy es `01/12/2026` | EGRESADOS2026 sin fecha | `CUPON_VENCIDO` (tiene que usar la fecha del día de la llamada) | Unitario |

La regla "el descuento nunca puede superar el subtotal" no la pude probar con un caso real: BIENVENIDA
pide un mínimo de $20.000 y los porcentajes son menores al 100 %, así que con estos dos cupones
nunca pasa.

## R7 — Dinero y redondeo

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Medio centavo | Es el ejemplo de la spec | 15 % de 1 remera (`11999.50`) | `1799.93` (redondea para arriba, no `1799.92`) | Unitario |
| Más de dos decimales | — | 15 % de 1 campera (`47999.99`) | `7200.00` | Unitario |
| Porcentaje que da justo | — | 10 % de 5 remeras (`59997.50`) | `5999.75` | Unitario |
| Precio por cantidad | — | Subtotal de 3 buzos | `74999.70` exacto (con `float` da `74999.70000000001`) | Unitario |
| Tipo de dato | — | `calcular_total` de 1 buzo a CABA | Los 4 importes son `Decimal`, ninguno `float` | Unitario |

## R8 — Envío

Si no digo otra cosa, el subtotal es `10000.00`.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Zona válida | — | `"CABA"` | `2500.00` | Unitario |
| Zona válida | — | `"GBA"` | `4000.00` | Unitario |
| Zona válida | — | `"INTERIOR"` | `6500.00` | Unitario |
| Zona válida | — | `"RETIRO"` | `0.00` | Unitario |
| Zona en minúscula | — | `"caba"` | `2500.00` | Unitario |
| Zona con espacios | — | `"  GBA "` | `4000.00` | Unitario |
| Zona que no existe | — | `"MARTE"` | `ZONA_INVALIDA` | Unitario |
| Zona vacía | — | `""` | `ZONA_INVALIDA` | Unitario |
| Se cobra envío | Un centavo abajo del límite | Subtotal `59999.99`, CABA | `2500.00` | Unitario |
| Envío gratis | Justo el límite | Subtotal `60000.00`, CABA | `0.00` | Unitario |
| Envío gratis | Un centavo arriba | Subtotal `60000.01`, CABA | `0.00` | Unitario |
| El límite se mira con el descuento ya hecho | Sin descuento pasa los $60.000, con descuento no | 2 buzos + 1 remera, CABA, BIENVENIDA | Subtotal `61999.30`, descuento `3000.00`, envío `2500.00`, total `61499.30` | Unitario |
| El mismo carrito sin cupón | Pasa los $60.000 | 2 buzos + 1 remera, CABA | Envío `0.00`, total `61999.30` | Unitario |

## R9 — Total

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Ejemplo de la spec | — | 2 buzos talle M, CABA, sin cupón | Subtotal `49999.80`, descuento `0.00`, envío `2500.00`, total `52499.80` | Unitario |
| Con cupón | — | 1 remera, CABA, EGRESADOS2026, fecha `30/11/2026` | Subtotal `11999.50`, descuento `1799.93`, envío `2500.00`, total `12699.57` | Unitario |

### Orden de los errores (sección 3 de la spec)

Si hay más de un error, tiene que avisar el primero.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Carrito vacío primero | — | Carrito vacío, zona `"MARTE"`, cupón `"OTRO"` | `CARRITO_VACIO` | Unitario |
| Producto antes que talle | — | `"gorra"` con talle `"XXXL"` | `PRODUCTO_INEXISTENTE` | Unitario |
| Talle antes que cantidad | — | Talle `"XXXL"` con cantidad `0` | `TALLE_INVALIDO` | Unitario |
| Ítems en orden | — | Primer ítem con cantidad `0`, segundo `"gorra"` | `CANTIDAD_INVALIDA` | Unitario |
| Cupón antes que zona | — | Ítem bien, cupón `"OTRO"`, zona `"MARTE"` | `CUPON_INVALIDO` | Unitario |

---

## R10 — Guardar pedidos (`pedidos.py`)

Para estos uso una base SQLite de verdad en un archivo temporal. Para ver si algo quedó guardado,
abro otra conexión a la misma base.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Pedido válido | — | ana@mail.com, 1 remera, CABA, EGRESADOS2026, fecha `30/11/2026` | Devuelve un id y el pedido tiene subtotal `11999.50`, descuento `1799.93`, envío `2500.00`, total `12699.57` | Integración |
| Pedido con error | — | Talle `"XXXL"` | Lanza `CheckoutError` con `TALLE_INVALIDO` | Integración |
| Pedido con error | — | El mismo, y después cuento las filas desde otra conexión | 0 pedidos y 0 ítems guardados | Integración |
| Pedido con error | — | El segundo ítem es `"gorra"` | 0 pedidos y 0 ítems guardados | Integración |
| Pedido terminado | — | Guardo un pedido de 2 ítems y lo leo desde otra conexión | Aparece completo, con los 2 ítems | Integración |
| Montos sin perder precisión | — | El pedido válido de arriba | Los montos son `Decimal` y valen exactamente lo mismo (`Decimal("1799.93")`) | Integración |
| Precio unitario | — | 1 buzo con `"precio": 1` | `precio_unitario` = `24999.90` | Integración |
| Email normalizado | — | `"  Ana@Mail.COM "` | Se guarda `"ana@mail.com"` | Integración |
| Zona normalizada | — | `" caba "` | Se guarda `"CABA"` | Integración |
| Talle normalizado | — | `" m "` | Se guarda `"M"` | Integración |
| Cupón normalizado | — | `" egresados2026 "` | Se guarda `"EGRESADOS2026"` | Integración |
| Cupón vacío | — | `""` | Se guarda `None` | Integración |
| Id que no existe | — | `obtener_pedido(con, 999)` | `None` | Integración |
| Buscar por email | — | Guardo con `"ana@mail.com"` y busco `"  ANA@mail.com "` | Lo encuentra | Integración |
| Buscar por email | 3 pedidos | 3 pedidos del mismo email | Del más nuevo al más viejo | Integración |
| Buscar por email | — | Un email que no tiene pedidos | `[]` | Integración |
| Email "trucho" (inyección SQL) | — | `"x' OR '1'='1"`, con pedidos de otras personas en la base | `[]` (no tiene que devolver pedidos de otros) | Integración |

## R11 — API (`api.py`)

Para estos levanto el servidor de verdad y le mando pedidos HTTP.

| Partición | Límites | Caso | Esperado | Nivel |
|---|---|---|---|---|
| Crear pedido | — | POST `/api/v1/pedidos` con 1 remera, EGRESADOS2026, fecha `"2026-11-30"` | `201` y `{"id": ..., "subtotal": "11999.50", "descuento": "1799.93", "envio": "2500.00", "total": "12699.57"}` | E2E |
| Crear pedido sin cupón ni fecha | — | POST sin `cupon` ni `fecha` | `201` | E2E |
| Los montos van como texto | — | La respuesta del POST | Los montos son strings (`"11999.50"`), no números | E2E |
| Consultar un pedido | — | Creo uno y hago GET `/api/v1/pedidos/{id}` | `200` y el pedido completo, con los montos como texto | E2E |
| Error de negocio | — | Talle `"XXXL"` | `422` con `{"error": {"code": "TALLE_INVALIDO", "message": ...}}` | E2E |
| Error de negocio | — | Carrito vacío | `422` con `CARRITO_VACIO` | E2E |
| Error de negocio | — | EGRESADOS2026 con fecha `"2026-12-01"` | `422` con `CUPON_VENCIDO` | E2E |
| JSON mal escrito | — | Cuerpo: `{no es json` | `400` con `JSON_INVALIDO` | E2E |
| Falta un dato | — | Sin `email` | `400` con `DATOS_INCOMPLETOS` | E2E |
| Dato con otro tipo | — | `"carrito": "buzo"` | `400` con `DATOS_INCOMPLETOS` | E2E |
| Fecha con otro formato | — | `"fecha": "30/11/2026"` | `400` con `FECHA_INVALIDA` | E2E |
| Pedido que no existe | — | GET `/api/v1/pedidos/999` | `404` con `PEDIDO_INEXISTENTE` | E2E |
| Ruta que no existe | — | GET `/api/v1/otra` | `404` con `RUTA_INEXISTENTE` | E2E |
| Nunca 500 | — | Todos los errores de arriba | Ninguno devuelve `500` y todos tienen el formato `{"error": {"code", "message"}}` | E2E |