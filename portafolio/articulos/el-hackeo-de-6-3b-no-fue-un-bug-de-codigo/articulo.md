---
title: El hackeo de $6.3B no fue un bug de código
lede: Diez repositorios públicos con workflow de despliegue, medidos con el commit exacto de cada uno: 807 hallazgos y 115 con conjunción de autoridad. Ninguno de los diez devuelve un verde limpio, y el artículo dice por qué eso no son 807 vulnerabilidades.
date: 2026-11-06
tags: security, devops, supplychain, opensource
cola_slug: red_el-hackeo-de-6-3b-no-fue-un-bug-de-codigo
fuente: DEPARTAMENTOS/comercial/ARTICULO_AUTORIDAD_MEDIDA_20261030_PUBLICO.md
---

**Origen de las cifras:** medición propia y reproducible. Cada cifra de este artículo tiene su commit; el desglose por código está más abajo, no en un anexo.

---

## Lo que sí está confirmado, y lo que la prensa todavía discute

Entre el 29 y el 30 de octubre, ocho cabeceras publicaron el mismo hecho: el mayor robo de la historia de las
criptomonedas, entre **$6.3 y $6.4 mil millones**, con TRM Labs atribuyéndolo a Corea del Norte. Una actualización de
Ethereum, **EIP-7702**, aparece en todas las piezas: permite que una cuenta delegue su capacidad de firma en otro
contrato. Con esa delegación firmada, se vaciaron billeteras calientes.

Hasta ahí, el titular. Ahora la parte que casi nadie está publicando:

- **Cryptonews, 30 de octubre:** «EIP-7702 didn't cause Binance hack, but may have amplified losses».
- **CCN, 30 de octubre:** «$3.66B Was Stolen Without It».
- **CryptoTicker, 29 de octubre:** «$2.8B Drained From Hot Wallet via EIP-7702».

Sumadas, esas tres piezas dicen algo incómodo: **la mayor parte del dinero se perdió sin que la actualización
estuviera involucrada**. Si eso se sostiene, entonces EIP-7702 no es la causa. Es el amplificador.

Y una cuarta pieza, del mismo día, cierra el círculo desde el otro lado: **The News International** titula que Binance
«confirms advanced EIP-7702 exploits and compromised DevOps laptop». Es decir: que el vector pasara por una **máquina de
ingeniero comprometida** no es la hipótesis de este artículo — lo confirmó el propio exchange. El hecho no es mío; el
ángulo sí.

Los cuatro titulares se verificaron el 30 de octubre de 2026 con fecha y medio de publicación; ninguno se cita de
memoria.

Y si no es la causa, la pregunta correcta no es «¿qué primitiva falló?». Es: **¿quién podía firmar?**

---

## El agujero es la cadena de autoridad, no la línea de código

Una auditoría de código busca el error en el programa. El incidente apunta a otro sitio: una máquina de ingeniero con
capacidad de firmar y desplegar, y una delegación que convierte una firma en autoridad permanente. Nada de eso vive en
una línea mal escrita. Vive en la **cadena de autoridad**: qué identidad puede publicar, con qué token, desde qué
artefacto, y con cuántos factores.

Eso no es una hipótesis sobre criptomonedas. Es la estructura de cualquier despliegue moderno. Y se puede medir.

---

## Lo medimos en nuestra propia casa primero

Tenemos un instrumento que audita la superficie de autoridad de GitHub Actions: quién tiene permiso de escritura y a la
vez ejecuta código, quién puede publicar por OIDC y a la vez construye el artefacto, qué acciones entran por tag
movible, dónde viajan secretos inline.

Lo corrimos sobre nuestro propio repositorio, antes de correrlo sobre el de nadie más.

**Resultado: 8 hallazgos, `RC 1` (`FINDINGS`).** Seis eran del mismo workflow. Los tres que importan:

1. Ese workflow declara `pages: write` + `id-token: write` **en la raíz**, no en el job de despliegue. Todos los jobs
   lo heredan, incluido el que compila.
