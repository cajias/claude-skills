# milestone-goal-prompt

Research a GitHub/GitLab milestone's open issues and print a copy-paste autonomous-loop prompt that
drives the milestone to completion. Use when asked to "generate a goal prompt", "milestone loop
prompt", or a "prompt to finish the milestone". Encodes BDD scenarios, an adversarial gap-check, a
per-iteration Definition-of-Done gate (build + tests + zero lint + code review + security audit),
specialized-agent selection with model tier scaled to complexity, and a root-cause hardening loop
closed out each iteration by a `/claude-code-setup:claude-automation-recommender` cross-check.
The deliverable is the prompt itself — the skill never runs the loop.
