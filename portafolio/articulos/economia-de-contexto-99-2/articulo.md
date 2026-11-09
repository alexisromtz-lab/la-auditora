---
title: Economía de contexto — el 99.2 %
lede: El 99.2 % del coste de un agente es input, no output. Medido sobre dos generaciones del mismo panel: el total se mueve 28.19 % entre corridas, la proporción se mueve 0.06 puntos. Por eso lo que se vende es una razón, no un recibo.
date: 2026-11-06
tags: ai, llm, productivity, opensource
cola_slug: red_economia-de-contexto-99-2
fuente: DEPARTAMENTOS/comercial/ARTICULO_ECONOMIA_CONTEXTO.md
---

**Regla de este documento:** ninguna cifra se escribe a mano. Cada una lleva el comando o el `archivo:línea` que la produce, y la que no tiene denominador declarado no se publica.

---

## 1 · La tesis en una frase

**El coste de un agente no está en lo que el modelo escribe; está en lo que la llamada arrastra.** Medido sobre
28 971 llamadas reales de 5 días: el `output` es el **0.89 %** del consumo. El **99.11 %** es `input`
(`REPORTE_TOKENS.md:130`).

De ahí el corolario incómodo: optimizar el modelo, el prompt o la temperatura mueve menos del 1 % de la factura.
**El 99 % restante lo decide cuántas veces se reenvía la historia.**

## 2 · El número del negocio: coste por tarea verificada

No coste por llamada — coste por **tarea**, que es la unidad en la que se factura y en la que se decide.

| métrica (mediana por tarea) | valor | n |
|---|---:|---:|
| consumo total de la tarea (`input` + `output`) | **18 024 682.50** tok | 10 |
| de eso, `output` del modelo | **141 574.50** tok | 10 |
| llamadas al modelo que hizo falta encadenar | 217.50 | 10 |
| tokens reenviados **por cada** llamada (arrastre) | 80 032.00 | 10 |

locus: `REPORTE_TOKENS.md:185-188 @ blob 1c09a667 (213 l)` — correcto para la generación que §2 congela; en la generación viva la tabla vive en `:188-197 @ blob bc67c4c5` (ver §8.1).

**Una tarea cuesta 18.02 M tokens. De ellos, 141.6 k —el 0.79 %— es lo que el modelo produjo.** El resto es la
misma historia contada otra vez doscientas diecisiete veces.

Arrastre = `1 − 141 574.50 / 18 024 682.50` = **99.215 %**.

> No es un 95 %. Es un 99.2 %. La diferencia importa: un 95 % todavía admite la fantasía de que el 5 % restante
> —«el trabajo real»— sea donde está la palanca. Un 99.2 % dice que no hay tal 5 %.

## 3 · Cómo se reproduce (esto es la parte que se cobra)

El reporte no es una opinión con tablas. Es un instrumento determinista sobre evidencia del propio disco:

```bash
git cat-file blob bb7190b0 > /tmp/ttr.json           # el crudo de atribución, congelado por blob
.venv/bin/python tools/reporte_tokens.py --ttr /tmp/ttr.json --md-out /tmp/panel.md   # RC 150 = nominal
```

La corrida de verificación del 30-Oct-2026 reproduce `18 024 682.50` y `141 574.50` **exactamente**, desde el
blob `bb7190b0` y no desde un archivo temporal perdido. Un lector tercero puede hacer lo mismo sin pedirnos
nada.

**Por qué esto es la parte comercial y no la técnica:** cualquier proveedor puede decir «optimizamos tu
contexto». Lo que casi nadie puede hacer es entregar el comando con el que el cliente comprueba la cifra en su
propia máquina.

## 4 · La trampa del porcentaje: tres denominadores, tres verdades

Aquí está el hallazgo que convierte el artículo en algo que no existe en la literatura de agentes: **el mismo
ahorro mide tres cifras distintas según contra qué se divida**, y casi todo el material publicado no declara el
denominador.

Caso medido: recortar el bloque de esquemas de herramientas del perfil de 73 a 22 herramientas.

| contra qué se divide | cifra | lectura honesta |
|---|---:|---|
| el bloque de esquemas del perfil que lo protagoniza | **57.9 %** | «recorté el bloque un 58 %» |
| el `input` de ese mismo perfil | **15.4 %** | «ahorré el 15 % del input» |
| el `input` de **todo** el corpus | **8.73 %** | «ahorré el 8.7 % del gasto» |

Las tres son ciertas. Solo la tercera es «del total», y es la más pequeña. Un proveedor que publica la primera
como si fuera la tercera está vendiendo un número con el sujeto cambiado — y ese error es indistinguible de una
mentira en el contrato, aunque no haya intención.

El tax ponderado real del bloque de esquemas es **730 356 952 / 2 472 640 471 = 29.54 %** del input
(`REPORTE_TOKENS.md:142-160`, suma sobre llamadas). Casi un tercio del dinero se va en declarar herramientas.

## 5 · Y la poda no es lineal: el tax depende del conjunto, no del número

La intuición de mercado —«menos herramientas, menos coste»— es **falsa**, y se refuta con el mismo panel:

| herramientas expuestas | `tool_tokens` por llamada | n |
|---:|---:|---:|
| 98 | 26 109.00 | 343 |
| 97 | **25 818.00** | 933 |
| 94 | **32 768.00** | 1 |
| 22 | 9 464.00 | 416 |
| 21 | **9 173.88** | 205 |

locus: `REPORTE_TOKENS.md:147-160`.

