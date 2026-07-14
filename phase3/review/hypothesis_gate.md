# Phase 3A Hypothesis Gate

No hypothesis or experiment advances to costly execution until every required item below is checked.

## Evidence gate

- [ ] Every supporting Phase 2 evidence object resolves to the correct paper version.
- [ ] Page, equation, figure, table, theorem, and algorithm locators are independently checked.
- [ ] Material caveats and boundary conditions are captured.
- [ ] Contradiction/gap records distinguish direct conflict from scope mismatch.

## Hypothesis-quality gate

- [ ] Research question is precise and scientifically meaningful.
- [ ] Null and alternative hypotheses are explicit.
- [ ] Primary outcomes and practical effect thresholds are predeclared.
- [ ] Falsification conditions could realistically occur.
- [ ] Assumptions, exclusions, and foreseeable confounders are documented.
- [ ] The hypothesis does not merely restate a paper's result.

## Experiment-design gate

- [ ] Code instances, datasets, noise models, and syndrome conventions are versioned.
- [ ] Baselines are faithful and use fair stopping/resource rules.
- [ ] Sample-size or simulation stopping logic is documented.
- [ ] Confidence intervals and multiple-comparison policy are specified.
- [ ] Random seeds and environment manifests will be preserved.
- [ ] Smoke tests precede pilot and full runs.
- [ ] Compute, memory, runtime, and financial caps are approved.
- [ ] Failure and abort conditions are explicit.

## Reproducibility gate

- [ ] At least one published baseline has been minimally reproduced.
- [ ] Missing implementation details are recorded rather than guessed silently.
- [ ] Independent seed replication is part of the design.
- [ ] A second implementation/operator is planned where feasible.

## Decision states

- `blocked`: evidence or implementation details are insufficient.
- `revise`: scientifically plausible but design changes are required.
- `approved_smoke_test`: tiny bounded validation may run.
- `approved_pilot`: limited experiment may run within a fixed cap.
- `approved_primary`: full primary experiment may run.
- `replicated`: result survived the predeclared independent replication.

Only `replicated` results may be considered for the discovery gate, and even then they must be stated with uncertainty and scope limitations.
