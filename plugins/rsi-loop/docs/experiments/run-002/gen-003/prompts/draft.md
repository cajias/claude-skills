# DRAFT operator method

You are creating an initial candidate solution from scratch.

1. Read `task.md` carefully. Identify the exact function contract (name,
   signature, return type) and the scoring formula.
2. Follow your assigned direction — sibling drafts explore other directions,
   so do not hedge toward a generic approach.
3. Write the complete solution file. Keep it simple and obviously correct
   before making it clever: a valid mediocre score beats an invalid 0.
4. Run the public scorer exactly as `task.md` shows. If it reports errors,
   you may fix and re-run up to two times, then report honestly whatever you
   have.

## Invariance check (measure `robustness` — required)

Your solution is graded on held-out data you cannot see, and that held-out
data may express the SAME inputs in different surface forms. A solution that
only works on the exact public phrasing/format will collapse. So measure how
stable your solution is to equivalent variation, using only the public data:

1. Take a handful of the public inputs. Programmatically produce "equivalent"
   variants of each — transformations that a human would agree do NOT change
   the correct answer. Depending on the task these may include: reordering
   independent items, changing whitespace/casing/formatting, substituting
   synonyms or rephrasing instructions, adding harmless filler, or relabeling.
   Do NOT change anything that would legitimately change the answer.
2. Run your solution on both the original and each variant.
3. `robustness` = the fraction of variants for which the solution still
   produced a valid, non-degenerate output consistent with the original
   (e.g. did not return empty, crash, or flip to a clearly wrong result).
4. Report that measured fraction. If a whole class of variants breaks the
   solution, that is exactly the signal to note in `robustness_note` — and
   prefer to fix it now by parsing/normalizing the input more tolerantly.

Anti-overfitting:

- Solve the general problem, not the specific public instances. Never
  hard-code instance names, sizes, or answers.
- Do not tune magic constants against the public split; prefer principled
  heuristics that work at any input size.
- Robustness comes from tolerant, normalized input handling and principled
  logic — not from memorizing the public phrasing.

Report the real scorer output and the ACTUALLY MEASURED robustness. A
fabricated or estimated score or robustness is a protocol violation and will
be caught by re-testing.
