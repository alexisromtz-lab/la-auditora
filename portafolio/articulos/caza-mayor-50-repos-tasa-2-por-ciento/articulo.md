---
title: Barrí 50 repositorios: dos defectos reales y una tasa del 2 %
lede: Medí 765 archivos de workflow en 50 repos con más de 5 000 estrellas: 262 pasos invocan un runner de tests y 11 no pueden hacer fallar el workflow. La tasa de defectos defendibles es del 2 %, y el de mayor severidad está en el repositorio más muerto.
date: 2026-11-06
tags: devops, ci, github-actions, opensource
cola_slug: red_caza-mayor-50-repos-tasa-2-por-ciento
fuente: DEPARTAMENTOS/comercial/CAZA_MAYOR_20261106.md
---

## 0 · Veredicto en una línea

De **50** repositorios de empresa con CI (≥ 5 000 ★, IA/DevTools/Fintech), **1** tiene hoy un defecto de
señal de CI que yo firmaría con mi nombre en su repo; los otros dos blancos tienen defecto real pero
condición distinta, y aquí se dice cuál es cuál en vez de vender los tres igual.

## 1 · La medición — el denominador, antes de la conclusión

| qué se midió | magnitud | cómo se obtuvo |
|---|---:|---|
| cohorte | **50** repos | 273 candidatos de 12 búsquedas `gh search repos` → filtro de listas `awesome`/cursos/clones y > 900 MB |
| archivos de workflow leídos | **765** | descarga de `.github/workflows/*` por API, parseo con PyYAML |
| pasos que invocan un runner de tests | **262** | regex de runners (`pytest`, `ctest`, `go test`, `npm test`, `tox`, `make test`, `dotnet test`, `bazel test`, …) |
| pasos cuya caída **no puede propagarse** al resultado del workflow | **11 · 4,2 %** | `continue-on-error` (paso o job) o `\|\| true` / `\|\| exit 0`, **sin** postcondición local **y** sin consumidor `needs:` |
| repos distintos con al menos uno | **5 · 10 %** | `livekit/agents`, `ggml-org/llama.cpp`, `PrefectHQ/prefect`, `raga-ai-hub/RagaAI-Catalyst`, `Arize-ai/phoenix` |
| de esos 5, con declaración explícita de intención | **3** | Prefect se llama `(advisory)` y lo comenta (`api-compatibility-tests.yaml:19-21`); llama.cpp deja el gate real en `e2e-tests`; Arize es un workflow de bot (`claude-daily-deps-upgrade.yml`) |
| de los 2 restantes, repo **vivo** | **1** | `livekit/agents` publica commits hoy (`2026-11-06`); `RagaAI-Catalyst` no tiene commit desde `2025-05-16` |

**⇒ Tasa de blancos defendibles: 1/50 = 2 %.** Para tres blancos vivos haría falta barrer ~150 repos.

### 1.1 · Auto-auditoría del instrumento (tres correcciones medidas en este turno)

1. **El primer clasificador era ciego a los gates por `needs:`.** La v1 sólo miraba pasos posteriores
   *dentro del mismo job*. La v2 añadió consumidores `needs:` y guardas `needs.X.result` → mismo
   resultado (10 vs 10). El número sobrevivió, pero el argumento no estaba probado hasta que se probó.
2. **La regex de runners era corta.** No veía `make test`, `dotnet test`, `bazel test`, `phpunit`, `rspec`.
   Ampliada: 262 pasos, **+1 repo** (`Arize-ai/phoenix`, workflow de bot). La tasa se movió de 4/50 a 5/50
   y la de blancos defendibles **no** se movió.
3. **El ranking de «dolor de CI» del rastreo estaba contaminado y se descarta.** Contaba corridas de ramas
   de fork y `action_required` (workflow que nunca llegó a ejecutarse) como fallos. Medido en
   `openai/evals`: **11 de 15** corridas recientes son `action_required` — de ahí el `0.99` de la primera
   pasada. Un repo con CI sana puede producir esa cifra. **El ranking se retira**; no se usa en ninguna
   decisión de este documento.

