# Laboratorio: automatización de pruebas

Duración sugerida: 2 h 45 min. Trabajar en una rama propia y abrir un Pull
Request para ver el pipeline en acción.

## Parte 1 — Leer y ejecutar (15 min)

1. Ejecuta `make test-unit` y `make test-integration`. Anota cuánto demora
   cada uno.
2. Abre `htmlcov/index.html` tras correr
   `pytest tests/unit --cov=app --cov-report=html`. ¿Qué módulos no cubren
   las unitarias? ¿Por qué eso es correcto y no un problema?

## Parte 2 — ¿Qué nivel detecta el bug? (30 min)

Introduce **un** bug a la vez, ejecuta ambos niveles y completa la tabla.
Revierte con `git checkout -- app/` antes del siguiente.

Para la columna E2E hay que redesplegar: `make test-e2e`.

| # | Bug a introducir | ¿Unit? | ¿Integración? | ¿E2E? |
|---|---|---|---|---|
| 1 | En `pricing.py` cambia `IGV_RATE` a `0.19` | | | |
| 2 | En `pricing.py` cambia `>=` por `>` en el umbral de volumen | | | |
| 3 | En `repository.py` quita `Product.stock >= quantity` del `where` | | | |
| 4 | En `models.py` cambia `Numeric(10, 2)` del precio por `Float` | | | |
| 5 | En `services.py` mueve `charge(...)` antes del bucle `decrease_stock` | | | |
| 6 | En `main.py` cambia `status_code=201` por `200` en `/orders` | | | |
| 7 | En `index.html` cambia `data-testid="total"` por `data-testid="importe"` | | | |
| 8 | En `index.html` borra la línea `await loadCatalog();` del submit del pedido | | | |
| 9 | En el `Dockerfile` cambia `COPY app ./app` por `COPY app/*.py ./app/` | | | |

Preguntas:
- ¿Qué bugs solo los detecta la integración? ¿Por qué el mock no los ve?
- El bug 5 cobra antes de validar stock. ¿Qué prueba lo detecta y qué
  consecuencia de negocio tendría en producción?
- Los bugs 7, 8 y 9 solo los detecta la E2E. ¿Qué tienen en común? ¿Justifica
  eso el costo (tiempo, infraestructura) de mantener E2E?
- El bug 7 no rompe nada para el usuario, pero sí la prueba. ¿Es un falso
  positivo? ¿Qué dice esto sobre acoplar pruebas a detalles de la UI?

## Parte 3 — Escribir pruebas (45 min)

Nueva regla de negocio: **los clientes `VIP` tienen envío gratis; el resto
paga S/ 15.00 si el subtotal (con descuento) es menor a S/ 200.00.** El
envío está afecto a IGV.

1. Escribe primero las pruebas unitarias en `test_pricing.py` (TDD):
   casos VIP, regular con 199.99, regular con 200.00. Deben fallar (rojo).
2. Implementa en `pricing.py` hasta que pasen (verde). Refactoriza.
3. Agrega la columna `shipping` a `Order` y una prueba de integración en
   `test_api.py` que verifique el total devuelto por `POST /orders`.
4. Asegura que `make test` sigue en verde y que la cobertura no baja.

## Parte 4 — E2E (45 min)

1. Corre `pytest tests/e2e --headed --slowmo 500` y observa el navegador.
2. Escribe una E2E nueva: crear un producto desde la UI con un SKU que ya
   existe debe mostrar el mensaje de error "ya existe".
3. Rompe a propósito un selector, corre la prueba y abre el trace con
   `playwright show-trace`. ¿Qué información te da que no da el log?
4. Corre `make test-e2e` dos veces seguidas sin `make down`. ¿Por qué no
   fallan aunque la BD tenga datos de la ejecución anterior? ¿Qué pasaría
   si las pruebas usaran un SKU fijo como `"CEL-01"`?

## Parte 5 — Pipeline (30 min)

1. Haz push y abre un PR. Observa las etapas en *Actions* (o Azure DevOps).
2. Haz que la prueba unitaria falle a propósito y vuelve a hacer push.
   ¿Se ejecutó la etapa de integración? ¿Por qué ese diseño ahorra tiempo
   y dinero?
3. Sube `--cov-fail-under` a 100 en integración. ¿Qué pasa? Discute si
   100 % de cobertura es una meta razonable.
4. (Opcional) Configura *branch protection* para que `main` exija que el
   jobs `integration-tests` y `e2e-tests` estén en verde antes del merge.
