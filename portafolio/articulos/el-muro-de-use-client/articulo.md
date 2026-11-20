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

No es que el sitio no defina títulos. Es que no puede definirlos donde los definió.

En el App Router de Next.js, el título de una ruta lo lee el **servidor**: es la parte del árbol que se serializa a `<head>` antes de que exista JavaScript. Se declara exportando `metadata` desde un componente de servidor.

`"use client"` marca la frontera del módulo: todo lo que ese fichero importa entra al bundle del navegador y deja de ejecutarse en el servidor. Y una de las cosas que deja de estar disponible es exactamente la exportación de `metadata`.

Conteo sobre el repositorio, en `fb28bab`:

```
find src/app -name page.tsx | wc -l                            → 8
grep -rl '^"use client"' src/app --include=page.tsx | wc -l    → 7
```

Siete de ocho `page.tsx` abren con `"use client"` — el 87,5 %. El único que no lo hace es `src/app/informes/ariastate/page.tsx`, y es el único que exporta su propio título.

## El 2×2, sin excepciones

| qué es el componente | URLs servidas | con título propio |
|---|---|---|
| `"use client"` | 14 | 0 |
| servidor | 1 | 1 |

Cero de catorce, uno de uno. Una regla con una sola excepción no es una correlación: es la regla.

Y el efecto es multiplicativo, no aditivo: cada slug nuevo que se añada a la comunidad hereda el mismo título raíz sin que nadie toque nada. La deuda no crece de uno en uno; crece con el catálogo.

## El arreglo es estructural

Reescribir el título dentro de cada componente de cliente no funciona: React 19 puede montar un `<title>` y el navegador lo aplica, pero eso ocurre **después** de la hidratación, y el rastreador que decide indexar lee el HTML antes. El título quedaría correcto para un humano y vacío para un buscador — el peor de los dos estados, porque parece resuelto.

El arreglo es subir la declaración al nivel donde vive el servidor:

- `src/app/layout.tsx` — `metadataBase`, plantilla de título, `openGraph`, `robots`.
- `src/app/comunidad/layout.tsx` — título propio de la sala común.
- `src/app/comunidad/[slug]/layout.tsx` — `generateMetadata`, que sí recibe los `params` y produce un título por slug.
- `src/app/sitemap.ts` y `src/app/robots.ts` — las dos rutas que no existían y devolvían 404.
- `next.config.ts` — cabeceras `X-Robots-Tag` para no indexar los dos demos.

Seis archivos, +147 −2 líneas. Con eso: `tsc --noEmit` → RC 0, `next build` → RC 0, y los tres layouts de servidor emiten canonical más tres alternates `hreflang` por página.

## El punto ciego: el arreglo no llegó a la frontera

Aquí es donde la pieza se separa de casi todo lo que se escribe sobre este tema. El parche está escrito y validado. **No está desplegado.** Y eso no lo digo por memoria: lo mide una cabecera.

```
$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/
200 age=783014

$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
404 age=175297
```

`783014` segundos son **9,06 días**: el HTML que sirve hoy la portada se generó antes de que el parche existiera. `175297` segundos son **2,03 días**: el 404 del sitemap está cacheado desde el día 18.

Dos objetos distintos, dos instrumentos distintos:

| qué se quiere saber | qué lo mide | veredicto aquí |
|---|---|---|
| ¿el código compila y genera las rutas? | `next build` | verde, RC 0 |
| ¿producción sirve ese código? | `age` de la respuesta | **no**: 9,06 días de antigüedad |

Un build verde en local no es un acto público. Es la mitad del acto. Medir sólo la primera mitad es cómo se publica un arreglo que nadie recibe, y se siente terminado.

## Qué no afirma esta pieza

- **No afirma** que corregir los títulos vaya a subir el tráfico. La analítica del dominio no es accesible desde donde se hizo esta medición: ese número es `NO_MEDIDO`, y `NO_MEDIDO` no se lee como cero.
- **No afirma** que el 404 del sitemap lo causara el parche. Tiene 2,03 días y el parche se escribió hoy: el 404 es anterior.
- **No afirma** que el despliegue vaya a resolverse solo. Entre el repositorio y el dominio hay una CDN que puede reescribir `robots.txt` sin consultar al origen; si lo hace, la directiva `Sitemap:` de `app/robots.ts` no aparecerá nunca en la respuesta. Eso no está medido.
- **No afirma** que `"use client"` sea un error. Es una directiva correcta usada en el sitio equivocado: la portada, la comunidad y las páginas legales son componentes de servidor que alguien marcó como interactivos.

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