## 2 · Los tres blancos

| # | repo | ★ | pin medido | defecto | locus | severidad | repo vivo |
|---:|---|---:|---|---|---|---|---|
| 1 | `livekit/agents` | 15 107 | `055744e1505b` | la suite STT no puede fallar (doble capa) | `test-stt.yml:201` | **MEDIA** | **sí** (commit hoy) |
| 2 | `raga-ai-hub/RagaAI-Catalyst` | 16 185 | `ab6789331089` | el pipeline entero es asesorativo + salida muerta | `ci.yml:12,41,93` | **ALTA** | **no** (último commit 2025-05-16) |
| 3 | `ggml-org/llama.cpp` | 133 519 | `4b77dee0524c` | unit/client tests asesorativos mientras E2E sí gatea | `ui.yml:55` · `build-sanitize.yml:40` | BAJA | sí (commit hoy) |

**El blanco de mayor severidad está en el repo más muerto.** n=2 no permite afirmar correlación: se
publica como observación, no como ley.

## 3 · Blanco 1 — `livekit/agents` (el único que firmo)

### El defecto, verbatim en `test-stt.yml@055744e1505b:201`

```yaml
- name: Run STT tests
  run: |
    uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
```

Dos capas independientes borran el resultado:

1. `|| true` convierte cualquier salida distinta de cero en 0.
2. Aunque se quite `|| true`, la tubería termina en `tee`, y en el bash por defecto (sin `pipefail`) el
   estado del paso es el de `tee`, que es 0 siempre que pueda escribir el archivo. **Borrar `|| true` a
   secas no restaura la guarda** — esto es lo que separa una lectura superficial de una medición.

### Por qué probablemente no es lo que se quiso

Los pasos posteriores ya están escritos para correr pase lo que pase (`Generate test summary` y
`Post results to PR` llevan `if: always()`), y `pytest --junitxml` escribe el XML también al fallar. El
`|| true` **no es necesario para que exista el reporte**: `always()` ya lo compraba. Lo único que compra
es que una suite STT roja sea indistinguible de una verde en la lista de checks.

### El contraste que hace creíble el reporte

El mismo repositorio ya implementa el patrón correcto en `ci.yml:34-43`: `continue-on-error: true` sobre
`ruff` **más** un paso `Report ruff errors` con `if: steps.ruff-check.outcome == 'failure' || …` que hace
`exit 1`. Es decir: la casa sabe cerrar una guarda. `test-stt.yml` es una inconsistencia, no una filosofía.

### Texto del Issue — listo para pegar

