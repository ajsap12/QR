# Level 2 Scientific Extraction — arXiv:2509.22347

**Paper:** Decoding quantum low density parity check codes with diffusion  
**Authors:** Zejun Liu; Anqi Gong; Bryan K. Clark  
**Status:** machine-extracted draft; not yet human-approved evidence

## Research question
Can diffusion models infer logical errors for QLDPC codes with better accuracy/latency trade-offs than BP-OSD and autoregressive neural decoders?

## Core contributions
- Introduces masked and continuous diffusion decoders for syndrome-to-logical-error inference.
- Evaluates bivariate bicycle codes under realistic circuit-level noise.
- Reports masked diffusion as more accurate, often faster on average, and faster in the worst case than compared state-of-the-art decoders.
- Reports that fewer diffusion steps can improve speed with limited accuracy loss.
- Uses attention analysis to argue that the network learns code structure from syndrome/logical-error pairs.
- Reports better scaling for masked than continuous diffusion under code-capacity noise.

## Mathematical objects to extract from full text
- Forward/noising and reverse/denoising processes.
- Masking distribution and inference objective.
- Syndrome and logical-class representation.
- Loss function, factorized attention, and sampling schedule.
- Logical-error-rate and runtime definitions.

## Training / inference workflow
- Generate syndrome–logical-error pairs under specified code/noise models.
- Train diffusion model with architecture and schedule stated in the paper.
- Sample logical classes using a configurable number of reverse steps.
- Compare accuracy and latency against BP-OSD and autoregressive baselines.

## Assumptions to verify
- Training/test code families and distances.
- Whether a separate model is trained per code/noise point.
- Dataset generation, class balance, and leakage controls.
- Hardware used for latency comparisons.
- Baseline implementation and tuning fairness.

## Key claims requiring page-level evidence
- Accuracy advantage over each baseline and statistical uncertainty.
- Average and worst-case latency comparisons.
- Accuracy degradation as diffusion steps are reduced.
- Scaling difference between masked and continuous variants.
- Evidence that learned attention corresponds to code structure.

## Limitations / risks
- Training cost and retraining requirements may dominate deployment economics.
- Neural latency comparisons can be hardware- and batching-dependent.
- Generalization beyond tested BB codes/noise models is unproven.
- Interpretability observations do not by themselves establish causal use of code structure.

## Cross-paper links
- Direct comparison with BPGD/BP-OSD on identical BB code instances.
- Compare worst-case latency with union-find baselines.
- Test transfer to coprime/self-dual BB and erasure-aware circuits.

## Page-level review checklist
- Extract architecture, parameter count, optimizer, epochs, data volume, and seeds.
- Record every code/noise/decoder benchmark and confidence interval.
- Normalize latency comparisons by hardware, batch size, and stopping rules.
- Separate code-capacity from circuit-level conclusions.
