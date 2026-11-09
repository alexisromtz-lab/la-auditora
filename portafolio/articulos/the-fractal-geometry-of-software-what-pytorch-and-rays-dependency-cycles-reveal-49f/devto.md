---
title: "The Fractal Geometry of Software: What PyTorch and Ray's Dependency Cycles Reveal"
published: false
description: "The Fractal Geometry of Software: What PyTorch and Ray's Dependency Cycles Reveal  Code search can..."
tags: p, y, t, h
canonical_url: "https://alexisromtz-lab.github.io/la-auditora/portafolio/articulos/en/the-fractal-geometry-of-software-what-pytorch-and-rays-dependency-cycles-reveal-49f/"
---

The Fractal Geometry of Software: What PyTorch and Ray's Dependency Cycles Reveal

Code search can find a function. Retrieval-augmented generation can retrieve relevant passages. Neither result, by itself, tells us how modules depend on one another.

That distinction matters. A codebase is not only a collection of text. It is also a directed structure: files import modules, modules connect to other modules, and some paths eventually lead back to where they began.

We extracted public Python import graphs for ten repositories and published the sanitized JSON in the [Platino Labs Data Room](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2). The graphs expose a structural fact that a passage search does not answer: the shape and scale of strongly connected components in the declared import graph.

From code retrieval to code structure

Retrieval systems and dependency graphs solve different problems. A retrieval system is designed to find text relevant to a query. An import graph records directed relationships declared by source code. Similarity between two passages does not tell us whether module A imports module B, whether a path leads back to A, or how many modules participate in that cycle.

This is not an argument that retrieval is useless, or that one representation replaces the other. It is an argument for measuring structure directly when the question is structural.

Build the graph from Python syntax

The pipeline parses Python source with the abstract syntax tree (AST), extracts import relationships, and publishes a graph rather than embeddings. It does not ask a language model to infer which modules are related. For a fixed source revision and declared perimeter, the extraction is a deterministic transformation of syntax into edges.

The release adds a strongly connected component (SCC) layer. An SCC is a set of nodes where each node can reach every other node along directed edges. A component with multiple modules therefore contains a cycle; a self-loop also counts as cyclic. The published SCC layer uses iterative Tarjan followed by Kahn's topological ordering of the condensed graph. Its schema and method are described in the [release notes](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2).

Two large components, two different shapes

At the pinned revisions in the release:

| Repository | Modules in graph | SCCs | Cyclic SCCs | Largest cyclic SCC |
|---|---:|---:|---:|---:|
| [PyTorch](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_pytorch_611154b3.json) · `611154b3` | 2,527 | 831 | 14 | **1,660 modules** |
| [Ray](https://github.com/alexisromtz-lab/platino-data-room/releases/download/arch-index-20261029-batch2/public_graph_ray_096fce7c.json) · `096fce7c` | 4,108 | 2,787 | 23 | **960 modules** |

The largest PyTorch component contains about 65.7% of the modules in this graph. Ray's largest contains about 23.4%—roughly 23% of the 4,108 modules in its declared graph. These are measurements of the published graph perimeter, not claims about every file or every runtime path in either repository.

The numbers are not a ranking of engineering quality. They describe topology: how many components the graph has, how many are cyclic, and how large its largest cycle is. That is more specific—and more testable—than calling a codebase “tightly coupled.”

What cycles can mean for performance

Import cycles can be relevant to startup and initialization when the edges are eager imports: a module may trigger other modules to load, and initialization order can become harder to reason about. A large cycle can also make isolated testing, refactoring, and ownership boundaries more complicated.

But an SCC count is not a runtime benchmark. The published graphs do not measure import duration, memory use, cold-start latency, or the cost of any particular execution path. A static cycle does not, by itself, prove a performance regression. To establish that, we would need a separate, controlled runtime measurement with a declared command, environment, and workload.

The graph gives maintainers a map of where to ask those questions. It does not pretend to answer them without measurement.

The storage comparison—and its boundary

The PyTorch graph asset is **7,468,906 bytes**, or **7.47 MB** in decimal units. Across all ten current SCC assets, the published graphs total **46,259,186 bytes**.

Those sizes are useful facts about the artifacts. They are not a measured comparison with a RAG index. The **80.19%** figure sometimes quoted came from an earlier, pre-SCC graph total compared with the `.py` files being indexed; it did not measure RAG storage. With the current SCC assets, the release reports **79.93%** less storage than the mapped source files across all ten repositories, using a mixed denominator: eight source totals were measured file by file, while Airflow and PyTorch are declared estimates. For the eight directly measured repositories, the reduction is **78.49%**.

We should not claim that a RAG index would require “hundreds of megabytes” or that this graph saves 80.19% versus RAG without measuring a specified RAG pipeline over the same files, with its chunking, embedding model, dimensions, and serialization declared. Those are different artifacts and different comparisons.

## Negative results are part of the map

A useful structural instrument must be able to report what it did not find. If a declared perimeter has no cyclic SCC, that is a meaningful result about that graph—not proof that the whole application has no runtime coupling. If a cycle exists, it is evidence of a static import path, not a verdict that the code is broken.

This is why the data is published as JSON with repository commit pins and a stated perimeter. Readers can inspect the bytes, recompute the SCC layer, and challenge the extraction. The goal is not to replace engineering judgment with a score. It is to make the structure available for judgment.

Software has geometry in this precise sense: its relationships form a graph, and cycles have measurable shape. An AST-based graph makes that shape inspectable without embeddings or model-generated guesses. Retrieval can help us find code; a structural graph can show us how the code is connected.

Explore the ten pinned graphs in the [public Data Room](https://github.com/alexisromtz-lab/platino-data-room/releases/tag/arch-index-20261029-batch2).

<!-- HUELLA-ARTICULO-DEVTO-FINAL-20261029 -->
