# IMPROVE operator method

You are improving the current best node — it works; make it score higher.

1. Study the best node's code and score, and the history of what has
   already been tried (including failed improvements — do not repeat them).
2. Pick ONE concrete improvement with a clear mechanism: a stronger
   heuristic, better preprocessing/ordering, a deterministic local-search
   pass, or handling a weak input class better. One idea per node.
3. Implement it as a complete new solution file (do not just patch
   cosmetically) and keep it deterministic and fast — a timeout scores 0
   and wastes the node.
4. Run the public scorer and compare against the parent's score.

Anti-overfitting (this is scored on held-out data you cannot see):

- Improvements must come from a better algorithm, not from tuning to the
  visible instances. Never hard-code instance names, sizes, or answers.
- If a change only helps one specific public instance, treat that as a
  red flag and prefer a change that helps a whole input class.

Report the real scorer output, even if it is worse than the parent —
honest regressions are useful search signal; fabricated gains are a
protocol violation caught by re-testing.
