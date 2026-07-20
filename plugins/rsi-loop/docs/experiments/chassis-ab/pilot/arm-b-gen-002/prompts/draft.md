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

Anti-overfitting (this is scored on held-out data you cannot see):

- Solve the general problem, not the specific public instances. Never
  hard-code instance names, sizes, or answers.
- Do not tune magic constants against the public split; prefer principled
  heuristics that work at any input size.

Report the real scorer output. A fabricated or estimated score is a
protocol violation and will be caught by re-testing.