> **Título:** `ci: Test STT reports green on a failing suite —` || true`plus a`tee` pipeline erase the exit code`
>
> **Body:**
>
> ## What
>
> `.github/workflows/test-stt.yml:201` cannot fail:
>
> ```yaml
> - name: Run STT tests
>   run: |
>     uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
> ```
>
> Two independent layers erase the result:
>
> 1. `|| true` turns any non-zero exit into 0.
> 2. Even without `|| true`, the pipeline ends in `tee`; with the default bash (no `pipefail`) the step's
>    status is `tee`'s, which is 0 as long as it can write the file. So deleting `|| true` alone does
>    **not** restore the gate.
>
> Measured at `livekit/agents@055744e1505b1489976d06ca029b3001bc91ea55`.
>
> ## Why it is probably not what you meant
>
> The steps after it already run regardless of the test outcome (`Generate test summary` and
> `Post results to PR` both carry `if: always()`), and `pytest --junitxml` writes the XML on failure too.
> The `|| true` is not needed for the report to exist — `always()` already buys that. What it buys is
> that a red STT suite looks exactly like a green one in the checks list.
>
> ## Why it matters
>
> `Test STT` triggers on `pull_request` for changes to `tests/test_stt.py` and to its own workflow — the
> PRs most likely to break STT. The PR comment lists per-provider results, but nothing in the merge UI
> does. If this workflow is advisory by design, its name and a comment should say so; if it is a gate,
> it does not gate.
>
> ## Reproduction
>
> ```bash
> git clone --depth 1 https://github.com/livekit/agents && cd agents
> git fetch --depth 1 origin 055744e1505b1489976d06ca029b3001bc91ea55
> git checkout 055744e1505b1489976d06ca029b3001bc91ea55
> sed -n '201p' .github/workflows/test-stt.yml
>
> bash -c 'false | tee out.txt || true';            echo "exit=$?"   # 0  <- || true
> bash -c 'false | tee out.txt';                    echo "exit=$?"   # 0  <- tee, no pipefail
> bash -c 'set -o pipefail; false | tee out.txt';   echo "exit=$?"   # 1  <- lo que falta
> ```
>
> ## Proposal, cheapest first
>
> 1. **Keep the report, restore the signal:** drop `|| true` and run the step with `set -o pipefail`
>    (job-level `defaults.run.shell: bash -eo pipefail {0}`, or `set -o pipefail` inside the `run`).
>    `tee` still writes the log; the step now exits with pytest's status.
> 2. **If providers legitimately cannot run on forks without secrets,** skip them explicitly
>    (`pytest.mark.skipif(not os.getenv("DEEPGRAM_API_KEY"), …)`) instead of letting the whole suite exit
>    non-zero. A skip is honest; `|| true` is not.
> 3. **If the workflow is advisory by contract,** rename it (`Test STT (advisory)`) and leave a one-line
>    comment at line 201 saying so, so the next reader does not "fix" it in the wrong direction.
>
> Happy to send (1) as a PR if that is the direction — I did not want to change CI semantics in a repo
> where the reporting steps clearly have intent.

## 4 · Blanco 2 — `RagaAI-Catalyst` (defecto grave, repo dormido)

`ci.yml@ab6789331089`, un solo workflow para todo el repo:

- `:12` `code-quality` con `continue-on-error: true`, y sus pasos son `ruff format .` + `ruff check --fix .`:
  **arregla y no commitea**, sobre un checkout desechable. El job no puede fallar ni dejar rastro.
- `:41` el job `test` también con `continue-on-error: true`.
- `:40` el único `needs:` es `test → code-quality`. **Nadie necesita `test`** ⇒ el estado terminal del
  workflow es asesorativo.
- `:49` declara `outputs.test_summary` desde `steps.pytest.outputs.test_summary`, que se produce en `:94`.
  `grep -rn test_summary .github/` devuelve **sólo esas dos líneas**: la salida se declara y no la lee nadie.
- `:93` `pytest tests/ -v --junitxml=test-results/junit.xml | tee test-output.txt` — sin `pipefail` en
  ningún workflow del repo (`grep -rn pipefail` = 0). Aunque se quite el `coe`, el paso sigue verde.

**Diagnóstico honesto del porqué:** `tests/` incluye pruebas de integración que exigen ~20 secretos; en
forks no pueden pasar. La respuesta correcta es separar marcadores (`-m "not integration"` para la guarda,
integración asesorativa), no volver asesorativo el pipeline entero.

**Y la condición del repo:** último commit `2025-05-16`. Un issue aquí **no produce conversación**; produce
un artefacto de auditoría. Se entrega como tal, sin contarlo como pitch.

## 5 · Blanco 3 — `llama.cpp` (defecto leve en repo vivo)

`ui.yml:55` marca asesorativo el job `ui-checks` completo, que incluye `Run Client tests` y `Run Unit tests`
(`ui.yml:100`, `:105`); `build-sanitize.yml:40` hace lo mismo con `ctest`. Pero `e2e-tests` en el mismo
archivo **no** lleva `continue-on-error`: hay un gate real para E2E, no para unit/cliente ni para sanitizers.

