---
title: Catorce de quince URLs dicen el mismo título, y la causa es una directiva de tres palabras
lede: Sobre 15 URLs vivas de un sitio Next.js, 14 sirven literalmente el mismo título y ninguna declara canonical. La única que tiene título propio es la única cuyo componente no empieza por "use client".
date: 2026-11-20
tags: nextjs, react, seo, arquitectura
---

## El síntoma, medido

Un sitio con contenido distinto en cada ruta. Medí el HTML crudo de 15 URLs — 7 rutas estáticas más las 8 rutas dinámicas de una comunidad — y esto es lo que devuelve el servidor:

| ruta | título servido |
|---|---|
| `/` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/arquitecto-cuantico` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/codigo-origen` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/mente-eterna` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/privacy` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/terms` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/informes/ariastate` | **Informe de riesgo estructural — ariastate · Platino Labs** |

Catorce de quince. La excepción no es aleatoria, y ahí está toda la pieza.

*(Tabla abreviada: se listan 8 de las 15 URLs medidas. Las 7 restantes — `/pinterest-demo`, `/tiktok-demo` y los 5 slugs de comunidad no listados — devuelven el mismo título raíz. El listado completo se reproduce al final.)*

Además: `rel="canonical"` aparece **0 veces** en las 15. Y `https://arquitectocuantico.com/sitemap.xml` responde **HTTP 404**.

## La causa no es el contenido

No es que el sitio no defina títulos. Es que no puede definirlos con el mecanismo que eligió.

En el App Router de Next.js hay dos formas de poner un título. La primera es exportar `metadata` desde un componente de servidor: el framework la serializa a `<head>`. La segunda es renderizar un elemento `<title>` en cualquier punto del árbol — React 19 lo eleva a `<head>`, también durante el renderizado en servidor.

**`"use client"` no impide ninguna de las dos cosas por sí mismo**, y conviene decirlo antes de seguir, porque la intuición habitual —«cliente significa que lo pinta el navegador y el servidor no»— es falsa, y se mide en un comando. `/privacy` es un componente de cliente y su texto completo está en el HTML crudo:

```
curl -sL https://arquitectocuantico.com/privacy | sed 's/<[^>]*>/ /g' | tr -s ' ' | wc -c
→ 3194
```

Tres mil ciento noventa y cuatro caracteres de texto visible servidos por el servidor, con el JavaScript sin ejecutar. El componente de cliente se prerenderiza igual.

Lo que `"use client"` sí hace es excluir el módulo de la exportación de `metadata`: esa API es de servidor y no está disponible en el lado cliente. El sitio eligió `metadata` —una sola vez, en `src/app/layout.tsx`— y marcó las otras siete rutas como `"use client"`. El resultado no es una imposibilidad: es una omisión, con una declaración para quince URLs.

Conteo sobre el repositorio, en `fb28bab`:

```
find src/app -name page.tsx | wc -l                            → 8
grep -rl '^"use client"' src/app --include=page.tsx | wc -l    → 7
```

Siete de ocho `page.tsx` abren con `"use client"` — el 87,5 %. El único que no lo hace es `src/app/informes/ariastate/page.tsx`, y es el único que exporta su propio título.

## El 2×2, sin excepciones

| qué es el componente | URLs servidas | declara su propio título |
|---|---|---|
| `"use client"` | 14 | 0 |
| servidor | 1 | 1 |

Cero de catorce, uno de uno. La única ruta que declara algo es también la única a la que `metadata` le está permitido.

Y el efecto es multiplicativo, no aditivo: cada slug nuevo que se añada a la comunidad hereda el mismo título raíz sin que nadie toque nada. La deuda no crece de uno en uno; crece con el catálogo.

## El arreglo es estructural

Escribir un `<title>` dentro de cada componente de cliente también funcionaría — acabamos de medir que se prerenderiza — y esa es justamente la trampa: reparte la misma declaración en catorce archivos, uno por slug, y el decimoquinto que se añada mañana vuelve a olvidarla. La deuda no se paga una vez; se paga con el catálogo.

El arreglo sube la declaración a donde vive el servidor, que es donde el catálogo ya está listado:

- `src/app/layout.tsx` — `metadataBase`, plantilla de título, `openGraph`, `robots`.
- `src/app/comunidad/layout.tsx` — título propio de la sala común.
- `src/app/comunidad/[slug]/layout.tsx` — `generateMetadata`, que sí recibe los `params` y produce un título por slug.
- `src/app/sitemap.ts` y `src/app/robots.ts` — las dos rutas que no existían y devolvían 404.
- `next.config.ts` — cabeceras `X-Robots-Tag` para no indexar los dos demos.

Seis archivos, +147 −2 líneas. Con eso: `tsc --noEmit` → RC 0, `next build` → RC 0, y los tres layouts de servidor emiten canonical más tres alternates `hreflang` por página.

## El punto ciego: el arreglo no llega a estas URLs

Aquí es donde la pieza se separa de casi todo lo que se escribe sobre este tema. El parche está escrito y validado. **Y ninguna de las quince URLs lo sirve.**

```
$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/
200 age=783014

$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
404 age=175297
```

`783014` segundos son **9,06 días**: el HTML que sirve hoy la portada se generó antes de que el parche existiera. `175297` segundos son **2,03 días**: el 404 del sitemap está cacheado desde el día 18.