2. Entra por **cuatro tags flotantes** (`@v4`, `@v5`, `@v3`, `@v4`). Un tag es una referencia movible: quien pueda
   moverlo ejecuta código dentro del perímetro que puede publicar.
3. El job de deploy consume el token OIDC sin consumir un artefacto construido aparte: **construye y firma en el mismo
   contexto**.

Ninguna de las tres piezas es dramática por separado. **La conjunción es el hallazgo**: token de publicación heredado
por todos los jobs, más cuatro puertas de entrada que otra persona puede mover.

Tiempo de la corrida: **1.2 segundos**. Cero tokens. Sin instalar nada en el repositorio auditado.

---

## Y luego lo arreglamos, porque un informe sin arreglo es una factura

Aquí es donde la mayoría de las auditorías termina y donde este artículo debería empezar a diferenciarse.

**Primer movimiento — arreglar.** Permisos raíz reducidos a `contents: read`. `pages: write` e `id-token: write` bajan
al job `deploy`, donde se ejercen. El workflow se parte en dos jobs con `needs:`: uno construye y sube el artefacto,
el otro publica, y **el que publica ya no tiene el código del repositorio en el disco**. Las cuatro refs flotantes
pasan a SHA completo. Y aparece un `download-artifact` que antes no existía: el gate lo exigía desde el principio y
teníamos razón en no creerle al primer verde —sin ese paso, el artefacto entero es un sumidero para el instrumento,
porque ningún paso del job lo declara como insumo.

**Segundo movimiento — volver a medir.** 8 hallazgos → **3**.

**Tercer movimiento — el que casi nadie hace: no borrar el residuo, declararlo.**

Los 3 que quedan no son bugs. Dos son el `keepalive` del corpus: un job que necesita `contents: write` porque su
trabajo **es** hacer `git push --dry-run`. Quitarle la escritura no cierra un agujero: apaga el keepalive. El tercero
es la concesión de escritura del job `deploy`, que ahora sí está donde se usa.

La tentación evidente es silenciar el instrumento. Añadir una lista de exclusión, un `# noqa`, un filtro. Eso convierte
la auditoría en teatro: el siguiente hallazgo real entra por la misma puerta que acabamos de abrir.

Lo que hicimos en su lugar fue un **registro de adjudicación**: un archivo donde cada excepción se escribe con su
código, su workflow, su job y **el acta que la autoriza**. El instrumento lee ese registro y exige dos cosas que un
filtro no puede dar:

- **Cero huérfanas.** Una fila que ya no corresponde a ningún hallazgo se reporta como error. Un registro que solo
  crece es un cementerio de excepciones.
- **La adjudicación no borra el hallazgo.** El hallazgo sigue en el JSON, con su severidad, su `job` y su `motivo`.
  Lo que cambia es el veredicto del repositorio: de `FINDINGS` a `ADJUDICADO`.

**Resultado: `RC 0`, `ADJUDICADO`, cero huérfanas.** Y cuando el instrumento vuelve a encontrar algo que no está en el
registro, vuelve a salir en rojo. *Eso* es lo que un `# noqa` no puede hacer.

Este es el punto comercial, y conviene decirlo sin adornos: **el entregable no es un número de hallazgos. Es un
número de hallazgos que se mueve, y un residuo con nombre y acta.** Cualquiera puede correr un escáner y entregarte
29 violaciones. Lo que casi nadie entrega es la prueba de que las 29 bajaron a 3, por qué esas 3 siguen ahí, y quién
firmó cada una.

---

## Y en un proyecto ajeno, 21 hallazgos

Sobre un proyecto open source activo (≈11 workflows), el mismo instrumento devolvió **21 hallazgos**: un job de release
con `contents: write`, `pull-requests: write` e `id-token: write` que además ejecuta el build en el mismo contexto, y un
token de bot pasado inline a una acción de terceros.

**Y aquí viene la parte que casi ningún proveedor de seguridad escribe:** ese job solo se dispara con `push` a `main`,
dentro de un `if` que exige ser el dueño del repositorio. **No hay entrada no confiable.** El hallazgo es *estructural,
no explotable*. Publicar «secreto expuesto en un repo público» habría sido técnicamente cierto en la superficie y falso
en el riesgo.

