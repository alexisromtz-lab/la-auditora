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

La [muestra de diagnóstico FinOps](./portafolio/DIAGNOSTICO_FINOPS_EJECUTIVO.pdf) usa datos sintéticos. Sus cifras y su veredicto ilustran el formato: no corresponden a una cuenta real, no prueban ahorros y no validan el precio ni el coste operativo del servicio.
<!-- HUELLA-LA-AUDITORA-FINOPS-LEADMAGNET-README-20261031 -->

## Las cuatro superficies, y cuál manda

| superficie | qué contiene | relación |
|---|---|---|
| `README.md` (este archivo) | índice completo, cohortes, comandos, licencia, contacto | **manda** |
| `index.html` · `en/index.html` | seis resúmenes bilingües con commit-pin y un enlace al Data Room | resume este archivo |
| Data Room (`platino-data-room`) | 23 snapshots JSON de imports: 10 con capa SCC canónica (`graph-input/1+scc/2`) y 13 adicionales sin capa SCC | es la evidencia pública; aquí solo se indexa |
| metadatos del repo y del perfil | descripción, topics, `homepageUrl`, licencia, «Start here» | pendiente, ver [En progreso](#en-progreso) |

## Índice de auditorías publicadas con datos

Cinco resultados de análisis de grafo, reproducibles desde sus snapshots JSON fijados a commit.
Los 23 snapshots de imports están en el release público
[`arch-index-20261029-batch2`](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2): diez llevan la capa SCC canónica (`graph-input/1+scc/2`) y trece adicionales publican imports sin resultados SCC. El 29-oct-2026 los diez primeros recibieron la capa SCC, así que esos diez activos cambiaron de tamaño y de SHA-256 respecto de la primera carga.

| repositorio | commit-pin | módulos | aristas internas | SCC cíclicas | tamaños | sin expansión de `__init__` | activo |
|---|---|---|---|---|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain/commit/facf2788ae1f60c62f2397d15698237c405a5f05) | `facf2788ae1f60c62f2397d15698237c405a5f05` | 40 | 131 | 2 | 19, 3 | 0 | [`public_graph_langchain_facf2788.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_langchain_facf2788.json) |
| [huggingface/transformers](https://github.com/huggingface/transformers/commit/95bafdcccfffe17ec383999fc39273867b11385e) | `95bafdcccfffe17ec383999fc39273867b11385e` | 3139 | 26078 | 8 | 176, 26, 5, 3, 2, 2, 2, 2 | 6 | [`public_graph_transformers_95bafdcc.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_transformers_95bafdcc.json) |
| [vllm-project/vllm](https://github.com/vllm-project/vllm/commit/7e3e3f6ab652550fdefecd8e9823394fd8e51950) | `7e3e3f6ab652550fdefecd8e9823394fd8e51950` | 3003 | 34061 | 23 | 1648, 25, 18, 12, 12, 10, 8, 8, 7 ×5, 4, 3, 3, 3, 2 ×7 | 8 | [`public_graph_vllm_7e3e3f6a.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_vllm_7e3e3f6a.json) |
| [bentoml/BentoML](https://github.com/bentoml/BentoML/commit/0aa1aea52b63b82100ff93675eff25f6428fb841) | `0aa1aea52b63b82100ff93675eff25f6428fb841` | 211 | 1287 | 5 | 78, 4, 3, 3, 2 | 4 | [`public_graph_bentoml_0aa1aea5.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_bentoml_0aa1aea5.json) |
| [run-llama/llama_index](https://github.com/run-llama/llama_index/commit/619d74664e8404612038bc15a1a40c686037277c) | `619d74664e8404612038bc15a1a40c686037277c` | 480 | 4024 | 4 | 334, 3, 2, 2 | 4 | [`public_graph_llamaindex_619d7466.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_llamaindex_619d7466.json) |

### Capa SCC canónica · los diez assets

El 29-oct-2026 los diez assets del release recibieron el bloque `scc` (`graph-input/1+scc/2`, huella
`ARCH_GRAPH_SCC_LAYER_V1_20261029`): Tarjan iterativo y condensación de Kahn sobre el grafo de
imports de cada commit. Los conteos de esta tabla se extrajeron de los bytes publicados, no de un
reporte de terceros.

| repositorio | commit-pin | módulos | aristas | SCC | ciclos | **mayor SCC** | fan-in mayor | bytes | activo |
|---|---|---:|---:|---:|---:|---:|---|---:|---|
| [pytorch/pytorch](https://github.com/pytorch/pytorch/commit/611154b3f03d63acac16cac8e8deb53a4deaed80) | `611154b3` | 2,527 | 19,353 | 831 | 14 | **1,660** | `torch` (2,203) | 7,468,906 | [`public_graph_pytorch_611154b3.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_pytorch_611154b3.json) |
| [vllm-project/vllm](https://github.com/vllm-project/vllm/commit/7e3e3f6ab652550fdefecd8e9823394fd8e51950) | `7e3e3f6a` | 3,003 | 34,061 | 1,225 | 23 | **1,648** | `vllm` (2,505) | 9,970,465 | [`public_graph_vllm_7e3e3f6a.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_vllm_7e3e3f6a.json) |
| [ray-project/ray](https://github.com/ray-project/ray/commit/096fce7ccc6a51984e6dec9d527f85f6eeae2705) | `096fce7c` | 4,108 | 35,426 | 2,787 | 23 | **960** | `ray` (3,610) | 10,975,888 | [`public_graph_ray_096fce7c.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_ray_096fce7c.json) |
| [apache/airflow](https://github.com/apache/airflow/commit/37b6b04e7233ec47c193915d6cff04dac742d5fd) | `37b6b04e` | 769 | 5,296 | 404 | 2 | **363** | `airflow` (535) | 2,171,655 | [`public_graph_airflow_37b6b04e.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_airflow_37b6b04e.json) |
| [run-llama/llama_index](https://github.com/run-llama/llama_index/commit/619d74664e8404612038bc15a1a40c686037277c) | `619d7466` | 480 | 4,024 | 143 | 4 | **334** | `llama_index.core` (395) | 1,219,946 | [`public_graph_llamaindex_619d7466.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_llamaindex_619d7466.json) |
| [huggingface/transformers](https://github.com/huggingface/transformers/commit/95bafdcccfffe17ec383999fc39273867b11385e) | `95bafdcc` | 3,139 | 26,078 | 2,929 | 8 | **176** | `transformers` (3,103) | 8,883,386 | [`public_graph_transformers_95bafdcc.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_transformers_95bafdcc.json) |
| [bentoml/BentoML](https://github.com/bentoml/BentoML/commit/0aa1aea52b63b82100ff93675eff25f6428fb841) | `0aa1aea5` | 211 | 1,287 | 126 | 5 | **78** | `bentoml` (159) | 563,547 | [`public_graph_bentoml_0aa1aea5.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_bentoml_0aa1aea5.json) |
| [huggingface/huggingface_hub](https://github.com/huggingface/huggingface_hub/commit/1725fefe88119095d3d01a384b68dc85a5e58270) | `1725fefe` | 182 | 996 | 117 | 4 | **35** | `huggingface_hub` (158) | 559,997 | [`public_graph_huggingface_hub_1725fefe.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_huggingface_hub_1725fefe.json) |
| [stripe/stripe-python](https://github.com/stripe/stripe-python/commit/b01f7c15196e729171fedb80a79b63146f3825ab) | `b01f7c15` | 1,651 | 5,130 | 1,619 | 1 | **33** | `stripe` (1,400) | 4,301,946 | [`public_graph_stripe_b01f7c15.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_stripe_b01f7c15.json) |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain/commit/facf2788ae1f60c62f2397d15698237c405a5f05) | `facf2788` | 40 | 131 | 20 | 2 | **19** | `langchain` (25) | 143,450 | [`public_graph_langchain_facf2788.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_langchain_facf2788.json) |
| **los diez** | — | **16,110** | **131,782** | **10,201** | **86** | **1,660** | `ray` (3,610) | **46,259,186** | 10 assets |

«Mayor SCC» es el tamaño, en módulos, de la componente fuertemente conexa más grande de cada grafo.
Los ciclos son las SCC con más de un módulo o con un auto-lazo: 86 en total, contra 10,201
componentes contadas. Ningún grafo es acíclico, y la proporción de módulos dentro de ciclos separa
los repositorios mejor que el conteo absoluto: `pytorch` mete el 67,7 % (1,710 de 2,527) y `vllm` el
60,0 % (1,801 de 3,003), mientras `langchain` no tiene ninguno expuesto (0 de 40).

<!-- HUELLA-LA-AUDITORA-SCC-20261029 -->

### Snapshots AST publicados · release `arch-index-20261029-batch2`

Estos cinco snapshots pertenecen a la cohorte inicial de diez y usan `ingesta_ast/v2`; todos tienen la capa SCC canónica listada arriba, aunque solo cinco incluyen sensibilidad al método. Sus registros, tamaños y commit-pins se verificaron en los assets del release.

| repositorio | commit-pin | esquema | registros `imports` | bytes | snapshot publicado |
|---|---|---|---:|---:|---|
| [stripe/stripe-python](https://github.com/stripe/stripe-python/commit/b01f7c15196e729171fedb80a79b63146f3825ab) | `b01f7c15196e729171fedb80a79b63146f3825ab` | `ingesta_ast/v2` | 21,137 | 4,301,946 | [`public_graph_stripe_b01f7c15.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_stripe_b01f7c15.json) |
| [ray-project/ray](https://github.com/ray-project/ray/commit/096fce7ccc6a51984e6dec9d527f85f6eeae2705) | `096fce7ccc6a51984e6dec9d527f85f6eeae2705` | `ingesta_ast/v2` | 58,928 | 10,975,888 | [`public_graph_ray_096fce7c.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_ray_096fce7c.json) |
| [huggingface/huggingface_hub](https://github.com/huggingface/huggingface_hub/commit/1725fefe88119095d3d01a384b68dc85a5e58270) | `1725fefe88119095d3d01a384b68dc85a5e58270` | `ingesta_ast/v2` | 3,496 | 559,997 | [`public_graph_huggingface_hub_1725fefe.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_huggingface_hub_1725fefe.json) |
| [apache/airflow](https://github.com/apache/airflow/commit/37b6b04e7233ec47c193915d6cff04dac742d5fd) | `37b6b04e7233ec47c193915d6cff04dac742d5fd` | `ingesta_ast/v2` | 11,651 | 2,171,655 | [`public_graph_airflow_37b6b04e.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_airflow_37b6b04e.json) |
| [pytorch/pytorch](https://github.com/pytorch/pytorch/commit/611154b3f03d63acac16cac8e8deb53a4deaed80) | `611154b3f03d63acac16cac8e8deb53a4deaed80` | `ingesta_ast/v2` | 42,083 | 7,468,906 | [`public_graph_pytorch_611154b3.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_pytorch_611154b3.json) |

### Trece snapshots adicionales · imports AST sin capa SCC

Estos activos amplían el Data Room de diez a 23 snapshots. Son instantáneas de imports (`ingesta_ast/v2`), no resultados SCC; sus cifras no amplían la cohorte SCC ni sus comparaciones.

| repositorio | commit-pin | archivos Python | registros `imports` | bytes | snapshot publicado |
|---|---|---:|---:|---:|---|
| [apache/superset](https://github.com/apache/superset/commit/22f768c3a55a508d09aef90798a1a7cfff001a31) | `22f768c3a55a508d09aef90798a1a7cfff001a31` | 3,070 | 45,145 | 8,624,859 | [`ingesta_ast_v2_apache_superset_22f768c3a55a.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_apache_superset_22f768c3a55a.json) |
| [celery/celery](https://github.com/celery/celery/commit/2ef8265b0a1dd977abdbcb087d3208b6575842c1) | `2ef8265b0a1dd977abdbcb087d3208b6575842c1` | 450 | 5,041 | 814,798 | [`ingesta_ast_v2_celery_celery_2ef8265b0a1d.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_celery_celery_2ef8265b0a1d.json) |
| [gradio-app/gradio](https://github.com/gradio-app/gradio/commit/211e8027c74e24429ddf91949c6371cbe69aee09) | `211e8027c74e24429ddf91949c6371cbe69aee09` | 784 | 5,466 | 904,303 | [`ingesta_ast_v2_gradio-app_gradio_211e8027c74e.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_gradio-app_gradio_211e8027c74e.json) |
| [matplotlib/matplotlib](https://github.com/matplotlib/matplotlib/commit/f318e28550a32e7a1b086303d6d2507a5a8585bf) | `f318e28550a32e7a1b086303d6d2507a5a8585bf` | 914 | 6,165 | 1,124,543 | [`ingesta_ast_v2_matplotlib_matplotlib_f318e28550a3.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_matplotlib_matplotlib_f318e28550a3.json) |
| [mlflow/mlflow](https://github.com/mlflow/mlflow/commit/cd1597e989e8667dad4603b9413fd4ea63b6237e) | `cd1597e989e8667dad4603b9413fd4ea63b6237e` | 2,882 | 41,301 | 7,507,603 | [`ingesta_ast_v2_mlflow_mlflow_cd1597e989e8.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_mlflow_mlflow_cd1597e989e8.json) |
| [numpy/numpy](https://github.com/numpy/numpy/commit/fe8c5053e5f5a0d7c7c6835a9f690b9a42124747) | `fe8c5053e5f5a0d7c7c6835a9f690b9a42124747` | 495 | 5,235 | 846,866 | [`ingesta_ast_v2_numpy_numpy_fe8c5053e5f5.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_numpy_numpy_fe8c5053e5f5.json) |
| [pandas-dev/pandas](https://github.com/pandas-dev/pandas/commit/0988929a21cdcc933b380871a622138eb18cc207) | `0988929a21cdcc933b380871a622138eb18cc207` | 1,546 | 17,509 | 2,987,025 | [`ingesta_ast_v2_pandas-dev_pandas_0988929a21cd.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_pandas-dev_pandas_0988929a21cd.json) |
| [pydantic/pydantic](https://github.com/pydantic/pydantic/commit/dd0c36a4be235522e34659ba372c59b43b55f33e) | `dd0c36a4be235522e34659ba372c59b43b55f33e` | 465 | 6,808 | 1,100,906 | [`ingesta_ast_v2_pydantic_pydantic_dd0c36a4be23.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_pydantic_pydantic_dd0c36a4be23.json) |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest/commit/a7b2446ee41a7298d3a0bc22c52f3b8bacae1566) | `a7b2446ee41a7298d3a0bc22c52f3b8bacae1566` | 274 | 3,278 | 523,722 | [`ingesta_ast_v2_pytest-dev_pytest_a7b2446ee41a.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_pytest-dev_pytest_a7b2446ee41a.json) |
| [python-poetry/poetry](https://github.com/python-poetry/poetry/commit/d59ff3b47c5d70b5e4934db874e94ea78b98feb8) | `d59ff3b47c5d70b5e4934db874e94ea78b98feb8` | 451 | 4,341 | 776,354 | [`ingesta_ast_v2_python-poetry_poetry_d59ff3b47c5d.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_python-poetry_poetry_d59ff3b47c5d.json) |
| [saleor/saleor](https://github.com/saleor/saleor/commit/cc4aea76e397b1dead74363c266c579ae808770f) | `cc4aea76e397b1dead74363c266c579ae808770f` | 4,371 | 36,543 | 7,340,685 | [`ingesta_ast_v2_saleor_saleor_cc4aea76e397.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_saleor_saleor_cc4aea76e397.json) |
| [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn/commit/d685424bec8f8585d8017c1aab1db7535d3fa03d) | `d685424bec8f8585d8017c1aab1db7535d3fa03d` | 1,033 | 14,780 | 2,662,667 | [`ingesta_ast_v2_scikit-learn_scikit-learn_d685424bec8f.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_scikit-learn_scikit-learn_d685424bec8f.json) |
| [wagtail/wagtail](https://github.com/wagtail/wagtail/commit/49c8767eab954e5e027c806c4833398b1aa297a8) | `49c8767eab954e5e027c806c4833398b1aa297a8` | 1,338 | 11,082 | 2,061,453 | [`ingesta_ast_v2_wagtail_wagtail_49c8767eab95.json`](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/ingesta_ast_v2_wagtail_wagtail_49c8767eab95.json) |

<!-- HUELLA-LA-AUDITORA-23-README-20261029 -->

`apache/airflow` y `pytorch/pytorch` entraron al Data Room como checkpoints de ingesta; la capa SCC
se calculó después sobre esos mismos commits, y sus conteos viven en la tabla canónica de arriba.
`pytorch/pytorch` aparece además en la tabla de auditorías en
prosa con otro commit (`210bb7ca`), otro método y otro hallazgo.

<!-- HUELLA-LA-AUDITORA-COHORTE-20261029 -->

<!-- HUELLA-LA-AUDITORA-8-PUBLICADOS-20261029 -->

<!-- HUELLA-LA-AUDITORA-10-PUBLICADOS-20261029 -->

Los cinco resultados `graph_sensitivity_*.json` declaran `source_bytes_verified: false`: los bytes
fuente no se re-verificaron contra el checkout al proyectarlos. Los cinco snapshots AST de la cohorte
inicial publican imports y la capa SCC canónica; los trece snapshots añadidos al ampliar el Data Room
son solo de imports y no publican métricas SCC. Los `graph_sensitivity_*` siguen siendo otra medición,
con su propio método y su propio límite declarado. vLLM está incluido arriba, entre los cinco grafos.

Release anterior: [`arch-index-20261028-v1`](https://github.com/alexisromtz-lab/la-auditora/releases/tag/arch-index-20261028-v1)
(28-oct-2026, seis activos: los mismos cinco grafos sin la capa de sensibilidad).

## Valor: el grafo frente al código que mapea

El grafo AST de PyTorch pesa 7,47 MB y mapea 2.527 archivos `.py` del paquete `torch`. Los diez
grafos del Data Room pesan 46,26 MB. Frente a los archivos `.py` que indexan, el ahorro medido es
del 78,49 % en los ocho repositorios cuyo código se pesó archivo por archivo, y del 79,93 % sumando
los dos restantes con los denominadores que declara la medición externa.

| repositorio | `.py` mapeados | grafo | ahorro | denominador |
|---|---:|---:|---:|---|
| pytorch/pytorch | 53,82 MB | 7,47 MB | 86,12 % | declarado |
| huggingface/transformers | 56,09 MB | 8,88 MB | 84,16 % | medido |
| ray-project/ray | 48,58 MB | 10,98 MB | 77,41 % | medido |
| vllm-project/vllm | 44,12 MB | 9,97 MB | 77,40 % | medido |
| stripe/stripe-python | 13,19 MB | 4,30 MB | 67,39 % | medido |
| apache/airflow | 6,42 MB | 2,17 MB | 66,16 % | declarado |
| huggingface/huggingface_hub | 3,27 MB | 0,56 MB | 82,86 % | medido |
| run-llama/llama_index | 2,67 MB | 1,22 MB | 54,30 % | medido |
| bentoml/BentoML | 1,69 MB | 0,56 MB | 66,66 % | medido |
| langchain-ai/langchain | 0,65 MB | 0,14 MB | 78,06 % | medido |
| **los diez** | **230,50 MB** | **46,26 MB** | **79,93 %** | mixto |

Cómo se mide, para que se pueda refutar:

- **Numerador**: bytes de cada asset publicado, `stat -f%z`. Es el objeto que cualquiera descarga.
- **Denominador medido**: suma de bytes de las rutas que el propio snapshot lista en `archivos[].rel`, resueltas contra el checkout del repositorio. En los ocho medidos se resolvieron todas las entradas (211/211, 182/182, 3,139/3,139, 40/40, 480/480, 4,108/4,108, 1,651/1,651, 3,003/3,003).
- **Denominador declarado**: `apache/airflow` (6,42 MB) y `pytorch/pytorch` (53,82 MB, por diferencia sobre el total de 230,5 MB) no tienen checkout en esta máquina. Se publican como supuesto; un clon de cada uno los vuelve medibles.
- Aquí se compara el **peso del índice frente a los archivos `.py` que mapea**. La versión anterior de este párrafo —98,81 % frente a un índice vectorial de 614,4 MB— era una proyección (100.000 fragmentos × 1.536 dimensiones × 4 bytes) y se retiró por teórica.

Con los tamaños previos a la capa SCC (45,668,259 B) el mismo cociente da 80,19 %, que es la cifra
que circuló; añadir la capa mueve el total a 46,259,186 B y el ahorro a 79,93 %.

<!-- HUELLA-LA-AUDITORA-VALOR-20261029 -->
<!-- HUELLA-LA-AUDITORA-VALOR-EMPIRICO-20261029 -->

## Auditorías publicadas en el sitio

Seis resúmenes en prosa con commit-pin, verificables en la página. **Ninguna de estas seis filas
tiene snapshot en el Data Room para su commit-pin**: son otra cohorte, medida con otro método. Dos
repositorios de esta tabla sí tienen snapshot en el Data Room, pero **en otro commit y para otro
hallazgo** (ver la nota de cohortes al final de la tabla).

| repositorio | commit-pin | hallazgo |
|---|---|---|
| [pytorch/pytorch](https://github.com/pytorch/pytorch/commit/210bb7ca5c4e08c40513c389c14b1adbf4a82f8c) | `210bb7ca5c4e08c40513c389c14b1adbf4a82f8c` | 45 archivos de tests sin camino de ejecución en el CI (alcanzabilidad estática) |
| [django/django](https://github.com/django/django/commit/641e9368105e07237e4d09cf951f3038cde4d973) | `641e9368105e07237e4d09cf951f3038cde4d973` | 3 ciclos eager en backends de base de datos, dependientes del orden de carga |
| [tenstorrent/tt-metal #59955](https://github.com/tenstorrent/tt-metal/pull/59955) | rotura `7d399796b4770ca95e15c7877e157872dc87ba82` · reparación `78957cf011ab40db8e4f6283a61ce4839c51b896` | un job verde ocultó 12 de 13 nodos afectados tras abortar con `-x` |
| [huggingface/transformers](https://github.com/huggingface/transformers/commit/b4a5b4b2c652615ef0c4dfa8adabad1756a6ec3f) | `b4a5b4b2c652615ef0c4dfa8adabad1756a6ec3f` | resultado nulo: 0 ciclos eager, 0 de 8 rutas del PR intersectadas |
| [vllm-project/vllm-omni](https://github.com/vllm-project/vllm-omni/commit/9573acc90213cb473c30d64115ab0e1dd1a32d9a) | `9573acc90213cb473c30d64115ab0e1dd1a32d9a` | 0 ciclos eager en `vllm_omni/platforms/`; cinco componentes con ciclos diferidos |
| [pallets/flask](https://github.com/pallets/flask/commit/d086db856be187255b8ec61ef409357393020f32) | `d086db856be187255b8ec61ef409357393020f32` | 1 SCC mixta de 18 módulos, 0 ciclos eager |

**Las dos cohortes no coinciden, y se declara a propósito.** Dos repositorios aparecen en las dos
listas, y **en commits distintos**:

| repositorio | commit en el sitio | commit en el Data Room |
|---|---|---|
| `huggingface/transformers` | `b4a5b4b2` (0 ciclos eager) | `95bafdcc` (8 SCC) |
| `pytorch/pytorch` | `210bb7ca` (45 archivos de tests sin ruta en CI) | `611154b3` (ingesta AST, 42,083 imports) |

Quien siga el commit-pin de la página hasta el Data Room encontrará otro objeto y otra medida. Eso
no es un fallo de medición: son dos productos con el mismo nombre genérico, y por eso están en dos
tablas separadas.

## En progreso

La capa SCC está publicada para los diez snapshots de la cohorte inicial; los trece añadidos después
son snapshots de imports sin SCC y no amplían esa muestra. La sensibilidad al método —con y sin
expansión de `__init__`— existe solo para cinco de los diez activos SCC; los otros cinco publican un
único número, sin contraste contra su propio defecto declarado.

## Cómo se reproduce

Desde un directorio vacío, con el release a la vista:

```bash
gh release download arch-index-20261029-batch2 \
  --repo alexisromtz-lab/platino-data-room \
  --pattern 'public_graph_langchain_*.json'
gh release download arch-index-20261028-v2 \
  --repo alexisromtz-lab/la-auditora \
  --pattern 'calculate_arch_index.py' \
  --pattern 'graph_sensitivity_langchain.json'

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
- **`source_bytes_verified: false`** en los cinco resultados de `graph_sensitivity_*.json`; los trece snapshots añadidos al Data Room después de la cohorte SCC no publican métricas SCC.

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
<!-- HUELLA-README-HF-PENDIENTE-20261029 -->
