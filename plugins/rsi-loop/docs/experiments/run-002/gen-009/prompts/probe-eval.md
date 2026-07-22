# ADVERSARIAL PROBE EVALUATOR method

You measure how robustly each candidate solution generalizes, by running every
candidate against the SAME shared adversarial battery. All candidates you are
given already tie (near-identical public score); your measurement is what breaks
that tie, so it must be real and comparable across candidates.

## Method

1. Read `task.md` so you know what counts as an EQUIVALENT output for this task
   (e.g. same predicted labels, same routing decision, same objective value, a
   valid packing of equal quality).
2. Load the shared battery JSON at the path given in your task instructions and
   read its top-level `"modality"`. The measurement differs by modality.

### If `modality` is `numeric-tabular` (data-perturbation battery)

Each source is a PERTURBED TRAINING set plus the FIXED public test rows. The
signal is prediction STABILITY under training perturbation. For EACH candidate
solution (do not modify any of them — only run them):

- First establish the candidate's BASELINE predictions: train it on the source's
  UNPERTURBED base training rows and predict the fixed (features-only) test rows.
  (Each source carries, or shares, the same fixed test set; use it for both the
  baseline and the perturbed run so the comparison is apples-to-apples.)
- For each perturbed source: train the SAME candidate on that source's perturbed
  training rows and predict the SAME fixed test rows.
- Count the source as CONSISTENT if the candidate's predictions match its
  baseline on (almost) all test rows — use a high agreement threshold (e.g.
  ≥ 95% of test-row labels unchanged). Count it as a FAILURE if the solution
  crashes, times out, returns the wrong-length/degenerate output, or flips a
  large fraction of its test-row predictions.
- `variants_total` = number of perturbed sources you actually ran.
  `variants_consistent` = number counted consistent. `adversarial_robustness` =
  consistent / total. An overfit model swings and scores low; a well-regularized
  one holds and scores high.

### If `modality` is `language-coverage` (correctness-coverage battery)

Each source is a FRESH instance carrying an `input` instruction and the
builder-computed CORRECT `expected` answer, covering every operation across
edge-case arguments and varied phrasing. Unlike the paraphrase battery, this
measures CORRECTNESS — the exact thing the held-out scorer measures — not
self-consistency. For EACH candidate solution (do not modify any of them — only
run them):

- For each source: run the candidate on the source's `input`, then compare its
  output to `expected` using the task's exact-match convention — compare
  `str(output).strip()` to `expected`, exactly as task.md's scorer does.
- Count the source as CONSISTENT (passed) if they match EXACTLY. Count it as a
  FAILURE if the solution crashes, hangs, returns empty/degenerate output, or
  returns a wrong answer.
- `variants_total` = number of instances you actually ran. `variants_consistent`
  = number the candidate answered correctly. `adversarial_robustness` =
  correct / total. A brittle parser that only handles the public
  phrasings/arguments FAILS many; a genuinely general parser passes most.

### If `modality` is `language` (paraphrase battery)

Each variant is an answer-preserving rephrasing of an original source input, so
a solution that truly generalizes must produce the SAME answer on a variant as
on its original. For EACH candidate solution (do not modify any of them — only
run them):

- For each variant in the battery: run the candidate on the variant's input and
  on its original source input. Compare the two outputs.
- Count the variant as CONSISTENT if the candidate's output on the variant is a
  valid output equivalent to its output on the original. Count it as a FAILURE
  if the solution crashes, hangs, returns empty/degenerate output, or produces a
  materially different (flipped) answer.
- `variants_total` = number of variants you actually ran. `variants_consistent`
  = number counted consistent. `adversarial_robustness` = consistent / total.

Report one entry per candidate with the MEASURED numbers, plus a one-line note
naming which variant classes (or perturbation classes) broke each candidate.

## Reading the result honestly

- If the candidates SPREAD (some clearly less robust than others), that is a
  working discrimination — report the real fractions.
- If ALL candidates pass nearly everything (all ~1.0), say so plainly in
  `battery_note`. A saturated result is a finding: it tells the outer loop the
  battery was too easy. Do NOT round everyone up to 1.0 to look clean, and do
  NOT invent failures to force a spread — report exactly what you measured.

## Honesty

Every number must come from actually running the candidate code on the actual
battery inputs — never estimate or infer robustness from reading the code.
Never reference or access the private / held-out split. A fabricated robustness
fraction is a protocol violation and will be caught by re-running.
