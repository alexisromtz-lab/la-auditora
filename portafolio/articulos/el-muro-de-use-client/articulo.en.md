---
title: Fourteen of fifteen URLs serve the same title, and the cause is a three-word directive
lede: Across 15 live URLs of a Next.js site, 14 serve literally the same title and none declares a canonical. The only one with a title of its own is the only one whose component does not start with "use client".
date: 2026-11-20
tags: nextjs, react, seo, architecture
lang: en
---

## The symptom, measured

A site with different content on every route. I measured the raw HTML of 15 URLs — 7 static routes plus the 8 dynamic routes of one community — and this is what the server returns:

| route | title served |
|---|---|
| `/` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/arquitecto-cuantico` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/codigo-origen` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/comunidad/mente-eterna` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/privacy` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/terms` | El Arquitecto Cuántico — Libros de Jose Alexis Román Martínez |
| `/informes/ariastate` | **Informe de riesgo estructural — ariastate · Platino Labs** |

Fourteen of fifteen. The exception is not random, and that is the whole piece.

*(Abbreviated table: 8 of the 15 measured URLs are listed. The remaining 7 — `/pinterest-demo`, `/tiktok-demo` and the 5 community slugs not listed — return the same root title. The full listing is reproduced at the end.)*

Also: `rel="canonical"` appears **0 times** across the 15. And `https://arquitectocuantico.com/sitemap.xml` answers **HTTP 404**.

## The cause is not the content

It is not that the site does not define titles. It is that it cannot define them where it defined them.

In the Next.js App Router the title of a route is read by the **server**: it is the part of the tree that gets serialised into `<head>` before any JavaScript exists. It is declared by exporting `metadata` from a server component.

`"use client"` marks the module boundary: everything that file imports enters the browser bundle and stops running on the server. And one of the things that stops being available is precisely the `metadata` export.

Counting over the repository, at `fb28bab`:

```
find src/app -name page.tsx | wc -l                            → 8
grep -rl '^"use client"' src/app --include=page.tsx | wc -l    → 7
```

Seven of eight `page.tsx` open with `"use client"` — 87.5%. The only one that does not is `src/app/informes/ariastate/page.tsx`, and it is the only one that exports a title of its own.

## The 2×2, without exceptions

| what the component is | URLs served | with a title of its own |
|---|---|---|
| `"use client"` | 14 | 0 |
| server | 1 | 1 |

Zero of fourteen, one of one. A rule with a single exception is not a correlation: it is the rule.

And the effect is multiplicative, not additive: every new slug added to the community inherits the same root title without anyone touching anything. The debt does not grow one at a time; it grows with the catalogue.

## The fix is structural

Rewriting the title inside each client component does not work: React 19 can mount a `<title>` and the browser applies it, but that happens **after** hydration, and the crawler that decides whether to index reads the HTML before. The title would be right for a human and empty for a search engine — the worst of the two states, because it looks solved.

The fix is to move the declaration up to where the server lives:

- `src/app/layout.tsx` — `metadataBase`, title template, `openGraph`, `robots`.
- `src/app/comunidad/layout.tsx` — the title of the shared room.
- `src/app/comunidad/[slug]/layout.tsx` — `generateMetadata`, which does receive the `params` and produces a title per slug.
- `src/app/sitemap.ts` and `src/app/robots.ts` — the two routes that did not exist and answered 404.
- `next.config.ts` — `X-Robots-Tag` headers so the two demos are not indexed.

Six files, +147 −2 lines. With that: `tsc --noEmit` → RC 0, `next build` → RC 0, and the three server layouts emit a canonical plus three `hreflang` alternates per page.

## The blind spot: the fix never reached the edge

This is where the piece parts ways with almost everything written about this topic. The patch is written and validated. **It is not deployed.** And I am not saying that from memory: a header measures it.

```
$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/
200 age=783014

$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
404 age=175297
```

`783014` seconds is **9.06 days**: the HTML the front page serves today was generated before the patch existed. `175297` seconds is **2.03 days**: the sitemap 404 has been cached since the 18th.

Two different objects, two different instruments:

| what you want to know | what measures it | verdict here |
|---|---|---|
| does the code compile and generate the routes? | `next build` | green, RC 0 |
| does production serve that code? | the response `age` | **no**: 9.06 days old |

A green local build is not a public act. It is half the act. Measuring only the first half is how you ship a fix nobody receives, and it feels finished.

## What this piece does not claim

- **It does not claim** that fixing the titles will raise traffic. The domain's analytics are not reachable from where this measurement was taken: that number is `NO_MEDIDO` (not measured), and `NO_MEDIDO` does not read as zero.
- **It does not claim** that the patch caused the sitemap 404. It is 2.03 days old and the patch was written today: the 404 predates it.
- **It does not claim** that the deployment will resolve itself. Between the repository and the domain there is a CDN that can rewrite `robots.txt` without consulting the origin; if it does, the `Sitemap:` directive from `app/robots.ts` will never appear in the response. That is not measured.
- **It does not claim** that `"use client"` is a mistake. It is a correct directive used in the wrong place: the front page, the community and the legal pages are server components that someone marked as interactive.

## Reproduce

The title each dynamic URL serves, in one line:

```
for s in arquitecto-cuantico codigo-origen corazon-punto-cero experiencias-de-lectura \
         mente-eterna sala-general sincronicidades suenos-y-meditaciones; do
  curl -sL "https://arquitectocuantico.com/comunidad/$s" | grep -o '<title>[^<]*</title>'
done | sort | uniq -c
```

The edge, in another:

```
curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
```

And the count behind the cause, over the repository:

```
find src/app -name page.tsx | wc -l
grep -rl '^"use client"' src/app --include=page.tsx | wc -l
```

## Single CTA

Before reading the content of any site you inherit, run this (`EL-DOMINIO` stands for the domain):

```
curl -sL https://EL-DOMINIO/ | grep -o '<title>[^<]*</title>'
```

If that title is also the title of the inner pages, the problem is not in the text: it is in where the declaration lives. And fixing the text does not touch it.

- The instrument this is measured with: https://alexisromtz-lab.github.io/auditor-toolkit/
- Other published measurements: https://alexisromtz-lab.github.io/la-auditora/
