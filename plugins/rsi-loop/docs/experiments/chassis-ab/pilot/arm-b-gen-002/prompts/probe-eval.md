# PROBE-EVAL method

You apply ONE fixed, shared probe battery IDENTICALLY to several candidate
solutions and report the REAL measured pass fraction for each. You are a neutral
test driver: you do not author the battery, you do not judge which candidate
"should" win, and you never modify a candidate's solution file.

## Method

1. Confirm the entry function name and signature from `task.md`.
2. Write ONE small standard-library Python driver under the sandbox `nodes/`
   directory (not outside the sandbox). It must:
   - take a solution file path,
   - import that file as a module,
   - for each probe, call `entry(*probe.args)`,
   - compare `str(result).strip()` to the probe's `expected` string,
   - count matches, and treat any exception on a probe as a MISS (not a skip).
3. Run the driver once PER candidate, passing the SAME battery every time. Do
   not add, drop, or alter probes between candidates — identical battery is what
   makes the comparison fair.
4. For each candidate report: `node` id, `n_correct`, `n_total` (= number of
   probes in the battery), and `probe_score = n_correct / n_total`. A candidate
   that crashes on every probe scores 0.

## Integrity

- Apply the SAME battery to every candidate; never tailor probes to a
  candidate or peek at how one is implemented to make it pass.
- The battery is synthesized from the PUBLIC task definition — it is not a
  private/held-out split and must never reference one.
- Report the REAL measured pass counts only — never estimate, round up, or
  fabricate a score. Honest numbers (even all-equal or all-zero) are the
  signal the search needs; a fabricated spread corrupts final selection.
