# tdd-context-compaction-resilience

Fix TDD workflow state loss during Claude Code context compaction. Use when:
(1) Agent forgets which TDD phase (RED/GREEN/REFACTOR) it's in after long sessions,
(2) Agent repeats exploration/investigation work it already did,
(3) Ralph-loop iterations lose track of failed approaches,
(4) Scratchpad exists but agent still loses TDD discipline,
(5) User has to remind agent "you already tried that" or "write tests first".
Covers structured state persistence, investigation tracking, and compaction-resistant markers.
