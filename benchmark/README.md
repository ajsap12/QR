# QR Decoder Benchmark Suite

## Goal

Provide matched-sample, reproducible comparisons across QEC decoders without confusing algorithm quality with workload differences.

## Initial decoder set

- BP
- layered BPGD
- RevBPGD
- random-restart BPGD
- narrow-beam BPGD
- BP-OSD when available
- Relay-BP when a compatible implementation is available

## Initial code set

- published BB primary panel
- expanded hard-case corpus
- later: surface, color, and hypergraph-product controls

## Required metrics

- syndrome convergence
- logical success
- logical failure
- mean operation count
- p95 and p99 operation counts
- wall-clock latency when comparable
- peak state count
- peak checkpoint memory
- unique logical wins
- failure overlap by decoder

## Experimental policy

1. All decoders receive identical syndrome cases.
2. Hard-case corpus results must never be presented as natural-frequency LER.
3. Natural-frequency Monte Carlo runs must preserve unfiltered shot frequencies.
4. Every result records code, sector, physical error rate, random seed, decoder configuration, and software version.
5. Wall-clock comparisons must identify hardware, language, thread count, and implementation maturity.

## First milestone

Produce a Gate 3 matched-sample dashboard comparing layered BPGD, RevBPGD, random restart, and narrow beam on held-out expanded-corpus cases.