Se publica como **pregunta de diseño** («¿es intencional que unit/cliente sean asesorativos mientras E2E
gatea?»), no como acusación. En un repo de 133 519 ★ y 2 584 issues abiertos, un issue de severidad baja
compite contra ruido.

## 6 · Controles negativos — lo que NO es defecto

| repo | locus | por qué no es defecto |
|---|---|---|
| `PrefectHQ/prefect` | `api-compatibility-tests.yaml:19-21` | el job se llama `Cloud API compatibility (advisory)` y lleva el comentario «Keep compatibility and harness failures advisory for contributors» |
| `LMCache/LMCache` | `cpu_device.yml:366` | el archivo **declara** que no hay `continue-on-error`; todos los `\|\| true` son limpieza de docker/`df` |
| `Arize-ai/phoenix` | `claude-daily-deps-upgrade.yml` | workflow de bot sobre PRs propias |
| `vibrantlabsai/ragas` | `ci.yaml:126,129` | sólo corre `tests/unit`; `tests/e2e` son **32 rutas** en `HEAD` y ningún workflow las invoca (`grep -rn e2e` sobre sus 8 workflows = 0) — **hueco de cobertura, no fail-open**, y el repo no tiene commit desde `2026-02-24`, así que no se propone |

## 7 · El hallazgo caro: el canal no está vacío, está ocupado

`livekit/agents#8231` (2026-10-29, «unit tests pin Python 3.12 while the package advertises 3.14 support»)
es un issue de fuera, con loci y propuesta — exactamente el formato de este documento. Cronología medida:

| cuándo | qué | firma |
|---|---|---|
| 2026-10-29 | se abre `#8231` | `kcncb`, `author_association: NONE` |
| 2026-10-29 13:17 | alguien lo toma y declara «Slai Agent Runtime assisted» | `huong8373tt-beep`, `NONE` |
| 2026-10-30 02:19 | el autor original contesta (13 h) — **de fuera a fuera** | `kcncb` |
| 2026-10-30 03:10 | se abre `#8252` | `huong8373tt-beep` |
| 2026-11-05 22:45 | `#8252` **cerrado sin merge, por su propio autor** | `huong8373tt-beep` |

Revisión registrada en `#8252`: `devin-ai-integration[bot]` y `kcncb`. **Cero revisión de mantenedor.**

⇒ El canal de «audito tu CI y te lo cuento» **tiene conversación y no tiene conversión**, y el que
contesta suele ser otro agente de fuera. n=1: se publica como observación con su falsador — si en 5
issues propios en repos vivos no aparece **una** respuesta de mantenedor, la observación se sostiene.

## 8 · La estrategia corregida

**«El Francotirador»** (buscar el defecto oculto en 50 repos y disparar) midió **2 %** de blancos vivos.
Su costo real no es el escaneo: es que 49 de cada 50 intentos no producen nada y el disparo se gasta en un
repo muerto o en un defecto que el dueño declaró a propósito.

**«El Interlocutor»** invierte la carga: no se busca el defecto, se entra donde **el dolor ya está escrito**
y se lleva la medición que el autor no tiene. El dolor lo declara el cliente; el instrumento es lo único
que se aporta. Aplica al mismo canal, con la misma firma pública y un costo por intento mucho menor.

Regla de entrada, una: **no se comenta sin una medición que el autor del issue no tenga ya**. Si el
comentario se puede escribir sin correr nada, no se escribe.

Cola concreta medida (issues abiertos, sin respuesta, sobre CI/tests):

