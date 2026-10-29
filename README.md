# La Auditora

Auditorías de software reproducible, fijadas a un commit y con sus límites escritos. Sitio
bilingüe: [español](https://alexisromtz-lab.github.io/la-auditora/) ·
[English](https://alexisromtz-lab.github.io/la-auditora/en/).
Este README es la **fuente única de verdad** del repositorio: el sitio resume, el Data Room
publica la evidencia, y lo que no está aquí no es una auditoría publicada.

## Qué es

Una auditoría es una pregunta acotada, hecha sobre un objeto fijo y con un resultado que otra
persona puede volver a obtener. En este repositorio cada entrada declara tres cosas: **qué
commit** se miró, **qué se midió** y **qué quedó fuera**. Los resultados negativos —«cero ciclos
eager en el ámbito»— se publican igual que los positivos, porque un cero medido también es
evidencia. Lo que no se publica es una opinión sobre el estado actual de un proyecto: un
resultado pertenece al commit que lo produjo, no a la rama móvil.

## Las cuatro superficies, y cuál manda

| superficie | qué contiene | relación |
|---|---|---|
| `README.md` (este archivo) | índice completo, cohortes, comandos, licencia, contacto | **manda** |
| `index.html` · `en/index.html` | seis resúmenes bilingües con commit-pin y un enlace al Data Room | resume este archivo |
| Data Room (`releases`) | cinco grafos de imports en JSON + la herramienta que los mide | es la evidencia; aquí solo se indexa |
| metadatos del repo y del perfil | descripción, topics, `homepageUrl`, licencia, «Start here» | pendiente, ver [Pendientes](#pendientes) |

## Índice de auditorías publicadas con datos

Cinco snapshots publicados en el release
[`arch-index-20261028-v2`](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v2)
(28-oct-2026). Cada archivo lleva el repo y el commit completo dentro, no solo en el nombre.

| repositorio | commit-pin | módulos | aristas internas | SCC cíclicas | tamaños | sin expansión de `__init__` | activo |
|---|---|---|---|---|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain/commit/facf2788ae1f60c62f2397d15698237c405a5f05) | `facf2788ae1f60c62f2397d15698237c405a5f05` | 40 | 131 | 2 | 19, 3 | 0 | `public_graph_langchain_facf2788.json` |
| [huggingface/transformers](https://github.com/huggingface/transformers/commit/95bafdcccfffe17ec383999fc39273867b11385e) | `95bafdcccfffe17ec383999fc39273867b11385e` | 3139 | 26078 | 8 | 176, 26, 5, 3, 2, 2, 2, 2 | 6 | `public_graph_transformers_95bafdcc.json` |
| [vllm-project/vllm](https://github.com/vllm-project/vllm/commit/7e3e3f6ab652550fdefecd8e9823394fd8e51950) | `7e3e3f6ab652550fdefecd8e9823394fd8e51950` | 3003 | 34061 | 23 | 1648, 25, 18, 12, 12, 10, 8, 8, 7 ×5, 4, 3, 3, 3, 2 ×7 | 8 | `public_graph_vllm_7e3e3f6a.json` |
| [bentoml/BentoML](https://github.com/bentoml/BentoML/commit/0aa1aea52b63b82100ff93675eff25f6428fb841) | `0aa1aea52b63b82100ff93675eff25f6428fb841` | 211 | 1287 | 5 | 78, 4, 3, 3, 2 | 4 | `public_graph_bentoml_0aa1aea5.json` |
| [run-llama/llama_index](https://github.com/run-llama/llama_index/commit/619d74664e8404612038bc15a1a40c686037277c) | `619d74664e8404612038bc15a1a40c686037277c` | 480 | 4024 | 4 | 334, 3, 2, 2 | 4 | `public_graph_llamaindex_619d7466.json` |

Los cinco llevan `source_bytes_verified: false`: el grafo es estático, no se re-verificaron los
bytes de cada archivo contra el checkout al proyectarlo. Se declara, no se esconde.

Release anterior: [`arch-index-20261028-v1`](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v1)
(28-oct-2026, seis activos: los mismos cinco grafos sin la capa de sensibilidad).

## Auditorías publicadas en el sitio

Seis resúmenes en prosa con commit-pin, verificables en la página. **No tienen snapshot en el
Data Room**: son otra cohorte, medida con otro método.

| repositorio | commit-pin | hallazgo |
|---|---|---|
| [pytorch/pytorch](https://github.com/pytorch/pytorch/commit/210bb7ca5c4e08c40513c389c14b1adbf4a82f8c) | `210bb7ca5c4e08c40513c389c14b1adbf4a82f8c` | 45 archivos de tests sin camino de ejecución en el CI (alcanzabilidad estática) |
| [django/django](https://github.com/django/django/commit/641e9368105e07237e4d09cf951f3038cde4d973) | `641e9368105e07237e4d09cf951f3038cde4d973` | 3 ciclos eager en backends de base de datos, dependientes del orden de carga |
| [tenstorrent/tt-metal #59955](https://github.com/tenstorrent/tt-metal/pull/59955) | rotura `7d399796b4770ca95e15c7877e157872dc87ba82` · reparación `78957cf011ab40db8e4f6283a61ce4839c51b896` | un job verde ocultó 12 de 13 nodos afectados tras abortar con `-x` |
| [huggingface/transformers](https://github.com/huggingface/transformers/commit/b4a5b4b2c652615ef0c4dfa8adabad1756a6ec3f) | `b4a5b4b2c652615ef0c4dfa8adabad1756a6ec3f` | resultado nulo: 0 ciclos eager, 0 de 8 rutas del PR intersectadas |
| [vllm-project/vllm-omni](https://github.com/vllm-project/vllm-omni/commit/9573acc90213cb473c30d64115ab0e1dd1a32d9a) | `9573acc90213cb473c30d64115ab0e1dd1a32d9a` | 0 ciclos eager en `vllm_omni/platforms/`; cinco componentes con ciclos diferidos |
| [pallets/flask](https://github.com/pallets/flask/commit/d086db856be187255b8ec61ef409357393020f32) | `d086db856be187255b8ec61ef409357393020f32` | 1 SCC mixta de 18 módulos, 0 ciclos eager |

**Las dos cohortes no coinciden, y se declara a propósito.** El único repositorio que aparece en
las dos listas es `huggingface/transformers`, y **en commits distintos**: `b4a5b4b2` en el sitio,
`95bafdcc` en el Data Room. Quien siga el commit-pin de la página hasta el Data Room encontrará
cinco grafos que miden otra cosa sobre otro objeto. Eso no es un fallo de medición: son dos
productos con el mismo nombre genérico, y por eso están en dos tablas separadas.

## En progreso

Pendientes declaradas. **Sin acta, sin snapshot y sin commit-pin**: nada de lo que sigue es una
auditoría publicada hasta que aparezca en una de las dos tablas de arriba.

| repositorio | estado | qué falta |
|---|---|---|
| `stripe/stripe-python` | pendiente | acta, grafo de imports y commit fijado |
| `ray-project/ray` | pendiente | acta, grafo de imports y commit fijado |

## Cómo se reproduce

Desde un directorio vacío, con el release a la vista:

```bash
gh release download arch-index-20261028-v2 \
  --repo alexisromtz-lab/la-auditora \
  --pattern 'public_graph_langchain_*.json' \
  --pattern 'calculate_arch_index.py'

python3 calculate_arch_index.py public_graph_langchain_facf2788.json --graph-sensitivity
```

Salida esperada (resumida): `cyclic_scc_count: 2`, tamaños `[19, 3]`, `node_count: 40`,
`unique_internal_edges: 131` y `graph_input_sha256` que empieza por `5733904a5821`. Comparar
contra `graph_sensitivity_langchain.json` del mismo release: **debe coincidir byte a byte**.

Medido el 29-oct-2026: los cinco pares `public_graph_*.json` → `graph_sensitivity_*.json`
reproducen **5 de 5 idénticos**, con Python 3.12.13 y solo biblioteca estándar. Control interno
del instrumento: `python3 calculate_arch_index.py --self-test` → `SELF-TEST OK: 3 SCC, 2 cyclic SCC`.

Para medir otro repositorio hace falta primero la ingesta `ingesta_ast/v2` de ese checkout; el
JSON publicado es la entrada, no la salida del programa.

## Alcance y límites

- **Objeto fijado.** Cada resultado pertenece al commit escrito arriba. No se extrapola a la rama
  ni al estado actual del proyecto.
- **Alcance visible.** Un grafo de imports no dice nada sobre runtime, rendimiento, seguridad ni
  comportamiento. El acta de Django lo dice de forma expresa: **no es una vulnerabilidad**.
- **`type_checking` excluido.** 95 imports de ese tipo quedan fuera del grafo de LangChain
  (`type_checking_imports_excluded: 95`), y con ellos cualquier ciclo que solo exista ahí.
- **Sensibilidad al expansor.** Con y sin expansión de `__init__.py` ancestrales, LangChain pasa
  de 2 componentes cíclicas a 0. El número no es robusto al método, y por eso se publican los dos.
- **`source_bytes_verified: false`** en los cinco snapshots.

## Falsabilidad y negativos publicables

- **Negativos:** «cero ciclos eager en el ámbito» es un resultado medido, no una certificación de
  que el sistema esté libre de defectos.
- **Qué falsaría un ciclo publicado:** que la ingesta haya omitido un módulo dentro del ámbito, o
  que el import esté diferido y el clasificador lo haya contado como eager. Ambos son
  reproducibles con los archivos publicados.
- **Qué falsaría la sensibilidad al expansor:** correr `--graph-sensitivity` sin expansión y
  obtener un conteo distinto de 0 para LangChain.
- **Controles:** el instrumento trae `--self-test` con un control mínimo de Tarjan; un instrumento
  sin control negativo no se publica.

## Contacto

- Propuestas y preguntas: sección **Contacto** del sitio —
  [español](https://alexisromtz-lab.github.io/la-auditora/#contacto-titulo) ·
  [English](https://alexisromtz-lab.github.io/la-auditora/en/#contact-title).
- Sitio editorial y contexto: [arquitectocuantico.com](https://arquitectocuantico.com/).
- **Pendiente declarado:** el buzón que hoy recibe consultas es el que aparece en la página; falta
  publicar un buzón de dominio propio o un formulario. Medido el 29-oct-2026: `arquitectocuantico.com`
  responde 200 y no expone ni formulario ni ruta de contacto (`/contacto`, `/contact`, `/escribir`
  → 404). No se inventó una dirección.

## Licencia

- **Código** (`calculate_arch_index.py` y este sitio): **MIT** — ver [`LICENSE`](./LICENSE).
- **Datos y texto de auditoría** (los `public_graph_*.json`, los `graph_sensitivity_*.json` y los
  resúmenes): **CC BY 4.0** — ver [`LICENSE-DATA`](./LICENSE-DATA).

Reutilizar los datos requiere atribución; reutilizar la herramienta, no.

## Pendientes

| # | qué | dónde |
|---|---|---|
| 1 | `homepageUrl` vacío y `topics` sin declarar en el repo | ajustes de GitHub |
| 2 | la página menciona una auditoría de **Scrapy** que no existe en ninguna tabla | `index.html`, aviso «Frontera» |
| 3 | `la-auditora` no aparece en «Start here» del perfil de `alexisromtz-lab` | repo de perfil |
| 4 | correo de dominio o formulario en lugar del buzón actual | página y este archivo |

<!-- HUELLA-README-LA-AUDITORA-20261029 -->
