# DEBUG operator method

You are fixing a buggy node (score 0, crash, timeout, or invalid output).

1. Reproduce first: run the public scorer on the buggy node's file and read
   the per-instance `error` fields — they name the exact failure.
2. Diagnose the root cause from the error and the code in your history.
   Common causes: wrong function name/signature, invalid output structure,
   constraint violations, unbounded loops (timeout), nondeterminism.
3. Make the minimal fix that addresses the root cause. Do not redesign the
   approach — preserve the node's algorithmic idea and its family label; this
   matters doubly when the node is from a rare family (e.g. an explore node):
   a fixed member of a new family is worth more to the search than yet
   another member of a common one. Redesigns are other operators' jobs.
4. Re-run the scorer and verify the failure is gone. If the stress harness
   exists (`nodes/stress/stress_eval.py`), run it too and report its real
   output (0 if it fails).

Anti-overfitting: fix the bug for all inputs, not just the instance that
exposed it. Never special-case public or stress instance names or sizes.

Report the real scorer output, even if your fix did not work, and keep the
node's family label in your structured output.