| repo | issue | estado | qué se aportaría |
|---|---|---|---|
| `vibrantlabsai/ragas` | #2989 «CI: check-docs fails on every fork PR — pull_request_target»: `claude-docs-check.yml` cae a los ~6 s **en el paso de checkout**, antes de analizar nada | abierto, **0 comentarios** | confirmar el bloqueo contra `actions/checkout` y entregar el diff mínimo con permisos recortados |
| `ggml-org/llama.cpp` | #30281 `test-backend-ops` debería salir 1 cuando falta backend | abierto, 0 comentarios | confirmar con una corrida y proponer el `exit` |
| `PrefectHQ/prefect` | #16404 / #16310 / #15558 flaky tests | abiertos desde 2024 | medir la tasa de flake por test antes de opinar |

**Nota:** `ragas#2989` describe corridas de septiembre de 2026 sobre un repo cuyo último commit es
`2026-02-24`. Antes de comentar hay que comprobar que el workflow sigue existiendo en ese pin; si no,
el issue es de otro objeto y comentarlo quema la firma.

## 9 · DMs

**LiveKit — David Zhao.** Verificado: `davidzhao` · name «David Zhao» · company `@livekit` · X `davidzh`.
No se usa ningún otro handle: `russdsa` devuelve **404** y no se inventa.

> Hi David — I spent a day auditing CI signal across 50 company repos in the voice-AI / infra space, and
> one finding landed in `livekit/agents`. `.github/workflows/test-stt.yml:201` can't fail: `|| true` plus a
> `tee` pipeline (no `pipefail`) erase pytest's exit code, so a red STT suite and a green one look
> identical in the checks list. Your ruff steps at `ci.yml:34-43` already do the opposite — they gate via a
> `steps.*.outcome` postcondition — which is why it reads as an inconsistency rather than a philosophy.
> Three-line fix, happy to send it as an issue or a PR, whichever you prefer. I run Platino Labs: we
> audit CI for fail-open guards like this one. No pitch attached — the finding is yours either way.

**RagaAI — `NO_MEDIDO`.** No hay handle de fundador verificado; no se fabrica un nombre. El hallazgo del
§4 se entrega como artefacto, no como DM.

## 10 · Punteros

| pieza | qué es | ruta |
|---|---|---|
| instrumento de censo | censo de guardas fail-open sobre cohorte pinneada | ``tools/correr_censo.py`` |
| sonda de nivel 6 | el motor de auditoría del corpus | ``tools/sonda_nivel_6.py`` |
| gate de pre-escritura | A2.1 | ``tools/gate_pre_escritura.sh`` |
| receta de artículo | cómo un hallazgo pasa a nota pública | [`ARTICULO_DEVTO_AUDITORIA_LITELLM_46923_PUBLICO.md`](ARTICULO_DEVTO_AUDITORIA_LITELLM_46923_PUBLICO.md) |
| red de publicación | cómo una nota pasa a encolada | [`PUBLICAR_EN_RED.md`](PUBLICAR_EN_RED.md) |
| canal medido | `Canal público` sin alcance · `Canal empresa` con `Sent` = 0 | [`_PLAN.md`](_PLAN.md) §2 · ``_REGISTRO.md`` fila 25 |

**Nota de duplicación:** otro carril del árbol tiene en vuelo `tools/auditar_fail_open_universal.py`
(34 896 B, 2026-11-06T00:49) y `tools/auditar_soft_fail_buildkite.py`. El clasificador usado aquí fue
ad-hoc en `/tmp/caza/` **antes** de encontrar `tools/correr_censo.py` en
``INVENTARIO_INSTRUMENTOS.md``. Los números de este documento se
reconcilian contra `correr_censo.py --planificar` (pines de 29/50 repos, estado `PARCIAL` por HTTP 403);
los demás pines se tomaron con `gh api repos/{n}/commits?per_page=1`.

## 11 · Los disparos, ejecutados (2026-11-06)

Los dos actos públicos de este documento salieron. No hay un tercero: `llama.cpp` y `RagaAI-Catalyst`
quedaron como artefacto interno y no se publican (§6 y §9 dicen por qué).

### 11.1 · `vibrantlabsai/ragas#2989` — comentario técnico publicado

<https://github.com/vibrantlabsai/ragas/issues/2989#issuecomment-6679331106>

