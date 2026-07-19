# IMPROVE operator method

You are improving the current best node (best by public score). Make its
public score strictly higher, or — when public score is already saturated —
make the solution GENERALIZE better without giving up any public points.

1. Study the best node's code and public score. Read the history of what has
   already been tried (including failed improvements — do not repeat them).
2. Decide where the win is:
   - If public score has clear headroom: pick ONE concrete algorithmic
     improvement (stronger heuristic, better preprocessing/ordering, a
     deterministic local-search pass, or handling a weak input class better).
   - If public score is already high/saturated: the durable win is
     GENERALIZATION. Make the solution handle input variation — parse
     tolerantly, normalize before solving, accept rephrasings / synonyms /
     reordered clauses / formatting and encoding differences so the same
     intent maps to the same answer. This does NOT lower the public score,
     and it is exactly what the final selection rewards (below).
   One idea per node.
3. Implement it as a complete new solution file (do not just patch
   cosmetically) and keep it deterministic and fast — a timeout scores 0
   and wastes the node.
4. Run the public scorer and compare against the parent's public score.

## How the final winner is chosen (why generalization matters)

After the search, all candidates that TIE on public score are run against a
single SHARED, deliberately hard adversarial battery — synonym substitutions,
re-templated phrasings, different sentence structures, reordered clauses,
filler, alternative equivalent encodings, edge-scale instances. The candidate
that stays correct across the most of that variation is returned. So a
solution that merely maxes the public phrasing loses to one that generalizes.
When public headroom is gone, invest the node in tolerant, principled input
handling.

Anti-overfitting:

- Improvements must come from a better algorithm or more tolerant, principled
  input handling — never from tuning to the visible instances. Never hard-code
  instance names, sizes, or answers.
- If a change only helps one specific public instance, treat that as a red
  flag and prefer a change that helps a whole input class.

Report the real scorer output and compare to the parent, even if worse —
honest regressions are useful search signal; fabricated gains are a protocol
violation caught by re-testing.
