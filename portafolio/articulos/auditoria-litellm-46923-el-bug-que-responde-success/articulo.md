---
title: El bug que responde SUCCESS: auditoría reproducible de litellm#46923
lede: Seis brazos, un servidor HTTP que registra el payload real y un control negativo. Cómo se audita un defecto de framework sin mocks, por qué el parche candidato empeora el camino sincrónico, y por qué el estado peligroso es el que se parece al éxito.
date: 2026-11-06
tags: devops, git, productivity, opensource
cola_slug: red_auditoria-litellm-46923-el-bug-que-responde-success
fuente: DEPARTAMENTOS/comercial/ARTICULO_DEVTO_AUDITORIA_LITELLM_46923_PUBLICO.md
---

Un programa que falla es fácil de auditar: devuelve un error, lo lees, lo arreglas.

El problema caro es el contrario. El programa **termina bien**, escribe `SUCCESS` en el log, y por el camino se saltó el guardia que debía protegerte. No hay traza, no hay excepción, no hay nada que buscar. Solo un pedido enorme que salió crudo hacia el proveedor.

Eso es lo que encontramos en [`BerriAI/litellm`](https://github.com/BerriAI/litellm) `#46923`, y lo que este artículo intenta mostrar no es el bug: es **cómo se mide** para que el bug no sea una opinión.

Todo lo que sigue tiene un comando, un commit y un testigo.

---

## 1. La trampa del instrumento (la que había que encontrar antes de creer nada)

La primera regla de una auditoría es que el instrumento no es el objeto. Aquí el instrumento estaba mintiendo por una razón de una línea:

```
cd /tmp/litellm
/tmp/venv_lit103/bin/python -c "import litellm; print(litellm.__file__)"
  -> /private/tmp/litellm/litellm/__init__.py
```

Correr desde la raíz del clon pone **el árbol en `sys.path[0]`**. El paquete instalado en el virtualenv **nunca se importa**. Cualquier medición con `PYTHONPATH=/tmp/litellm` mide el árbol (`1.107.0` más un parche local), no la versión que el informe declara.

La etiqueta «probado en `1.103.0`» no estaba sostenida por el comando.

La reparación no es `PYTHONPATH` — es sacar el instrumento del árbol:

```
cd /tmp && /tmp/venv_lit103/bin/python -c "import litellm; print(litellm.__file__)"
  -> /private/tmp/venv_lit103/lib/python3.14/site-packages/litellm/__init__.py
VERSION_MEDIDA 1.103.0
```

Un instrumento que no imprime **de dónde** importa no está midiendo: está citando.

---

## 2. Seis brazos, un servidor que es testigo

`REPRO_46923_V4.py` (181 líneas) levanta un servidor HTTP local que **registra el payload que recibe**. Sin mocks: el servidor es el testigo. Si el pedido salió crudo, se ve en el cuerpo que llegó.

Parámetros declarados: `WINDOW = 1000`, prompt `"hello " * 3000` (≈ 6 000 tokens crudos, 18 000 caracteres).

Brazos: **A** `acompletion` con checks ON + hook · **B** `acompletion` con checks OFF + hook · **C** `acompletion` con checks ON y **sin** hook (control) · **D** `completion` sincrónico ON + hook · **E** sincrónico OFF + hook · **F** sincrónico OFF sin hook.

### `litellm==1.103.0` — site-packages, instrumento fuera del árbol · `RC=0`

| brazo | camino | checks | resultado | hook ejecutado | hits | payload |
|---|---|---|---|---|---|---|
| A | `acompletion` | ON | `RAISED ContextWindowExceededError` | NO | 0 | — |
| B | `acompletion` | OFF | `SUCCESS` | **SÍ** | 1 | `'short'` (5 chars) |
| C | `acompletion` | ON (sin hook) | `RAISED ContextWindowExceededError` | NO | 0 | — |
| D | `completion` | ON | `RAISED ContextWindowExceededError` | NO | 0 | — |
| E | `completion` | OFF | `SUCCESS` | **NO** | 1 | **crudo (18 000 chars)** |
| F | `completion` | OFF (sin hook) | `SUCCESS` | NO | 1 | crudo (18 000 chars) |

Las cuatro filas del informe público quedan respaldadas por **A · B · D · E**.

Y sobre `HEAD` limpio (`d7620c77a1eb`, versión `1.107.0`, extraído con `git archive HEAD litellm`, 79 MiB): **idéntico brazo por brazo**. El defecto no es de versión.

---

## 3. La causa no es «la compresión no llega»: es un hook inalcanzable

La lectura fácil es que el hook de compresión falla. No falla: **no existe en el camino sincrónico**.

```
grep "def pre_call_deployment_hook"  ->  0 ocurrencias
```

Solo hay `async def async_pre_call_deployment_hook` (`integrations/custom_logger.py:280`, invocado en `utils.py:1543` y `utils.py:2078`). **No hay hermano sincrónico.** En `Router.completion` no se puede esperar una corrutina, así que el hook nunca corre y el payload crudo sale al proveedor.

Un detalle de vocabulario que cambia el diagnóstico: no es «compresión que no llega». Es **un hook estructuralmente inalcanzable**.

---

## 4. El control negativo que corrige la lectura fácil

El brazo **C** es el que más información dio, y es el que casi nadie corre: `acompletion` con checks ON y **sin** hook registrado.

Resultado: `RAISED ContextWindowExceededError`.

Es decir: **el chequeo sí funciona**. El defecto no es «el chequeo nunca sirve», es «el chequeo decide sobre el crudo cuando un hook podría haberlo reducido». Sin el brazo C, el artículo habría dicho lo contrario con la misma seguridad.

Un banco de pruebas sin control positivo solo demuestra que el instrumento sabe decir *no*.

---

## 5. La retractación que no se reproduce

Aquí viene la parte incómoda, y la incluyo porque es el método.

En el mismo hilo publiqué una **retractación**: afirmé haber medido `main @ d7620c7`. Al medirla:

```
                                         HEAD limpio d7620c7      árbol /tmp/litellm
_has_pre_deployment_request_rewriters           0 ocurrencias            2 ocurrencias
litellm/router.py                                       16 171 líneas      16 200 líneas
git status --porcelain -- litellm/router.py               (limpio)              M
```

La función que citaba mi retractación **no existe en el commit que decía haber medido**: es la que **añade el parche candidato**. El número de línea que cité correspondía al árbol parcheado (+29 líneas), y el `WARNING router.py:13931` solo aparece ahí.

La retractación era una medición sobre el árbol equivocado. Se publicó, se midió contra el objeto y se declaró la discrepancia — no se editó el historial.

---

## 6. El parche candidato arregla A y empeora D

El parche que existe hoy en el hilo: **47 líneas · 2 331 B · SHA16 `210bdc4c91cfdddd`**, aplica con `patch --dry-run -p1` → `RC 0` sobre `HEAD` limpio. No es upstream: es una propuesta local.

Medido en el árbol parcheado:

| brazo | antes | después |
|---|---|---|
| A | `RAISED` | **`SUCCESS`** + `WARNING router.py:13931` |
| D | `RAISED` | **`SUCCESS` con payload crudo de 18 000 chars** |

Su condición `_has_pre_deployment_request_rewriters()` **omite el rechazo local sin distinguir camino**. En el camino sincrónico no hay hook que pueda correr, así que se pierde el único guardia y el pedido sobre-ventana sale crudo, **sin error y sin compresión**.

Un parche que mejora un brazo y degrada otro no es un parche a medias: es un **cambio de comportamiento** que el informe original no declaraba.

---

## 7. El defecto hermano: `ttl` que se calcula y no se lee

En `#47340` el patrón se repite con otra forma. El rate limiter calcula la caducidad del contador:

```
parallel_request_limiter_v3.py:1391-1397
  key=counter_key, increment_value=total_tokens, ttl=self.window_size
```

Y el camino en memoria la descarta:

```
in_memory_cache.py:255-264
  await self.async_increment(increment["key"], increment["increment_value"], **kwargs)
```

`increment["ttl"]` **nunca se lee**. Idéntico en `HEAD` (`1.107.0`, l. 266-273). La ventana por defecto es **60 s** (`LITELLM_RATE_LIMIT_WINDOW_SIZE`).

Mientras tanto, la rama Redis **sí** lo honra: `redis.call('SET', …)` seguido de `EXPIRE counter_key window_size` y `if ttl > 0 then EXPIRE counter_key ttl`.

Dos puertas, un mismo contrato: **una lo cumple y la otra lo tira sin avisar**. Quien despliega con Redis no ve el bug; quien despliega en memoria sí. La configuración decide si el defecto existe para ti.

---

## 8. Lo que **no** afirma esta auditoría

- **No** reproduce el caso del reporte original (267 860 tokens crudos contra ventana 262 144). El instrumento usa `WINDOW=1000` y un prompt de ≈ 6 000 tokens: mide **el orden**, no esa magnitud.
- El numeral «*sends 500 tokens raw*» de la fila 4 publicada **no tiene comando que lo respalde en este instrumento**: aquí el brazo sincrónico envía **18 000 caracteres**. La discrepancia se declara, no se adjudica: son dos instrumentos distintos.
- El default efectivo de `default_ttl` en `1.83.10` **no se midió**: se midió `base_cache.py:23` (60) y el del handler en `HEAD` (600).
- El parche **no** está mergeado ni se abrió PR con él.

Una auditoría sin sección de límites es publicidad.

---

## 9. El patrón, que es lo único que se puede generalizar

Los tres casos de este artículo no son tres bugs: son **una misma ley**.

| caso | cómo se ve desde fuera | qué pasó de verdad |
|---|---|---|
| `sys.path[0]` | «probado en 1.103.0» | se midió 1.107.0 + parche |
| brazo E | `SUCCESS`, 1 hit | payload crudo al proveedor |
| rama memoria | contador creado | sin caducidad de ventana |

**El estado peligroso es el que se parece al éxito.** Y por eso el instrumento que lo detecta no puede ser un `assert` que no falla: tiene que ser un guardia que **niega la escritura antes de tocar el archivo**.

Esa es exactamente la forma del gate que usamos para auditar sin ensuciar el árbol de nadie. Antes de escribir una línea exige una tupla de destino —`TARGET` absoluto · `BLOB_PRE` · marca exclusiva · líneas previas— y devuelve un código que autoriza o bloquea:

| RC | significado |
|---:|---|
| `0` | pre-vuelo correcto: el destino acepta edición sobre `BLOB_PRE` |
| `10` | el objeto no existe (creación) |
| `11` | **la marca ya vive en el destino** ⇒ colisión: la fila ya está escrita |
| `12` | el blob medido no es el contratado ⇒ el árbol se movió |
| `13` | estado de git sucio ⇒ modificaciones sin adjudicar |
| `14` | el destino no está en un árbol git ⇒ el gate no puede verificar identidad |
| `15` | el conteo de líneas no coincide con el contrato |
| `20` | uso incorrecto (tupla incompleta, o `TARGET` relativo) |

El `RC 14` existe por el mismo motivo que este artículo: sin árbol git, `git status` devuelve `128` con **salida vacía**, y un gate ingenuo lee «vacío» como «limpio» y da verde. Aquí la imposibilidad se declara.

Cada código sale **con su causa impresa**. Un `RC` correcto por la razón equivocada no es un gate: es una coincidencia.

---

## 10. Cómo lo corres tú

El gate de CI es un paquete, y el de pre-escritura es un script sin dependencias:

```bash
pip install git-preflight-gate        # gate de CI (trae PyYAML)
ci-authority-gate /path/to/your/repo  # RC 0 = pasa · RC > 0 = fail-closed, causa impresa
```

```bash
curl -fsSL https://raw.githubusercontent.com/alexisromtz-lab/git-preflight-gate/main/preflight-gate.sh -o preflight-gate.sh
bash preflight-gate.sh /ruta/absoluta/archivo.py <blob_pre> <marca_exclusiva> <lineas_pre>
```

El banco de casos viene incluido y se ejerce con `bash tests/must_fail.sh`: **9 casos, 9/9**, cada uno verificando el código **y** la causa — `20` (tupla incompleta), `20` (ruta relativa), `10`, `11`, `12`, `15`, `13`, `14`, y el control positivo `0`.

---

## Cierre

El bug de `#46923` es real, está vivo en `HEAD` y no lo arregla una versión. Pero el hallazgo del artículo no es el bug: es que **seis brazos y un testigo** convierten «creo que el hook no corre» en una tabla que cualquiera puede volver a correr — y que **el control negativo** fue el que impidió publicar la conclusión contraria con la misma seguridad.

---

**¿Quieres auditar tu repo?** Usa `pip install git-preflight-gate` o contáctame en [la-auditora](https://github.com/alexisromtz-lab/la-auditora).

Si prefieres empezar sin instalar nada, deja `owner/repo` en los comentarios y publico en este mismo hilo el primer conteo: qué tan limpio está tu árbol para un agente que escribe, y qué códigos devuelve el gate sobre tus rutas más movidas. Sin clonar tu código, sin pedirte una llave.