Menos herramientas (94) cuestan **26.9 % más** que más herramientas (97). Y una herramienta menos que 22 (o sea
21) cuesta **3.07 % menos**. El tax lo fija el **contenido** del bloque —qué esquemas, con qué descripción y qué
esquema JSON—, no su longitud en unidades.

Consecuencia para quien vaya a comprar esto: la pregunta correcta no es «¿a cuántas herramientas podamos?» sino
**«¿qué conjunto, medido, para qué tarea?»**. Un contrato que prometa un porcentaje por umbral de cardinal está
prometiendo algo que el corpus no sostiene.

## 6 · Lo que este artículo NO afirma (y por qué decirlo lo hace vendible)

1. **No afirma coste por fila.** El 99.2 % es la **mediana de un panel de 200 commits evaluados**, con 10 tareas
   atribuidas. La atribución por enlace existe pero es residual: `por_enlace = 1`, `por_ventana = 199`
   (`REPORTE_TOKENS.md:69`). **No podemos decirle a un cliente «tu tarea cuesta X»**. Podemos decirle «la tarea
   mediana de este panel cuesta 18.02 M». Es un dashboard de flota, no un recibo por servicio, y el recibo es
   el producto que falta.
2. **No afirma ahorro monetario.** El campo `cost` del runtime viaja con `isByok: true`: un `0.0` ahí significa
   «no facturado a esta cuenta», no «gratis». Sin tarifas no hay euros (`REPORTE_TOKENS.md` §8).
3. **No afirma routing.** La comparación de modelos por coste está `NO_MEDIDO` por la misma razón.

Publicar los límites no debilita el artículo: **es la única forma de que las tres cifras que sí se afirman sean
creíbles.**

## 7 · Cierre

El sector mide tokens como quien mide gasolina: litros consumidos. La diferencia entre eso y economía es saber
**cuántos de esos litros movieron el coche y cuántos se quemaron en el semáforo**. En un agente, el semáforo es
el contexto reenviado, y en esta medición son **99.2 de cada 100 litros**.

Quien no mide el arrastre no está optimizando un agente: está eligiendo un motor más pequeño para un coche que
no avanza.

---

**Evidencia completa y reproducible:** `REPORTE_TOKENS.md` · **Instrumento:** `tools/reporte_tokens.py` (RC 150
nominal) · **Crudo congelado:** `crudos/reporte_ttr_20261030.json @ bb7190b0`.

## 8 · La cifra tiene fecha (y la razón no)

Este artículo se escribió sobre una **generación** del crudo, y hay que decirlo con número porque el defecto es
la especialidad de la casa: el productor escanea el `session-state` del host, que **crece mientras se escribe**,
así que dos corridas del mismo comando el mismo día **no** dan las mismas medianas.

| generación | blob del crudo | `T_total` mediana | `T_completion` mediana | llamadas | arrastre |
|---|---|---:|---:|---:|---:|
| §2 de este artículo | `bb7190b0` | 18 024 682.50 | 141 574.50 | 217.50 | **99.215 %** |
| vigente, en el repo | `03e9072b` | 23 105 392.50 | 167 397.00 | 276.50 | **99.276 %** |
| salto entre las dos | — | **+28.19 %** | +18.24 % | +27.13 % | **+0.061 pp** |

**Esa fila del salto es la tesis del artículo medida contra sí misma.** El absoluto se mueve un **28.19 %** según
cuándo se corra el comando; la **razón se mueve 0.061 puntos porcentuales**. Es exactamente por esto que el
número que se vende es una proporción y no un total: **una proporción sobrevive a la regeneración, un total no.**
Las dos generaciones dan **99.2 %** y **99.3 %** — y en ningún caso el **95 %** que circulaba. Una de las cuatro
columnas de §2, `tokens por llamada = 80 032.00`, es idéntica en las dos generaciones: la mediana de una razón
se queda quieta aunque sus dos operandos se muevan.

Dos consecuencias que no se esconden:

1. **`REPORTE_TOKENS.md:185-188` quedó superado por su propio sidecar, y ya se corrigió allí.** El sidecar del
   crudo (`crudos/reporte_ttr_20261030.meta.json`) declaró, en el mismo
   árbol, que «la primera generación publicó `18024682.5 / 141574.5` y esta publica `23105392.5 / 167397.0`» y
   que «la cifra que vale es la del crudo con su blob». La tabla §7 del reporte publicaba la primera: se midió y
   se corrigió en `REPORTE_TOKENS.md` (**commit `45917cec`**), donde hoy vive en `:188-197 @ blob bc67c4c5` y
   publica `23 105 392.50 / 167 397.00`. El locus de §2 no estaba mal escrito: era correcto para el blob que cita
   —`1c09a667`, 213 líneas— y lo desplazó el commit vecino `6d74da06`, que movió la tabla a `189-192` antes de
   que la corrección la dejara en `190-193`. **Este apartado no reescribe §2**: §2 se deja tal como se escribió,
   con su generación congelada y su blob, para que la diferencia entre las dos sea auditable en vez de invisible.
   Es **adenda, no reemplazo** — ahora con el cierre fechado, no con la deuda abierta.
2. **Quien corra el comando hoy obtendrá una tercera cifra.** La cifra no es el producto; **el comando lo es**.
   Por eso §3 entrega el comando y el blob, no la tabla.

`HUELLA-ARTICULO-ECONOMIA-CONTEXTO-VIGENCIA-20261030
`HUELLA-ARTICULO-COLATERAL-M7-CERRADO-20261030``
