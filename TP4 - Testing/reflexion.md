# Parte 5 — Reflexión

## 1. ¿Cuántos tests unitarios, de integración y E2E tenés? ¿Por qué esa proporción?

Tengo 27 tests unitarios en `test_checkout.py` (37 casos contando los `parametrize`), 5 de integración
y 7 end-to-end, contando el ejemplo que traía cada plantilla. La mayoría son unitarios porque
`checkout.py` es donde están casi todas las reglas (de R1 a R9) y cada una tiene límites que hay que
probar de los dos lados, como la cantidad 10 y 11 o el envío con $59.999,99 y $60.000. Además los
unitarios son rápidos: los 37 casos corren en menos de un segundo y `mutar.py` los puede correr 35
veces sin problema. Los de integración y E2E son menos porque cada uno tiene que crear una base de
datos o levantar un servidor, y porque prueban cómo se conectan las partes, no cada cuenta. Por eso
en E2E hice un test por endpoint y uno por cada error que elegí (422, 400 y 404), y no repetí ahí los
casos de cupones que ya estaban probados en los unitarios. Me quedó la forma de la pirámide que vimos
en clase: muchos tests abajo y pocos arriba.

## 2. ¿Qué falla de `pedidos.py` no podía encontrarse con un test unitario de `checkout.py`? ¿Por qué?

La falla de que, si `calcular_total` tira un error, el pedido igual queda guardado en la base. Pasa
porque `guardar_pedido` hace el `INSERT` y el `commit` antes de calcular el total, entonces cuando
`checkout` tira `TALLE_INVALIDO` el pedido ya está confirmado. Con un test unitario de `checkout.py`
esto no se puede ver, porque `checkout` hace bien su parte: tira el error que tiene que tirar. El
problema está en el orden en que `pedidos.py` usa ese resultado y en cómo maneja la transacción, y
para verlo hace falta una base de datos de verdad. En mi test `test_si_checkout_tira_error_no_queda_nada_guardado`
cuento las filas desde otra conexión después del error, y en vez de 0 pedidos aparece 1. Ningún test
de `checkout.py` podía encontrar eso porque `checkout` no sabe nada de la base.

## 3. ¿Qué falla de `api.py` estaba en el paso de información entre dos partes del sistema? ¿Qué parte tendría que haberla resuelto?

La de la fecha. El frontend la manda como texto (`"2026-11-30"`) y `api.py` se la pasa así, como
texto, a `pedidos.py`, que se la pasa a `checkout.py`, que espera un `date`. Cuando el pedido tiene el
cupón `EGRESADOS2026`, `checkout` compara un `str` con un `date`, explota y la API devuelve 500. Y
cuando no hay cupón es peor, porque nadie revisa la fecha: mi test con `"30/11/2026"` devuelve 201 en
vez de `FECHA_INVALIDA`. La parte que lo tendría que haber resuelto es `api.py`, porque es la que
recibe el JSON y la spec dice que ahí se valida el formato `AAAA-MM-DD` y se responde 400. `checkout`
no tiene la culpa: su contrato dice que `fecha` es un `date` o `None`, no un texto.

## 4. ¿Cuál de las fallas que encontraste habría sido la más cara de descubrir en producción? ¿Por qué?

Para mí, la de que el precio sale del ítem y no del catálogo (C9 en `checkout.py` y P4 en
`pedidos.py`). Cualquiera que sepa un poco de programación podría mandar `"precio": 1` en el pedido y
comprarse un buzo por un peso, que fue justo lo que vi en mi test de R1: el subtotal dio `1.00` en
vez de `24999.90`. En producción eso no tira ningún error ni aparece en ningún log, porque para el
sistema el pedido está bien. Te enterás cuando la comisión hace las cuentas y le falta plata, y para
ese momento puede haber muchos pedidos así guardados con `precio_unitario` trucho. La inyección SQL de
`pedidos_de` también es muy grave porque muestra los pedidos de otras personas, pero la del precio
pega directo en la plata y es más difícil de notar.

## 5. ¿Qué mide la cobertura, qué mide la mutación y qué mide la inyección de fallas? ¿En qué se diferencian?

La cobertura mide qué líneas y qué ramas del código se ejecutaron cuando corrieron los tests, pero no
si los tests revisaron que el resultado esté bien. La mutación mide si los tests se dan cuenta cuando
el código cambia: `mutar.py` cambia cosas chiquitas, como un `<` por un `<=` o un 10 por un 11, y se
fija si algún test falla. La inyección de fallas es parecida, pero con errores más grandes y
realistas, como sacar un `commit` o armar una consulta concatenando el texto, y sirve para ver si los
tests de integración y E2E detectan el problema. La diferencia se vio clara con los tests de la IA:
cubrían el 77 % de las líneas pero tenían 58,6 % de mutación, o sea que pasaban por el código sin
controlar nada. Mi suite terminó con 99 % de cobertura de ramas y 100 % de mutación, y los cambios
que con la IA sobrevivían, como tocar el límite de 5 prendas o el de $60.000, ahora los detecta algún
test. En resumen, la
cobertura dice por dónde pasaste, y la mutación y la inyección de fallas dicen si los tests de verdad
encuentran errores.

## 6. Si una IA escribiera tus tests de integración y E2E, ¿qué le faltaría probar? ¿Cómo lo comprobarías?

Creo que haría lo mismo que con `test_checkout_ia.py`: tests del camino feliz con asserts flojos,
como fijarse que el status sea 201 sin mirar si los montos vienen como texto. Seguramente leería el
pedido con la misma conexión que lo guardó, y así nunca vería que falta el `commit`, porque esa
conexión sí ve los ítems. También le faltarían los casos de error y de seguridad, como el JSON roto,
la fecha con otro formato o el email con `' OR '1'='1`, que fueron los que me encontraron fallas.
Para comprobarlo, correría sus tests contra el `pedidos.py` y el `api.py` originales: si pasan todos,
no están detectando las fallas que sé que existen. Y al revés, me fijaría que cada test pase contra un
código que cumpla la spec, porque un test que falla siempre tampoco sirve.