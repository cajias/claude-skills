# PR Shepherd

Drives open GitHub pull requests to merged, in any repo.

One cycle per PR: request a Copilot review at the **current** head SHA (a review
at an older SHA is stale), enumerate review threads through the GraphQL
`reviewThreads` API, judge each finding, delegate valid fixes to `@copilot`,
reply **and** `resolveReviewThread` on every thread, drive CI green, evaluate a
human-review gate, merge, then repair the sibling PRs the merge just staled.

The load-bearing idea: a pushed fix does not close a review thread. A watcher
that polls for new commits or new comment timestamps reports a PR as clean while
it is still blocked.

## Requirements

- `gh` authenticated (`gh auth status`) with `repo` scope — enough to merge,
  label, and request a Copilot review (`gh pr edit --add-reviewer Copilot`; the
  request is asynchronous, so it is confirmed on a later cycle by reading
  `/reviews`, never by reading `requested_reviewers` straight back).
- GraphQL access through `gh api graphql`. `gh pr view --comments` does not
  expose thread resolution state; only GraphQL does.
- Optional: the GitHub MCP server, for `update_pull_request_branch`. Its
  `request_copilot_review` returns `404 Not Found` — use the `gh` path above.

## Usage

The skill is user-invoked only (`disable-model-invocation: true`) because it
posts comments, resolves threads, labels, assigns and merges on real PRs. That
invocation is also what authorizes the merge.

```text
/pr-shepherd            # PRs for the current branch / repo
/pr-shepherd 77         # one PR
/loop 10m /pr-shepherd  # unattended, on a cadence
```

Re-assessment is gated on the head SHA, so a cycle where nothing moved costs one
API call per repo.

## Bundled agents

Five agents in [`agents/`](./agents/), one per loop step, each with its model
tier pinned to the consequence of getting that step wrong: `pr-recon` (sonnet),
`pr-thread-triage` (opus), `pr-ci-doctor` (sonnet), `pr-gate-auditor` (opus),
`pr-gate-handoff` (haiku). SKILL.md's "Which agent runs which step" table is the
dispatch map.

## Documentation

[`skills/pr-shepherd/SKILL.md`](./skills/pr-shepherd/SKILL.md) — the full loop,
the GraphQL mutations, the human-review rubric, and the concurrency rules.
