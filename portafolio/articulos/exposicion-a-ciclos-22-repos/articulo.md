---
title: Casi la mitad del código de 22 proyectos depende de un ciclo, y el indicador habitual premia al que peor está
lede: Sobre 33 688 módulos leídos en 22 proyectos, el 28,1 % está dentro de un ciclo y el 48,3 % queda expuesto a uno. Los dos números no ordenan igual: la correlación de Spearman entre ellos es +0,041.
date: 2026-11-20
tags: arquitectura, python, grafos, opensource
---

## El segundo número

Cuando se habla de deuda arquitectónica en Python se publica un número: cuántos ciclos hay. Medí dos cosas sobre 22 proyectos en lugar de una — cuántos módulos están **dentro** de un ciclo y cuántos, sin estarlo, **dependen** de uno.

| qué se midió | magnitud | cómo se obtuvo |
|---|---:|---|
| proyectos | **22** | commits elegidos a mano, cada proyección sobre el commit que declara su fila |
| módulos leídos | **33 688** | suma del campo `scc.modules` de las 22 proyecciones públicas |
| módulos dentro de un ciclo | **9 466 · 28,1 %** | pertenecen a un componente fuertemente conexo de tamaño > 1 |
| módulos expuestos | **16 256 · 48,3 %** | no están en un ciclo, pero alcanzan uno siguiendo el grafo de importaciones |

El segundo número es el que decide si un cambio en el ciclo te despierta a las tres de la mañana.

«Expuesto» tiene una definición mecánica y comprobable: un módulo que no pertenece a ningún componente cíclico, pero que alcanza uno siguiendo el grafo de importaciones. Es decir: importa, directa o transitivamente, algo que está dentro de un ciclo.

## El conteo de ciclos no ordena nada

Ordené los 22 proyectos por cantidad de componentes cíclicos y volví a ordenarlos por exposición. La correlación de Spearman entre los dos órdenes es **+0,041** sobre 22 filas: prácticamente cero. El conteo de ciclos no dice cuánto código cuelga de uno.

Cuatro proyectos tienen exactamente **un** componente cíclico, y sus tamaños van de 33 a 801 módulos:

| proyecto | componentes cíclicos | módulos en el mayor |
|---|---:|---:|
| apache/superset | 1 | 801 |
| gradio-app/gradio | 1 | 147 |
| pydantic/pydantic | 1 | 64 |
| stripe/stripe-python | 1 | 33 |

El mismo número para cuatro proyectos, con un factor de 24 entre el primero y el último. Otro par: apache/airflow y pytest-dev/pytest tienen dos componentes cíclicos cada uno, y suman 367 módulos atrapados frente a 4 — el mayor de airflow encierra 363 módulos y el de pytest encierra 2.

## Quién produce la exposición

Hipótesis de trabajo: el responsable no es «tener ciclos», es que el `__init__` del paquete esté dentro de uno. En 6 de las 10 filas donde la raíz del paquete se pudo resolver, la raíz está dentro del componente mayor. Los otros 12 proyectos quedan **sin medir** en este punto: el campo `paquete` de su proyección trae el literal `repo`, que no es un módulo. Ahí no hay un falso, hay ausencia de dato, y una ausencia no se lee como un cero.

El caso extremo es huggingface/transformers: 3 139 módulos, ocho componentes cíclicos, el mayor de 176 módulos, y el 91,9 % del paquete expuesto — 2 886 módulos de 3 139. El mecanismo está en el grafo: `transformers` es el nodo con más entrantes, 3 103 de esos 3 139 módulos lo importan, y ese nodo está dentro del ciclo de 176. Cuando el `__init__` cae en un ciclo pequeño, cada módulo del paquete pasa a depender de él.

## El indicador premia al peor

pytorch/pytorch tiene el ciclo más grande de los 22: **1 660 módulos**, el 65,7 % de los 2 527 del paquete, y 1 710 dentro de ciclos en total (el 67,7 %). Su exposición es de 493 módulos, el 19,5 %.

vllm-project/vllm: 1 648 en el componente mayor sobre 3 003 módulos (el 54,9 %), 1 801 dentro (el 60,0 %) y sólo 704 expuestos (el 23,4 %).

En los dos casos la exposición es baja por la peor razón posible: el ciclo se tragó el paquete y no quedó nadie fuera a quien exponer.

stripe/stripe-python es el espejo: 1 651 módulos, un único ciclo de 33 módulos (el 2,0 %) y 1 368 expuestos (el 82,9 % de 1 651). Ordenando por exposición, transformers encabeza la lista y pytorch cae a la mitad baja. Ordenando por cuánto del paquete está atrapado en un solo componente, el orden se da la vuelta.

Ninguno de los dos números es «el bueno». El error es publicar uno solo y llamarlo madurez arquitectónica.

## Punto ciego — lo que esta pieza no afirma

No afirma que un ciclo cause un fallo. Medí topología estática de importaciones en 22 commits; no ejecuté nada ni crucé los grafos con incidentes. Una medición previa y publicada del mismo corpus encontró 2 rupturas en 1 449 módulos: los ciclos dicen dónde mirar, no qué se va a romper.

No afirma que la exposición implique riesgo de ejecución. Un módulo expuesto puede importar el paquete raíz una vez, al arrancar, y no volver a tocarlo.

No afirma que los 12 proyectos sin raíz resuelta estén libres de un `__init__` cíclico: están sin medir, y por eso el crudo los marca como tales en vez de contarlos como cero.

No afirma que 22 proyectos sean una muestra. Son 22 commits elegidos a mano, con nombres grandes, no un sorteo; la tasa vale para esos 22 y para nadie más hasta que se repita sobre otro lote.

No afirma que el instrumento sea portable para el lector: calcula con `tools/calculate_arch_index.py`. Lo que cualquiera puede verificar sin él es la aritmética, descargando las 22 proyecciones públicas y sumando los campos `scc.*`, que es exactamente lo que hice aquí.

## Reproducir

```
.venv/bin/python tools/calculate_arch_index.py ingesta_ast_v2_mlflow_mlflow_cd1597e989e8.json --repo mlflow/mlflow
```

Las 22 proyecciones están en el release `arch-index-20261029-batch2` del data room; el crudo de esta medición es un JSON de 433 líneas con `sha256:ff0c2459a62c8276`.

## CTA único

Antes de aceptar cualquier informe de arquitectura — éste incluido — pide los dos números: cuántos módulos están dentro de un ciclo y cuántos dependen de uno. Si sólo trae el primero, trae el que se puede abaratar.

- Las 22 proyecciones: https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2
- El instrumento: https://alexisromtz-lab.github.io/auditor-toolkit/
- La misma pieza en dev.to: https://dev.to/alexisromtz7/casi-la-mitad-del-codigo-de-22-proyectos-depende-de-un-ciclo-y-el-indicador-habitual-premia-al-que-3ecn
