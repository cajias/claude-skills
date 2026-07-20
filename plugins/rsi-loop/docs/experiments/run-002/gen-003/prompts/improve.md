# IMPROVE operator method

You are improving the current best node (best by COMBINED score = public score
discounted by measured robustness). Make its combined score strictly higher.

1. Study the best node's code, its public score, AND its measured robustness
   and `robustness_note`. Read the history of what has already been tried
   (including failed improvements — do not repeat them).
2. Decide where the win is:
   - If public score has clear headroom: pick ONE concrete algorithmic
     improvement (stronger heuristic, better preprocessing/ordering, a
     deterministic local-search pass, or handling a weak input class better).
   - If public score is already high but robustness is low: the win is
     GENERALIZATION. Make the solution handle input variation — parse
     tolerantly, normalize before solving, accept rephrasings / synonyms /
     reordering / formatting differences so the same intent maps to the same
     answer. A high public score with brittle parsing is a red flag, not a win.
   One idea per node.
3. Implement it as a complete new solution file (do not just patch
   cosmetically) and keep it deterministic and fast — a timeout scores 0
   and wastes the node.
4. Run the public scorer and compare against the parent's public score.

## Invariance check (measure `robustness` — required)

Using only the public data, produce equivalent variants of a handful of public
inputs (reorder independent items, change whitespace/casing/formatting,
substitute synonyms or rephrase, add harmless filler) — transformations that do
NOT change the correct answer. Run your new solution on originals and variants.
`robustness` = fraction of variants that stayed valid and consistent with the
original. This is the actual measurement you report; note in `robustness_note`
which variant classes (if any) still break.

Anti-overfitting:

- Improvements must come from a better algorithm or more tolerant, principled
  input handling — never from tuning to the visible instances. Never hard-code
  instance names, sizes, or answers.
- If a change only helps one specific public instance, treat that as a
  red flag and prefer a change that helps a whole input class — or that makes
  the solution robust to how an input is phrased or formatted.

Report the real scorer output and the ACTUALLY MEASURED robustness, even if
worse than the parent — honest regressions are useful search signal; fabricated
gains are a protocol violation caught by re-testing.
