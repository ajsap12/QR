# Exact Failure Replay — Execution Status

Prepared and committed:

- `run_regenerate_and_replay_failures.py`
- `.github/workflows/bpgd-failure-replay.yml`

The workflow is designed to:

1. Regenerate the fixed-seed 12,000-shot stateful BPGD corpus.
2. Persist every full syndrome vector for the rare failure cases.
3. Replay exact cases under `T` and clipping variants.
4. Upload `stateful_failure_corpus.json` and `exact_failure_variant_results.json` as workflow artifacts.

## Current status

GitHub returned no workflow run for commit `da3976d5d257fad12049dda4ef6cd6dd3857d0b2` after two checks. Therefore the computational replay has **not yet executed in GitHub Actions**.

Likely causes include Actions being disabled for the repository, workflow execution being restricted to the default branch, or the GitHub App lacking Actions execution permission.

No exact-variant result is claimed until a workflow run and artifacts exist.