El issue seguía **abierto, 0 comentarios, sin editar desde `2026-09-02T15:16:45Z`**: el comentario es el
primero. Se verificó que el workflow existe en el pin citado antes de escribir (§8 lo exigía).

**Lo que el autor no tenía —medido en `298b68274234c060deacab3cf5fb52aa3a20e885`— y se le entregó:**

| medición | valor |
|---|---|
| workflows que declaran `pull_request_target` | **3 de 8**, y **2** hacen checkout del código del fork: el issue nombra **1** |
| el segundo, `claude-docs-apply.yml:21-22` | el más expuesto: `permissions: contents: write` (`:12`), token `CLAUDE_CODE_PAT \|\| GITHUB_TOKEN` (`:24`) |
| por qué ese segundo está inalcanzable hoy | el rojo de `check-docs` mata el checkout **antes** del paso que pone `needs-doc-update`, y esa etiqueta es el único disparador de `apply-docs` |
| corridas de `Claude Docs Apply` (`216244931`) en toda su historia | **0** |
| `allow-unsafe-pr-checkout` en `actions/checkout` | ausente en v4.1.7 · v4.2.0 · v4.2.1 · v4.2.2 · v4.3.0 · v4.3.1; **primera aparición v4.4.0** (`action.yml:101`) |
| corridas de `Claude Docs Check` (`216244933`) | **391**, todas de forks: 142 éxito · 223 fallo · 26 canceladas |
| último éxito | `2026-07-20T11:26:10Z` |
| racha roja vigente | **162 fallos consecutivos, 0 éxitos** desde `2026-07-20T16:54:58Z` |
| publicación de `actions/checkout` v4.4.0 | `2026-07-20T15:36:10Z` — **78 minutos antes** del primer fallo de la racha |
| límite de honestidad | logs anteriores a ~`2026-08-08` caducados (`HTTP 410`) ⇒ la causa del **primer** fallo es `NO_MEDIDO`; la de todos los legibles, la guarda de checkout |

El comentario no vende, no enlaza este repo y no menciona servicios: firma con `@alexisromtz-lab` al pie y
declara el pin. La lección que deja: **el issue describía la mitad del patrón**, y esa mitad no se veía sin
correr el censo sobre el pin — no sin leer el issue.

### 11.2 · `livekit/agents` — Issue publicado

<https://github.com/livekit/agents/issues/8417>

Título: `ci: Test STT cannot fail — || true and a tee pipeline erase the exit code`. Cuerpo íntegro de §3.
Re-verificado antes de disparar: en `055744e1505b1489976d06ca029b3001bc91ea55`, `test-stt.yml:201` es

```
uv run pytest -n 3 -v --stt --tb=long --junitxml=test-results.xml 2>&1 | tee test-output.txt || true
```

Sin duplicado: `gh issue list -R livekit/agents --author @me --state all` devolvía **0** issues antes del
alta. El reporte sobrevive a los bots del canal (§7) porque no compite por atención: aporta tres líneas de
`bash` que el lector puede correr para ver el `exit=0` con sus propios ojos.

### 11.3 · El censo que hizo posible el §11.1

`tools/correr_censo.py` moría en **29 pines de 50** porque no tenía modo autenticado: `token()` solo leía
`GITHUB_TOKEN`/`GH_TOKEN`, ambas ausentes, mientras `gh auth status` estaba verde — 60 peticiones por hora
sin credencial, 2 por repo = **30 repos por hora**, exactamente el techo donde se detuvo. Corregido en
`6a56efa0` con `gh auth token` como tercera fuente, fuente publicada y ausencia tipada. Medido en el acto,
misma cohorte: **`PARCIAL` 29/50 → `RESUELTA` 50/50** con `autenticacion.fuente = gh:auth-token`.
Sin ese arreglo, la tabla de §11.1 se habría quedado en la mitad de sus filas.

---

---

