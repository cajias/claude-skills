# DRAFT operator method

You are creating an initial candidate solution from scratch, committed to ONE
assigned algorithm family.

1. Read `task.md` carefully. Identify the exact function contract (name,
   signature, return type) and the scoring formula.
2. Follow your assigned family faithfully — sibling drafts hold the other
   families, so the population only has value if each draft is genuinely
   different. Judge your own plan by mechanism, not by name: if it amounts to
   "order the elements once, then place each into an open slot by a fixed
   rule", it is sorted-greedy regardless of what you call it. If that is not
   your assigned family, redesign before writing code.
3. Write the complete solution file. Keep it simple and obviously correct
   before making it clever: a valid mediocre score beats an invalid 0. But do
   not "simplify" your way into a different family — a modest, valid member of
   your assigned family is exactly what the search needs from you.
4. Run the public scorer exactly as `task.md` shows. If it reports errors,
   you may fix and re-run up to two times, then report honestly whatever you
   have.
5. Report your family label (short kebab-case, matching your assigned family)
   in the structured output.

Anti-overfitting (this is scored on held-out data you cannot see):

- Solve the general problem, not the specific public instances. Never
  hard-code instance names, sizes, or answers.
- Do not tune magic constants against the public split; prefer principled
  heuristics that work at any input size.

Report the real scorer output. A fabricated or estimated score is a
protocol violation and will be caught by re-testing.
