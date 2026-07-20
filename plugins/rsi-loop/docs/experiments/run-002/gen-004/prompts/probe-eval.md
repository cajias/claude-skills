# ADVERSARIAL PROBE EVALUATOR method

You measure how robustly each candidate solution generalizes, by running every
candidate against the SAME shared adversarial battery. All candidates you are
given already tie (near-identical public score); your measurement is what breaks
that tie, so it must be real and comparable across candidates.

## Method

1. Read `task.md` so you know what counts as an EQUIVALENT output for this task
   (e.g. same predicted label, same routing decision, same objective value, a
   valid packing of equal quality). The battery's variants are answer-preserving,
   so a solution that truly generalizes must produce the SAME answer on a variant
   as on that variant's original source input.
2. Load the shared battery JSON at the path given in your task instructions.
3. For EACH candidate solution (do not modify any of them — only run them):
   - For each variant in the battery: run the candidate on the variant's input
     and on its original source input. Compare the two outputs.
   - Count the variant as CONSISTENT if the candidate's output on the variant is
     a valid output equivalent to its output on the original. Count it as a
     FAILURE if the solution crashes, hangs, returns empty/degenerate output, or
     produces a materially different (flipped) answer.
   - `variants_total` = number of variants you actually ran. `variants_consistent`
     = number counted consistent. `adversarial_robustness` = consistent / total.
4. Report one entry per candidate with the MEASURED numbers, plus a one-line
   note naming which variant classes broke each candidate.

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
