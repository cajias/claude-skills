# IMPROVE operator method

You are improving the current best node — it works; make it better. "Better"
is lexicographic: a strictly higher public score wins outright; an equal
public score with a strictly higher stress score also counts as progress.

1. Study the best node's code, its family, and both its scores, plus the
   history of what has already been tried (including failed improvements —
   do not repeat them). If several past improvements tied the parent's public
   score, the public split is saturated: stop micro-tuning the same idea and
   target the stress signal with a change that helps a broader input class.
2. Pick ONE concrete improvement with a clear mechanism: a stronger
   heuristic, better preprocessing/ordering, a deterministic local-search
   pass, or handling a weak input class better (e.g. larger inputs, or value
   distributions unlike the easy uniform case). One idea per node.
3. Implement it as a complete new solution file (do not just patch
   cosmetically) and keep it deterministic and fast — a timeout scores 0
   and wastes the node.
4. Run the public scorer and compare against the parent's public score.
5. If the stress harness exists (`nodes/stress/stress_eval.py`), run it on
   your new solution and compare against the parent's stress score. The
   stress suite is a deterministic synthetic tie-breaker built from the task
   definition: it rewards genuine generalization that the small public split
   cannot measure. Do not read the stress instances to special-case them —
   treat the suite as a black-box scorer, exactly like the public scorer.
6. Report the parent's family label unchanged unless your improvement
   fundamentally replaced the core mechanism — in that case report the label
   of what you actually built.

Anti-overfitting (this is scored on held-out data you cannot see):

- Improvements must come from a better algorithm, not from tuning to the
  visible instances. Never hard-code instance names, sizes, or answers —
  neither for public instances nor for stress instances.
- If a change only helps one specific instance, treat that as a red flag
  and prefer a change that helps a whole input class.

Report the real scorer outputs (public and stress), even if they are worse
than the parent — honest regressions are useful search signal; fabricated
gains are a protocol violation caught by re-testing.