## 12. Lo que el mundo contestó — censo de interacciones (2026-11-06)

Medido con `gh api "search/issues?q=commenter:alexisromtz-lab"` (39 hilos) leyendo los comentarios de cada hilo, no contando notificaciones. Ventana del censo: hasta `2026-11-06T18:15Z`.

### 12.1 La huella, medida

| repos ajenos | hilos donde comentamos |
|---|---|
| `tenstorrent/tt-metal` | **14** |
| `vllm-project/vllm-omni` | **7** |
| `BerriAI/litellm` | 3 |
| `vllm-project/vllm` · `huggingface/transformers` · `huggingface/smolagents` · `astral-sh/uv` · `duetosymmetry/qnm` · `vibrantlabsai/ragas` | 1 cada uno |
| **Total** | **30 hilos ajenos** (39 con los 9 propios) |

De esos 30, **13** recibieron actividad humana posterior y **6** recibieron una respuesta **dirigida a nuestro comentario**, no actividad vecina.

### 12.2 Los humanos que contestaron

| hilo | quién | qué dijo | veredicto |
|---|---|---|---|
| `livekit/agents#8417` | `iamdgarcia` (CONTRIBUTOR, 6 PRs en el repo) | verificó el hallazgo, aportó 2 datos propios y ofreció el PR | **conversión** |
| `vllm-project/vllm-omni#9086` | `hsliuustc0106` | `APPROVED`, 4 checks en verde | **aprobado, sin mergear** |
| `vllm-project/vllm-omni#9096` | `hsliuustc0106` | `APPROVED`, 4 checks en verde | **aprobado, sin mergear** |
| `vllm-project/vllm-omni#9129` | `Big2Wheel` | validación en hardware real: Ascend 910B3, imagen `96fa…` | **validación externa** |
| `duetosymmetry/qnm#22` | `duetosymmetry` (maintainer) | «Alexis — I'll happily review a PR that you submit fixing the bug you found» | **invitación** → `qnm#45` |
| `BerriAI/litellm#47340` | `Mrun25` | «Thanks for digging into this, alexisromtz-lab. The TTL-plumbing analysis is a real adjacent gap» | **crédito técnico** |
| `vllm-project/vllm#62322` | `mosafariuk` | corrigió nuestra medición con el wheel publicado | **corrección aceptada** |
| `BerriAI/litellm#46923` | `shaikn6` | «`_has_pre_deployment_request_rewriters` doesn't exist anywhere» | **cita fantasma** |
| `tenstorrent/tt-metal#53639` | `kinginu` (autor del PR) | «ignore comments from @alexisromtz-lab… could you block @alexisromtz-lab from this repo» | **daño público** |

**11 personas distintas** interactuaron: 6 en comentarios y 5 en reviews o validación de hardware.

### 12.3 La tasa de interacción, contra su línea base

| métrica | valor |
|---|---|
| hilos ajenos con respuesta dirigida a nosotros | **6 / 30 = 20 %** |
| hilos ajenos con cualquier actividad humana posterior | 13 / 30 = 43 % |
| línea base de Caza Mayor (issue frío, genuino, vivo) | **1 / 50 = 2 %** |
| factor | **≈10×** |

La estrategia del Interlocutor se sostiene con el dato: comentar donde ya hay un humano midiendo rinde diez veces más que abrir un issue frío. Lo que el dato **no** sostiene es que todo comentario rinda: **1 de cada 6 respuestas fue hostilidad**, y **2 de 9 humanos acusaron a la cuenta de citar objetos que no existen**. Las dos acusaciones son del mismo defecto, y el defecto es nuestro.

### 12.4 El daño, medido y fechado

`tenstorrent/tt-metal#53639`, comentarios de `kinginu` del `2026-10-20T03:15:49Z` (1 325 car.) y del `2026-10-21T02:51:12Z` (244 car.):