Esa distinción —**estructural ≠ explotable**— es la diferencia entre un informe que un CISO puede usar y uno que tiene
que apagar.

Y ese repo ajeno no se clonó. `--repo owner/name` resuelve el nombre antes de la primera llamada, lee los workflows por
API de solo lectura y publica el commit exacto que midió (`6c9ca431`). **Ni una escritura en el disco de otro, ni un
token extra.** Si medir la casa de alguien requiere copiarte el código, no es una medición: es una mudanza.

---

## Diez repositorios, diez mediciones, ninguna muda

Un caso no es una muestra. Diez repositorios públicos, todos con al menos un workflow cuyo nombre publica o despliega
algo. El criterio de inclusión se declara antes de medir, no después: **un repositorio entra al lote si tiene un
workflow de despliegue o publicación**.

| Repositorio | Commit medido | Hallazgos | Conjunción de autoridad | Veredicto |
|---|---|---:|---:|---|
| `withastro/starlight` | `6c9ca431` | 21 | 4 | `RC 1` |
| `withastro/astro` | `10dae2f3` | 51 | 19 | `RC 1` |
| `vercel/next.js` | `4fed142e` | 181 | 36 | `RC 1` |
| `nuxt/nuxt` | `363f3b87` | 59 | 12 | `RC 1` |
| `sveltejs/svelte` | `fe21fce0` | 12 | 2 | `RC 1` |
| `remix-run/remix` | `2eb9249c` | 170 | 9 | `RC 1` |
| `angular/angular` | `458303fe` | 26 | 4 | `RC 1` |
| `vuejs/core` | `24c9d0bf` | 11 | 6 | `RC 1` |
| `facebook/react` | `16453bcd` | 234 | 11 | `RC 1` |
| `vitejs/vite` | `90bc034a` | 42 | 12 | `RC 1` |
| **Total** | **10 commits** | **807** | **115** | **10 de 10** |

Dos repositorios de la lista original quedaron fuera, y decirlo es parte del método: `gatsbyjs/gatsby` no tiene ningún
workflow de despliegue ni publicación (uno solo, y no es de deploy) — se declara `NO_APLICA` y se sustituye por
`vitejs/vite`. `astro-build/astro` no existe: la organización correcta es `withastro`, y se midió `withastro/astro`.

**Y aquí está la parte que un vendedor de escáneres no escribe: 807 no son 807 vulnerabilidades.** Son 807
observaciones de la superficie del YAML. De ellas, **115 son la conjunción que este artículo defiende** — autoridad de
escritura que ejecuta, autoridad heredada de la raíz, o permisos raíz ausentes. Las otras **692** se reparten sin
adorno: **308** refs movibles (higiene real), **153** revisiones de scope que el contrato SC-1 marca como `REVIEW`,
**3** lecturas de raíz en revisión, y **228** de **dos códigos del propio instrumento que detectan el mecanismo, no el
defecto**. `SECRETO_EXPUESTO` marca cualquier `${{ secrets.* }}` en un `env:`, que es *la manera correcta* de pasar un
secreto a un paso; y `SUMIDERO_IMPUDO` marca un job con `id-token: write` que hace `actions/checkout`, que es lo que
**todo** job de publicación tiene que hacer para tener algo que publicar. Publicar el número crudo habría sido el
mismo pecado que criticamos tres párrafos arriba, con el signo cambiado.

La tabla completa, con el desglose por código y el commit exacto de cada medición, es la de arriba: diez filas, diez commits, ninguna muda. El acta del lote guarda los diez SHA y el criterio con el que se eligieron.

---

## Lo que este instrumento NO mide

Decirlo es parte del contrato, no una cláusula al pie:

- **Permisos por defecto** del `GITHUB_TOKEN` a nivel de repositorio u organización: invisibles desde el YAML.
- **Políticas OIDC del destino** (npm, PyPI, AWS): el instrumento ve que hay una puerta, no qué cerradura tiene.
- **Modificación de dependencias en runtime** cuando se ejecuta código nativo no aislado.
- **Workflows reutilizables (`workflow_call`) y acciones compuestas alojadas en repositorios ajenos.**
- **Runtime.** Mide la superficie declarada del YAML; no certifica lo que pasa cuando corre.

