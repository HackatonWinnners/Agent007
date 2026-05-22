---
name: knitting-stitch-math
description: How each stitch operation changes the live stitch count in a row
---
Each stitch operation consumes some live stitches from the previous row and produces some new live stitches. Compiler must simulate this row by row to detect stitch count mismatches.

Per-stitch consume/produce table (CHECK the spec for the canonical set; this matches the public test fixtures):

| op | consumes | produces | net | notes |
|---|---|---|---|---|
| k    | 1 | 1 | 0  | knit |
| p    | 1 | 1 | 0  | purl |
| yo   | 0 | 1 | +1 | yarn over — creates new stitch from nothing |
| k2tog | 2 | 1 | -1 | knit two together — decrease |
| p2tog | 2 | 1 | -1 | purl two together — decrease |
| ssk  | 2 | 1 | -1 | slip slip knit — decrease |
| kfb  | 1 | 2 | +1 | knit front-back — increase |
| pfb  | 1 | 2 | +1 | purl front-back — increase |
| m1   | 0 | 1 | +1 | make one — increase from gap |
| sl   | 1 | 1 | 0  | slip — moves stitch unchanged |
| s    | 1 | 1 | 0  | alias for sl in some specs |

A stitch with a count suffix like `k10` means apply `k` 10 times. So `k10` consumes 10 produces 10. `yo3` consumes 0 produces 3. `k2tog2` consumes 4 produces 2.

A row's `start_stitches` = previous row's `end_stitches` (or `cast_on` for row 1). `end_stitches` = sum of net deltas applied to `start_stitches`. **Total consumed across the row MUST equal `start_stitches`.** If consumed > start → `E_STITCH_OVERFLOW`. If consumed < start → `E_STITCH_UNDERFLOW`.

Brackets and repeats:
- `[k1, p1] x3` expands to `k1, p1, k1, p1, k1, p1` (apply pattern 3 times). Total consumed = 6, produced = 6.
- Nested `[[k1] x2, p1] x3` works inside-out. NOT a parser flatten — each repetition is a separate run of the inner stitches.

`repeat rows N-M xK`: re-runs rows N through M, K times (in addition to the original). The expansion in `expanded_rows` includes all repetitions, each with its own `source_row` (which row from the original) and `expanded_row_index` (which expanded position).
