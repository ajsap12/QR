# QEC Frontier Knowledge Base

## Mission

Build a source-grounded knowledge base covering the quantum error-correction frontier so research and product decisions are based on hundreds of sources rather than a small seed set.

## Coverage targets

- 150–250 research papers and preprints
- 30–50 conference talks, posters, or proceedings
- 30–50 GitHub repositories
- 20–40 industry technical reports or engineering blogs
- 20–50 patents or published patent applications

Target total: 250–400 distinct sources.

## Evidence policy

Every record must identify its evidence type:

- `FACT`: hardware- or experiment-demonstrated
- `PUB`: peer-reviewed or archival publication
- `PAT`: patent or published application
- `REPO`: open-source repository evidence
- `ENG`: engineering assessment
- `MARKET`: commercial evidence
- `HYP`: testable hypothesis
- `SPEC`: speculation

Novelty, patentability, or commercial-value claims require an explicit nearest-prior-art comparison.

## Directory layout

```text
knowledge_base/
├── README.md
├── schema/source.schema.json
├── data/sources.jsonl
├── data/opportunities.jsonl
├── queries/search_plan.md
├── reports/frontier_summary.md
└── scripts/validate_kb.py
```

## Required source fields

Each source record should include:

- unique identifier
- title
- authors or organization
- source type
- publication date
- venue
- URL or DOI
- evidence tag
- research categories
- decoder and code families
- noise model
- hardware target
- main contribution
- reported performance
- limitations
- code availability
- patent or ownership notes
- nearest prior art
- relevance to QR
- commercial relevance
- confidence in extraction

## Decision outputs

The knowledge base should support:

1. research-area saturation maps;
2. momentum tracking by year and quarter;
3. nearest-prior-art lookup for proposed ideas;
4. active GitHub and implementation-maturity maps;
5. patent-overlap screening;
6. quantitative ranking of research and commercial opportunities;
7. explicit go/no-go decisions for RevBPGD, decoder IR/compiler, verification, observability, and related ideas.

## Initial milestone

The first milestone is a 50-source pilot set with complete metadata and validation. That pilot will test the schema before scaling to 250–400 sources.
