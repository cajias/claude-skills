# DEBUG operator method

You are fixing a buggy node (score 0, crash, timeout, or invalid output).

1. Reproduce first: run the public scorer on the buggy node's file and read
   the per-instance `error` fields — they name the exact failure.
2. Diagnose the root cause from the error and the code in your history.
   Common causes: wrong function name/signature, invalid output structure,
   constraint violations, unbounded loops (timeout), nondeterminism.
3. Make the minimal fix that addresses the root cause. Do not redesign the
   approach — preserve the node's algorithmic idea; redesigns are the
   IMPROVE operator's job.
4. Re-run the scorer and verify the failure is gone.

Anti-overfitting: fix the bug for all inputs, not just the instance that
exposed it. Never special-case public instance names or sizes.

Report the real scorer output, even if your fix did not work.
