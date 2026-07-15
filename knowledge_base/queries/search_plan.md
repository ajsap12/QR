# QEC Frontier Search Plan

## Scope

Primary review window: January 2025 through the current date, with older foundational papers included when they define a decoder family, code family, hardware architecture, or benchmark.

## Workstreams

### 1. Decoder algorithms

Search terms:

- quantum LDPC decoder belief propagation
- BP-OSD quantum error correction
- BPGD quantum decoder
- Relay-BP decoder
- beam-search quantum decoder
- localized inversion quantum decoder
- matching BB code decoder
- neural decoder GNN transformer diffusion QEC
- reversible decimation LDPC decoding
- backtracking belief propagation decoder

### 2. Systems and real-time operation

- real-time quantum error correction decoder
- QEC tail latency p99 p99.9
- decoder queueing backlog deadline
- streaming QLDPC decoding
- sliding-window decoder
- FPGA quantum decoder
- ASIC quantum error correction decoder
- GPU quantum decoder CUDA

### 3. Compiler and infrastructure

- quantum error correction compiler
- decoder intermediate representation
- QEC data interface QECi
- hardware-aware decoder synthesis
- code decoder hardware co-design
- automatic decoder generation FPGA
- decoder verification formal methods
- decoder observability replay trace

### 4. Failure mechanisms and rare events

- quantum trapping sets
- absorbing sets quantum LDPC
- pseudocodeword quantum BP
- decoder error floor qLDPC
- rare-event simulation QEC
- importance sampling logical error rate
- adversarial syndrome generation
- hard syndrome corpus decoder

### 5. Logical operations

- qLDPC lattice surgery decoding
- logical operation decoder
- transversal gate decoding
- deformed code decoding
- fault-tolerant operation decoder

### 6. Commercial and IP

- quantum error correction decoder patent
- FPGA decoder patent quantum
- quantum decoder compiler patent
- QEC software platform
- commercial QEC decoder toolkit
- quantum control stack decoder

## Source quotas for the 50-source pilot

- 25 papers or preprints
- 5 conference sources
- 8 repositories
- 5 industry reports or blogs
- 5 patents or applications
- 2 standards or interface specifications

## Review procedure

1. Collect bibliographic metadata and abstract-level screening.
2. Reject irrelevant or duplicate sources.
3. Verify decision-critical claims in the full source.
4. Add nearest-prior-art links between records.
5. Assign momentum, implementation maturity, and commercial-signal scores.
6. Run schema validation.
7. Produce category counts and an evidence-gap report.

## First decision questions

- Is bounded local reversal in BPGD distinct from existing list, beam, restart, and decimation decoders?
- Does a decoder algorithm IR exist beyond syndrome-data interface standards?
- Which parts of decoder verification and observability are genuinely unoccupied?
- Is failure-corpus and semantic-replay infrastructure already public under another name?
- Where are industrial teams spending engineering resources that have not yet become mainstream papers?
