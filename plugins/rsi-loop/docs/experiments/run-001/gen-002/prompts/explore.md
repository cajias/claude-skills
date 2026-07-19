# EXPLORE operator method

You are injecting algorithmic diversity into a stalled search. Every working
node so far belongs to the banned families in your prompt, and they tie on the
public score — another variant of a banned family is a wasted node by
construction. You were deliberately given NO code from existing nodes: design
from the task, not from the incumbent.

1. Read `task.md` and restate to yourself the objective and what structural
   property of a solution the score actually rewards.
2. Pick a family OUTSIDE the banned list. Candidate paradigms to consider
   (generic — adapt to the task):
   - complement/grouping construction: explicitly combine elements that fit
     together tightly (pair large with small, build groups that nearly reach a
     bound), instead of placing elements one-by-one;
   - local-search repacking: take any valid solution, then apply deterministic
     improvement moves (relocate an element, swap two elements across groups,
     dissolve the weakest group and redistribute) until no move helps;
   - exact solving of bounded subproblems: DP, branch-and-bound, or exhaustive
     search over small subsets with strict size/time cutoffs, safe fallback
     elsewhere;
   - multi-start portfolio: run several DIFFERENT deterministic constructions
     (different orderings/rules from different families) and keep the best
     result per instance;
   - problem-specific structure: exploit an invariant of the task the greedy
     family ignores (e.g. exact-fill combinations, residual capacities,
     matching lower bounds).
3. Mechanism check before coding: describe your core loop in one sentence. If
   that sentence is "sort, then place each element by a fixed rule", you are
   about to rebuild a banned family — pick again.
4. Implement it completely and deterministically, with strict time discipline:
   bound any search loops (fixed pass counts, size cutoffs) so no instance can
   time out. A timeout scores 0 and wastes the node.
5. Run the public scorer; if the stress harness exists, run it too. Your
   success criterion is lexicographic: strictly higher public score than the
   incumbent, or equal public score with strictly higher stress score.
6. Report a NEW family label (short kebab-case, not on the banned list) that
   honestly names your mechanism.

Anti-overfitting (this is scored on held-out data you cannot see):

- Solve the general problem, not the specific public instances. Never
  hard-code instance names, sizes, or answers — neither for public instances
  nor for stress instances. Treat the stress suite as a black-box scorer.
- Novelty must come from a genuinely different algorithm, not from tuning
  constants against the visible instances.

Report the real scorer outputs (public and stress), even if they are worse
than the incumbent — an honest weak explorer still teaches the search which
families are dead ends; fabricated scores are a protocol violation caught by
re-testing.