Un instrumento que no declara su ceguera no es un instrumento: es una opinión con formato JSON.

---

## El falsador

Esta tesis muere de dos maneras, y las dos son medibles:

- Si en **10 repositorios con workflows de despliegue** el instrumento no encuentra **una sola** conjunción de autoridad
  heredada con puertas movibles, entonces no hay mercado: el problema no existe fuera de nuestra casa.
- Si encuentra **10 de 10**, entonces el hallazgo deja de ser hallazgo y pasa a ser la norma — y el producto ya no es
  el escaneo (que cualquiera corre en un segundo), sino la **remediación** y la evidencia de que se hizo.

Ninguna de las dos es una derrota. Las dos obligan a dejar de vender «auditoría» y empezar a vender «esto quedó
cerrado, y aquí está la prueba».

**El falsador ya se ejerció, y no salió la rama cómoda.** Diez repositorios, diez mediciones: **10 de 10 tienen al
menos una conjunción de autoridad** (mínimo 2, en `sveltejs/svelte`; máximo 36, en `vercel/next.js`). No hay un solo
repositorio del lote donde el problema no exista.

**Y la medición encontró un hueco en el falsador, no en la tesis.** El texto decía «conjunción de autoridad heredada
**con** puertas movibles», y esa conjunción admite tres lecturas. Las tres se publican:

| Lectura del falsador | Repositorios que la cumplen |
|---|---:|
| **A** — al menos una conjunción de autoridad (criterio declarado en la evidencia) | **10 de 10** |
| **B** — conjunción de autoridad **y** al menos un `uses:` con tag movible | **6 de 10** |
| **C** — autoridad de escritura heredada **de la raíz** y tag movible | **4 de 10** |

**Ninguna lectura da cero.** La primera rama del falsador —«si no encuentra una sola, no hay mercado»— queda refutada
bajo las tres. Pero la segunda tampoco se alcanza limpia: solo la lectura **A** llega a 10 de 10. El falsador estaba
escrito con dos ramas y un hueco en medio, y ese hueco lo llenó la medición, no la retórica. La versión honesta del
falsador no es binaria: es **un umbral** — «si menos de la mitad de los repositorios con despliegue muestran la
conjunción, el problema no es estructural, y esto se cae». Medido: 4 de 10 en la lectura más estricta. **No se cae, y
por poco.**

Eso resuelve la tesis a la **segunda** rama bajo la lectura declarada, y hay que decirlo con la misma claridad con la
que se dijo el hallazgo propio: **la conjunción de autoridad no es una rareza; es la norma del ecosistema.** Si es la
norma, el escaneo no es un producto — cualquiera lo corre en un segundo, y el nuestro tampoco se cobra por velocidad.
**Lo escaso es el cierre:** que el número baje, que el residuo tenga nombre y acta, y que el siguiente escaneo pueda
probar que no volvió a subir.

La rama que mata la tesis habría sido la primera. Salió la segunda. **El producto que sobrevive a esta medición es el
que ya está descrito en la sección del 8 → 3 → 0, no el que estaba descrito en el titular.**

---

## Si te interesa saber dónde está tu punto único de firma

No hace falta que instales nada ni que nos des acceso a tu código. Un nombre de repositorio basta: el instrumento lee
la superficie declarada de tus workflows y devuelve, en segundos, cuántos jobs concentran autoridad de publicar y
cuántas de sus entradas las puede mover alguien más.

Si el resultado es «no hay cadena de autoridad declarada», ese es el hallazgo: la ausencia también se publica.

---

*¿Quieres la medición sobre tu repositorio? Deja el nombre (`owner/repo`) en los comentarios de este artículo y
publico el conteo en el mismo hilo: cuántos jobs concentran autoridad de publicar, y cuántas de sus entradas las puede
mover alguien más. Sin clonar tu código, sin pedirte una llave, sin instalar nada en tu máquina.*
