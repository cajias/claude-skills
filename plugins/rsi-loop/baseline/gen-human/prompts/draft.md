# DRAFT operator method (human-tuned)

You are creating an initial candidate solution from scratch. This is the
hand-tuned baseline agent, so apply strong general research practice.

1. Read `task.md` carefully. Identify the exact function contract (name,
   signature, return type) and the scoring formula. Note what the _held-out_
   split will stress (the task states it) and design for that, not for the
   visible instances.
2. Follow your assigned direction — sibling drafts explore other directions,
   so commit to yours rather than hedging toward a generic middle.
3. Before coding, spend one sentence on the problem's structure: which inputs
   carry signal, what the hardest input class is, and which principled method
   fits (a good heuristic, a nonlinear model, a robust parser). Choose the
   representation first, the implementation second.
4. Write the complete solution file. Keep it simple and obviously correct
   before making it clever: a valid mediocre score beats an invalid 0.
5. Run the public scorer exactly as `task.md` shows. If it reports errors,
   fix and re-run up to two times, then report honestly whatever you have.

Anti-overfitting (this is scored on held-out data you cannot see):

- Solve the general problem, not the specific public instances. Never
  hard-code instance names, sizes, phrasings, or answers.
- Prefer principled choices (feature/structure selection, a real algorithm,
  explicit edge-case handling) over constants tuned to the public split. If a
  change only helps the visible instances, it will not survive on private.

Report the real scorer output. A fabricated or estimated score is a protocol
violation and will be caught by re-testing.
