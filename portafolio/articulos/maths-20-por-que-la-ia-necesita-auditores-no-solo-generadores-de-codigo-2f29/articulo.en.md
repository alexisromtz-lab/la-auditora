---
title: Maths 2.0: why AI needs auditors, not just code generators
lede: Producir una respuesta no es lo mismo que poder explicarla, verificarla y mantenerla. Una lectura de Math 2.0 de Terence Tao aplicada a la auditoría de sistemas de IA, con límites de evidencia declarados.
date: 2026-10-28
tags: a, i, ,,  , s, o, f, t, w, a, r, e, d, e, v, e, l, o, p, m, e, n, t, ,,  , m, a, t, h, ,,  , e, n, g, i, n, e, e, r, i, n, g
fuente: https://dev.to/alexisromtz7/maths-20-por-que-la-ia-necesita-auditores-no-solo-generadores-de-codigo-2f29
lang: en
solo_en: si
---

AI can help produce code, tests, proofs and designs at a speed that changes how technical teams work. But producing an answer is not the same as being able to explain it, verify it and maintain it. As the volume of output grows, so does the value of being able to inspect it.

That difference — between generating and understanding — connects to a wider conversation about the future of mathematics.

## What "Math 2.0" means here

In his entry of 10 October 2026, Terence Tao describes the talk *Math 2.0* he gave at Caltech on the 9th. His proposal explores how AI tools can support the mathematical community and how mathematical understanding can better orient applications in the real world.

This is not a proposal by Tao about software auditing. The connection to AI systems is our application of that idea: if a tool produces results, we need ways to review what it produced, what object it worked on, and what the limits of the conclusion are.

The practical question is not only "does the output work?". It is also: "can we reconstruct why we trust it, and what evidence would change that decision?".

## From the answer to the verifiable object

A useful structural audit starts by bounding the object: a concrete version of the repository, the dependencies observed, the method and the commands executed. Then it publishes what it found, which controls it applied, and what was left out.

That scope matters. A dependency graph can reveal relationships that are hard to see at a glance, but it does not by itself prove that the system is secure, correct, or understandable in all of its behaviour. A metric is a signal to investigate; it does not replace execution tests, nor does it turn an observation into a certification.

That is why a technical conclusion should be able to answer, at a minimum:

- Which exact version was examined?
- Which tool, rule and configuration were used?
- Which control would catch a false positive or an omission?
- Which part of the system was not observed?
- Can another person repeat the analysis and get the same result?

If these answers are missing, the result can serve as a lead, but not as certainty.

## Sustainability also needs auditing

The same discipline applies to efficiency claims. Saying that an architecture is "green" requires more than identifying the hardware or running a local model. You have to declare the task, the machine, the measured boundary, the instrument, the baseline and the repetitions.

At Platino Labs we still do not have a measurement that backs a 95 % energy saving, nor a comparison that proves one platform is superior for this audit. We do not use that percentage as a claim. First we need reproducible data; then a conclusion limited to what that data actually measures.

Sustainable certainty does not promise that a system will never fail. It exposes what was reviewed, how it can be checked, and what remains unknown. That transparency also helps decide what to optimise and where it makes sense to run each workload, without confusing an efficiency hypothesis with a result.

## Generating more is not enough

AI expands what we can produce. The next step is to build better habits for reviewing what was produced: evidence tied to a version, visible controls, explicit limits, and results that another person can check again.

That is the role we propose for structural auditing: not replacing the people who develop systems, nor declaring that everything is understood, but making more visible what we know, what we infer, and what we do not know yet. If AI is going to take part in high-impact technical work, the quality of its output and the quality of its verification must advance together.

**Are you a CTO who wants to understand the structure of your system better?** Visit [the Platino Labs portfolio](https://alexisromtz-lab.github.io/la-auditora/) to see the approach and explore an audit.

**Sources**

- Terence Tao, ["Math 2.0"](https://terrytao.wordpress.com/2026/10/10/math-2-0/), 10 October 2026.
- Terence Tao, ["Some of my recent talks and interviews"](https://terrytao.wordpress.com/2026/10/17/some-of-my-recent-talks-and-interviews/), 17 October 2026.
- American Institute of Mathematics, ["Terence Tao presents Math 2.0 at the 2026 AIM Public Lecture"](https://aimath.org/news/article/terence-tao-presents-math-20-at-the-2026-aim-public-lecture/).
