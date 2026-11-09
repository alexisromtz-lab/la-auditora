---
title: "Why 99% of your LLM Bill is Context Overhead (and how to measure it)"
published: false
description: "The 99% is a measured share of token volume—not proof that 99% of dollars are wasted.  In one..."
tags: a, i, r, c
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/why-99-of-your-llm-bill-is-context-overhead-and-how-to-measure-it-33j/"
---

The 99% is a measured share of token volume—not proof that 99% of dollars are wasted.

In one five-day telemetry window, 99.13% of recorded model tokens were input tokens. That is a useful signal: the work surrounding a model’s response can dwarf the response itself.

But input tokens are not automatically waste, and token share is not the same as bill share. To find what you can actually optimize, measure the parts separately.

What the data says
Across 32,546 model calls and 76 sessions with usage data, the measured totals were:

Metric	Tokens
Input	2,944,901,602
Output	25,895,776
Total	2,970,797,378
Input share	99.13%
This is one measured corpus, not an industry benchmark. And input includes useful task content as well as instructions, tool definitions, and conversation history. The aggregate alone cannot tell us which input was necessary or redundant.

Find the components before optimizing
Tool definitions are one component we can measure directly. In the same telemetry report, the median tool-schema and input tokens differed by tool profile:

Tools exposed	Calls	Median schema tokens	Median input tokens	Schema / input
73	19,729	22,501	84,926.96	26.5%
22	416	9,464	73,672.51	12.8%
These are observational profiles, not a controlled before-and-after test. The difference does not prove that reducing a tool set caused a particular saving; the tasks and calls may differ. It does show why measuring the actual schema-token field is more informative than estimating from the number of tools.

A practical way to measure context
Choose a unit and window. Decide whether you’re measuring calls, sessions, or completed tasks, and record the time range.
Collect provider-reported usage. Keep input and output tokens separate. Record cached-token counts separately when available.
Break input into measurable components. Capture system instructions, tool schemas, task content, and conversation history where your instrumentation supports it. Mark anything inferred as an estimate.
Compare like with like. To test a prompt or tool change, hold the workload and configuration constant, record both versions, and compare the same metrics.
Convert tokens to money only with the applicable rates. Input, output, and cached tokens may have different prices.
For a basic token-share calculation:

input share
=
input tokens
input tokens
+
output tokens
input share= 
input tokens+output tokens
input tokens
​
 
That ratio describes token volume, not necessarily dollars. To estimate cost, apply the provider’s rates to each applicable token category. If the rates or cache treatment are unknown, report cost as unmeasured.

The useful question
“Can we use a smaller model?” is not the only optimization question. Ask what each request sends, which parts are repeated, and whether they need to be present for that task.

The measurement here supports a narrow conclusion: input dominated token volume in this corpus. It does not establish that all input was overhead, that 99.13% of spend went to context, or that a particular reduction would preserve quality. Those require separate, controlled measurements.

If you want to audit your own repository’s supply-chain security or cloud costs, check out our open-source tools at GitHub or reach out for a custom enterprise audit at La Auditora.
