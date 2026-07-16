# Semantic Failure Replay Analysis

- Exact failure cases: 17
- Semantic variants tested: 7
- Best resolved count: 14/17
- Best variant(s): serial__tie-lowest_index__zero-zero__seed-20260714
- Cases unresolved by every variant: 2

## Variant summary

| Variant | Resolved | Unresolved | Mean decimations | Tie events | Zero-LLR events |
|---|---:|---:|---:|---:|---:|
| `parallel__tie-lowest_index__zero-zero__seed-20260714` | 9 | 8 | 88.82 | 22 | 0 |
| `parallel__tie-highest_index__zero-zero__seed-20260714` | 9 | 8 | 88.82 | 25 | 0 |
| `parallel__tie-seeded_random__zero-zero__seed-1` | 9 | 8 | 88.82 | 23 | 0 |
| `parallel__tie-lowest_index__zero-one__seed-20260714` | 9 | 8 | 88.82 | 22 | 0 |
| `parallel__tie-lowest_index__zero-previous__seed-20260714` | 9 | 8 | 88.82 | 22 | 0 |
| `parallel__tie-lowest_index__zero-seeded_random__seed-1` | 9 | 8 | 88.82 | 22 | 0 |
| `serial__tie-lowest_index__zero-zero__seed-20260714` | 14 | 3 | 74.00 | 34 | 0 |

## Invariant unresolved cases

- `83cc513e8352f861d464fc57dee727be48466bfc45929f6b528cfe5a79fef44a`
- `bcc41e95e64626fa10ec9313a47460542b4edbefd4e1c4f0a2fab42de9caac5a`

## Interpretation rule

A variant is not considered paper-faithful merely because it resolves more failures. Its tie, zero-LLR, and scheduling behavior must be supported by the paper or author code before promotion.