Y aquí está la segunda trampa, la que me costó corregir el primer borrador de esta pieza: **`age` mide la respuesta, no el despliegue.** Una CDN puede servir un objeto viejo mientras el origen ya tiene el nuevo; la antigüedad de la respuesta no distingue «no se desplegó» de «se desplegó y la caché no se refrescó». Lo que estos dos números sí prueban es lo único que importa para el lector: el arreglo no llega a estas URLs. Si el origen lo tiene, desde aquí no se puede saber — no hay credencial de despliegue ni identificador de versión en las cabeceras. Ese campo es `NO_MEDIDO`.

Tres preguntas, tres instrumentos, y no se sustituyen:

| qué se quiere saber | qué lo mide | veredicto aquí |
|---|---|---|
| ¿el código compila y genera las rutas? | `next build` | verde, RC 0 |
| ¿el arreglo llega a estas URLs? | `age` de la respuesta | **no**: 9,06 días de antigüedad |
| ¿el origen tiene el despliegue? | credencial de despliegue o id de versión | `NO_MEDIDO` |

Un build verde en local no es un acto público: es la mitad del acto. Y una respuesta vieja no es prueba de un despliegue ausente: es prueba de una respuesta vieja. Las dos confusiones se parecen porque las dos se sienten como un veredicto.

## El desenlace, medido hoy

La sección anterior la escribí sin credencial de despliegue. Horas después había dos despliegues hechos desde el repositorio, y volví a correr el mismo censo sobre las mismas quince rutas. El resultado no es el que esa sección deja esperar:

| medición | antes | después |
|---|---|---|
| rutas medidas | 15 | 15 |
| títulos distintos | 2 | 15 |
| títulos repetidos | 14 | 0 |
| rutas con `rel="canonical"` | 0 | 15 |
| `/sitemap.xml` | 404 | 200, 11 URLs |
| `/robots.txt` con `Sitemap:` | no | sí |

El arreglo cubrió las once URLs declaradas en el sitemap. Las cuatro restantes — `/privacy`, `/terms` y las dos pantallas de autorización OAuth — seguían sirviendo el título del layout raíz: son componentes de cliente sin layout de servidor, que es literalmente el punto ciego que la sección anterior describe. Cuatro layouts de servidor más y el censo cierra en 15 de 15.

Y una corrección a mi propio plan: tenía la purga de Cloudflare como paso obligatorio antes de sondear. No hizo falta. `cf-cache-status` responde `DYNAMIC` en `/` y en `/sitemap.xml` —servidas desde el origen— y `REVALIDATED` en `/robots.txt`, que sí tenía una copia almacenada y la revalidó contra el origen. Qué caché produjo el `age` viejo no lo dice ninguna de esas cabeceras: ese campo queda `NO_MEDIDO`. Lo que sí se observa es lo único que importaba para el acto: con el despliegue nuevo, ninguna de las tres rutas sirve ya el objeto anterior, y sin purga manual.

## Qué no afirma esta pieza

- **No afirma** que corregir los títulos vaya a subir el tráfico. La analítica del dominio no es accesible desde donde se hizo esta medición: ese número es `NO_MEDIDO`, y `NO_MEDIDO` no se lee como cero.
- **No afirma** que el 404 del sitemap lo causara el parche. Tiene 2,03 días y el parche se escribió hoy: el 404 es anterior.
- **No afirma** que el despliegue esté ausente del origen. Mide que no llega al lector; el estado del origen es `NO_MEDIDO`.
- **No afirma** que el despliegue vaya a resolverse solo. Entre el repositorio y el dominio hay una CDN que puede reescribir `robots.txt` sin consultar al origen; si lo hace, la directiva `Sitemap:` de `app/robots.ts` no aparecerá nunca en la respuesta. Eso no está medido.
- **No afirma** que `"use client"` sea un error. Es una directiva correcta cuyo efecto lateral —excluir `metadata`— se vuelve costoso cuando se aplica a catorce rutas que no necesitan interactividad.

## Reproducir

El título que sirve cada URL dinámica, en una línea:

```
for s in arquitecto-cuantico codigo-origen corazon-punto-cero experiencias-de-lectura \
         mente-eterna sala-general sincronicidades suenos-y-meditaciones; do
  curl -sL "https://arquitectocuantico.com/comunidad/$s" | grep -o '<title>[^<]*</title>'
done | sort | uniq -c
```

La frontera, en otra:

```
curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
```

Y el conteo de la causa, sobre el repositorio:

```
find src/app -name page.tsx | wc -l
grep -rl '^"use client"' src/app --include=page.tsx | wc -l
```

## CTA único

Antes de leer el contenido de cualquier sitio que heredes, corre esto:

```
curl -sL https://EL-DOMINIO/ | grep -o '<title>[^<]*</title>'
```

Si ese título es también el de las páginas internas, el problema no está en el texto: está en dónde vive la declaración. Y arreglar el texto no lo toca.

- El instrumento con el que se mide esto: https://alexisromtz-lab.github.io/auditor-toolkit/
- Otras mediciones publicadas: https://alexisromtz-lab.github.io/la-auditora/
- El sitio donde esto se aplicó, medido tras desplegar: https://arquitectocuantico.com/?utm_source=la-auditora&utm_medium=articulo&utm_campaign=muro-use-client
