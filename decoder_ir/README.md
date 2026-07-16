# QR Decoder IR — Version 0 Scope

## Purpose

Define a hardware-neutral representation of a decoder experiment before attempting full compiler construction.

The first version is intentionally narrow: it captures code structure, decoder operations, scheduling, budgets, observability, and target constraints. It does not promise automatic FPGA generation yet.

## Core entities

### Code

- parity-check matrices
- stabilizer generators
- logical operators
- code family and parameters
- sector decomposition

### Noise model

- physical error rate
- Pauli bias
- measurement-noise model
- circuit-level or code-capacity flag

### Decoder graph

- variable nodes
- check nodes
- edges
- update dependencies
- optional alternate check bases

### Operations

- message update
- variable update
- check update
- decimate
- undo decimation
- checkpoint
- restore
- restart
- branch
- merge candidates
- syndrome consistency check
- logical-class check

### Schedule

- flooding
- layered/serial
- residual-driven
- fixed iteration budget
- event-triggered backtrack

### Resource constraints

- maximum iterations
- maximum backtracks
- beam width
- memory budget
- latency budget
- arithmetic precision
- target CPU/GPU/FPGA/ASIC

### Observability

- residual syndrome trajectory
- LLR trajectory
- selected variables
- reversals
- branch count
- convergence status
- operation count
- memory estimate

## Version-0 deliverable

Represent the current Gate 3 decoder configurations in a common JSON document and prove they can be validated and reproduced from that document.

## Non-goals

- automatic RTL synthesis
- universal support for every decoder family
- guaranteed hardware timing
- replacement of QEC data-interface standards

Those become later milestones only after the IR proves useful for experiment reproduction.