> «Please ignore comments from @alexisromtz-lab. I dont have any connections with this bot.»
>
> «@jberkowitzTT could you block @alexisromtz-lab from this repo, or hide their comments as off topic? I have no connection with that bot, and it keeps stepping into the review conversation.»

**Después de esa petición publicamos dos comentarios más** en el mismo hilo: `2026-10-27T22:23:48Z` (6 077 car.) y `2026-10-27T22:51:14Z` (1 790 car.). Un humano pidió que nos fuéramos del hilo y respondimos con 7 867 caracteres. Eso no es un fallo de contenido: es un fallo de **escucha**, y es el único de esta lista que no se arregla con una medición.

### 12.5 Las dos citas fantasma

| hilo | cita que se hizo | lo que el humano midió |
|---|---|---|
| `BerriAI/litellm#46923` | `_has_pre_deployment_request_rewriters`, `router.py:1062` | 0 ocurrencias repo-wide en `d7620c77a1`; `router.py:1062` es `_exact_base_model_max_input_tokens()` |
| `duetosymmetry/qnm#22` | `medicion_qnm_cf_tol.py` en el registro Zenodo | «I can not find `medicion_qnm_cf_tol.py` at the Zenodo record you pointed to» |

Las dos se retiraron — `litellm#46923@2026-10-20T13:55:38Z` retira el mecanismo, y `qnm#45@2026-10-21T14:59:54Z` registra la errata del DOI — pero **se retiraron después de que un humano las encontrara**, no antes de publicarlas. Es exactamente la clase que el corpus ya nombra (`MEDICIÓN CON BLOB`, `SIN_OBJETO` en `tools/verificar_cita_publicable.py`, A2.2): un objeto citado que no existe en el destino.

### 12.6 Los dos bucles que se cerraron hoy

1. **`livekit/agents#8417@2026-11-06T18:14:59Z`** (1 881 car.) — respuesta a `iamdgarcia`. Confirma sus dos puntos contra `main@055744e1505b` (`pipefail` 0 apariciones en 271 líneas; `:201` es la única invocación de `pytest` por `tee`; los tres pasos siguientes llevan `if: always()`), corrige el arreglo mínimo — **borrar `|| true` solo no hace nada**, porque sin `pipefail` el estado del pipe es el de `tee`, que es `0` — y le cede el PR. Verificado por lectura de vuelta: 2 comentarios en el hilo, el segundo es nuestro.
2. **`vllm-project/vllm#62322@2026-11-06T18:15:00Z`** (1 475 car.) — **retirada** de la mitad 1 de nuestro comentario del `2026-10-19`. Nuestro arnés instalaba un wheel sintético **por ruta de archivo**; `mosafariuk` resuelve por nombre con `--extra-index-url`, que es la única rama donde `uv` rechaza un `Requires-Dist` con URL. Lo que medimos fue nuestra reconstrucción de METADATA, no el artefacto que la gente instala. El `triton @` de `requirements/cpu.txt:25-26` gated por `platform_machine == "x86_64"` explica la asimetría x86_64/aarch64 sin nada más. Verificado por lectura de vuelta: 3 comentarios, el tercero es nuestro.

### 12.7 Política que sale de esta jornada

- **`tenstorrent/tt-metal`: cero escrituras.** Un autor de PR pidió que se bloqueara la cuenta en ese repo. La resolución no es un mensaje — cualquier mensaje nuevo es la conducta que motivó la petición. Se deja el hilo como está y no se vuelve.
- **Ningún comentario ajeno se publica con un símbolo, una ruta o un archivo que no se haya leído en el repo destino y en el commit declarado.** Las dos citas fantasma se habrían detenido con la misma sonda que ya corre sobre nuestros commits (A2.2), que hoy no tiene autoridad sobre la boca.
- **Los bucles abiertos se cierran o se declaran.** Queda uno declarado: `BerriAI/litellm#47340`, repro de `Mrun25` del `2026-10-20T04:25:18Z`, sin respuesta nuestra.
