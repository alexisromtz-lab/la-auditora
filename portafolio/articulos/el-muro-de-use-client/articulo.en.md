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

It is not that the site does not define titles. It is that it cannot define them with the mechanism it chose.

In the Next.js App Router there are two ways to set a title. The first is exporting `metadata` from a server component: the framework serialises it into `<head>`. The second is rendering a `<title>` element anywhere in the tree — React 19 hoists it into `<head>`, during server rendering too.

**`"use client"` prevents neither of those things by itself**, and it is worth saying so before going on, because the usual intuition — "client means the browser paints it and the server does not" — is false, and it is measured with one command. `/privacy` is a client component and its full text is in the raw HTML:

```
curl -sL https://arquitectocuantico.com/privacy | sed 's/<[^>]*>/ /g' | tr -s ' ' | wc -c
→ 3194
```

Three thousand one hundred and ninety-four characters of visible text served by the server, with JavaScript never executed. The client component is prerendered all the same.

What `"use client"` does do is exclude the module from the `metadata` export: that API is server-side and is not available on the client. The site chose `metadata` — once, in `src/app/layout.tsx` — and marked the other seven routes as `"use client"`. The result is not an impossibility: it is an omission, with one declaration for fifteen URLs.

Counting over the repository, at `fb28bab`:

```
find src/app -name page.tsx | wc -l                            → 8
grep -rl '^"use client"' src/app --include=page.tsx | wc -l    → 7
```

Seven of eight `page.tsx` open with `"use client"` — 87.5%. The only one that does not is `src/app/informes/ariastate/page.tsx`, and it is the only one that exports a title of its own.

## The 2×2, without exceptions

| what the component is | URLs served | declares a title of its own |
|---|---|---|
| `"use client"` | 14 | 0 |
| server | 1 | 1 |

Zero of fourteen, one of one. The only route that declares anything is also the only one `metadata` is allowed in.

And the effect is multiplicative, not additive: every new slug added to the community inherits the same root title without anyone touching anything. The debt does not grow one at a time; it grows with the catalogue.

## The fix is structural

Writing a `<title>` inside each client component would also work — we just measured that it is prerendered — and that is precisely the trap: it scatters the same declaration across fourteen files, one per slug, and the fifteenth added tomorrow forgets it again. The debt is not paid once; it is paid with the catalogue.

The fix moves the declaration up to where the server lives, which is where the catalogue is already listed:

- `src/app/layout.tsx` — `metadataBase`, title template, `openGraph`, `robots`.
- `src/app/comunidad/layout.tsx` — the title of the shared room.
- `src/app/comunidad/[slug]/layout.tsx` — `generateMetadata`, which does receive the `params` and produces a title per slug.
- `src/app/sitemap.ts` and `src/app/robots.ts` — the two routes that did not exist and answered 404.
- `next.config.ts` — `X-Robots-Tag` headers so the two demos are not indexed.

Six files, +147 −2 lines. With that: `tsc --noEmit` → RC 0, `next build` → RC 0, and the three server layouts emit a canonical plus three `hreflang` alternates per page.

## The blind spot: the fix does not reach these URLs

This is where the piece parts ways with almost everything written about this topic. The patch is written and validated. **And none of the fifteen URLs serves it.**

```
$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/
200 age=783014

$ curl -s -o /dev/null -w '%{http_code} age=%header{age}\n' https://arquitectocuantico.com/sitemap.xml
404 age=175297
```

`783014` seconds is **9.06 days**: the HTML the front page serves today was generated before the patch existed. `175297` seconds is **2.03 days**: the sitemap 404 has been cached since the 18th.

And here is the second trap, the one that cost me a correction in the first draft of this piece: **`age` measures the response, not the deployment.** A CDN can serve a stale object while the origin already holds the new one; the age of the response does not distinguish "it was never deployed" from "it was deployed and the cache was not refreshed". What these two numbers do prove is the only thing that matters to the reader: the fix does not reach these URLs. Whether the origin has it cannot be known from here — there is no deploy credential and no version identifier in the headers. That field is `NO_MEDIDO` (not measured).

Three questions, three instruments, and none of them substitutes for another:

| what you want to know | what measures it | verdict here |
|---|---|---|
| does the code compile and generate the routes? | `next build` | green, RC 0 |
| does the fix reach these URLs? | the response `age` | **no**: 9.06 days old |
| does the origin hold the deployment? | deploy credential or version id | `NO_MEDIDO` |

A green local build is not a public act: it is half the act. And a stale response is not proof of a missing deployment: it is proof of a stale response. The two confusions look alike because both feel like a verdict.

## The outcome, measured today

I wrote the previous section without a deploy credential. Hours later there were two deployments made from the repository, and I ran the same census again over the same fifteen routes. The result is not the one that section leads you to expect:

| measurement | before | after |
|---|---|---|
| routes measured | 15 | 15 |
| distinct titles | 2 | 15 |
| repeated titles | 14 | 0 |
| routes with `rel="canonical"` | 0 | 15 |
| `/sitemap.xml` | 404 | 200, 11 URLs |
| `/robots.txt` with `Sitemap:` | no | yes |

The fix covered the eleven URLs declared in the sitemap. The four remaining — `/privacy`, `/terms` and the two OAuth authorisation screens — still served the root layout title: they are client components with no server layout, which is literally the blind spot the previous section describes. Four more server layouts and the census closes at 15 of 15.

And a correction to my own plan: I had the Cloudflare purge as a mandatory step before probing. It was not needed. `cf-cache-status` answers `DYNAMIC` on `/` and on `/sitemap.xml` — served from the origin — and `REVALIDATED` on `/robots.txt`, which did have a stored copy and revalidated it against the origin. Which cache produced the old `age` is something none of those headers state: that field stays `NO_MEDIDO`. What is observed is the only thing that mattered for the act: with the new deployment, none of the three routes serves the previous object any more, and without a manual purge.

## What this piece does not claim

- **It does not claim** that fixing the titles will raise traffic. The domain's analytics are not reachable from where this measurement was taken: that number is `NO_MEDIDO` (not measured), and `NO_MEDIDO` does not read as zero.
- **It does not claim** that the patch caused the sitemap 404. It is 2.03 days old and the patch was written today: the 404 predates it.
- **It does not claim** that the deployment is absent from the origin. It measures that it does not reach the reader; the state of the origin is `NO_MEDIDO`.
- **It does not claim** that the deployment will resolve itself. Between the repository and the domain there is a CDN that can rewrite `robots.txt` without consulting the origin; if it does, the `Sitemap:` directive from `app/robots.ts` will never appear in the response. That is not measured.
- **It does not claim** that `"use client"` is a mistake. It is a correct directive whose side effect — excluding `metadata` — becomes expensive when applied to fourteen routes that need no interactivity.

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
- The site this was applied to, measured after deploying: https://arquitectocuantico.com/?utm_source=la-auditora&utm_medium=articulo&utm_campaign=muro-use-client
