---
name: cc-plugin-cache-multi-version-not-recorded
description: |
  Fix for Claude Code startup warning `Plugin "<name>" not cached at (not
  recorded) — run /plugins to refresh`. Use when: (1) Claude Code prints a
  `plugin-cache-miss` warning whose installPath is the literal string
  `(not recorded)`; (2) `claude plugin list` shows the plugin as installed
  with a valid version, AND
  `~/.claude/plugins/installed_plugins.json` has a real `installPath` for
  it, yet the warning still fires every session; (3) running `/plugins` or
  reinstalling the plugin doesn't clear the warning; (4) the plugin's
  cache directory at
  `~/.claude/plugins/cache/<marketplace>/<plugin>/` contains TWO (or more)
  version subdirectories — typically an old SHA-prefix dir and the
  current one — left over from an in-place marketplace SHA bump.
  Root cause: the Claude Code cache resolver (`fk8` in the binary) skips
  any cache parent whose subdir count `!== 1`, returns null, and the
  install-record fallback emits the warning with the hardcoded sentinel
  `installPath: "(not recorded)"`. The phrase is NOT a missing config
  field — it's a literal string in the error branch. Fix: delete every
  stale version subdir under that plugin so exactly one remains (the one
  recorded in `installed_plugins.json`).
author: Claude Code
version: 1.0.0
date: 2026-05-30
---

# Claude Code plugin cache "(not recorded)" warning

## Problem

Claude Code startup prints, e.g.:

```
Plugin "aws-serverless" not cached at (not recorded) — run /plugins to refresh
```

Running `/plugins` does nothing. Reinstalling the plugin doesn't help.
`claude plugin list` shows the plugin as healthy with a real version.
`~/.claude/plugins/installed_plugins.json` records a correct `installPath`
that physically exists on disk.

The literal phrase `(not recorded)` is misleading — it reads like a
missing/null field in your config, but no config edit will fix it. It's
a hardcoded sentinel string in one specific code branch of the Claude
Code binary.

## Context / Trigger Conditions

ALL of these together strongly point at this failure mode:

1. The error contains the exact string `(not recorded)` as the cache
   path.
2. `~/.claude/plugins/installed_plugins.json` has a non-null
   `installPath` for the named plugin, AND that path exists on disk
   with a `.claude-plugin/plugin.json` inside.
3. Listing the plugin's cache parent shows MORE THAN ONE
   version subdirectory:

   ```
   $ ls ~/.claude/plugins/cache/<marketplace>/<plugin>/
   6cfb70e55aa1-9ac9622d   ← stale
   9d46cc0a092c-9ac9622d   ← current (matches installed_plugins.json)
   ```

4. The plugin's marketplace source is `git-subdir` (i.e. fetched from
   a GitHub repo by SHA, where the SHA can change in place when the
   marketplace publisher updates `marketplace.json`).

The stale dir typically contains only old `.in_use/<pid>` lockfiles
from long-dead Claude Code sessions, no real plugin payload.

## Root Cause

The Claude Code cache resolver `fk8` (visible as a string in the v2.1.x
binary) is roughly:

```js
function fk8(H) {
  for (let _ of wMH()) {                     // iterate cache root candidates
    let q = lq.dirname(HT6(_, H, "_"));      // canonical parent path
    try {
      let K = await J5.readdir(q);
      if (K.length !== 1) continue;          // ← THE TRAP
      let O = lq.join(q, K[0]);
      if ((await J5.readdir(O)).length > 0) return O;
    } catch {}
  }
  return null;
}
```

Then the caller does:

```js
let j = await fk8(K);
if (j) Y = j;
else if (A) return T.push({
  type: "plugin-cache-miss",
  source: K,
  plugin: H.name,
  installPath: "(not recorded)"   // ← hardcoded sentinel
}), null;
else return T.push({ type: "plugin-not-installed", ... }), null;
```

When the cache parent has 2+ subdirs (one current, one orphan from a
prior marketplace SHA), `fk8` skips it (`K.length !== 1`), returns
null. The install record IS present (`A` truthy), so the cache-miss
branch fires with the literal `(not recorded)` as `installPath`.

The error message template "`Plugin X not cached at Y — run /plugins to
refresh`" then renders `Y = "(not recorded)"`, producing the
characteristic warning.

## Solution

1. Identify the current version from `installed_plugins.json`:

   ```bash
   python3 -c "
   import json
   d = json.load(open('/Users/$USER/.claude/plugins/installed_plugins.json'))
   for k, entries in d.get('plugins', {}).items():
       print(k.split('@')[0], '->', entries[0]['version'])
   "
   ```

2. List each plugin's cache parent and find ones with >1 subdir:

   ```bash
   for d in ~/.claude/plugins/cache/*/*/; do
     count=$(ls "$d" | wc -l | tr -d ' ')
     [ "$count" -gt 1 ] && echo "MULTI[$count]: $d -> $(ls "$d")"
   done
   ```

3. For each MULTI entry, the "keep" subdir is the one whose name
   matches the `version` field in `installed_plugins.json`. Delete all
   others:

   ```bash
   rm -rf ~/.claude/plugins/cache/<marketplace>/<plugin>/<stale-subdir>
   ```

4. Restart Claude Code. The warning is gone.

DO NOT delete `installed_plugins.json`, `known_marketplaces.json`, or
the marketplace clones in `~/.claude/plugins/marketplaces/` — those are
healthy and removing them triggers reinstalls.

## Verification

- Re-run the cache-parent scan from step 2. Every plugin should show
  exactly one subdir (no MULTI lines printed).
- Launch a fresh Claude Code session and watch for the
  `plugin-cache-miss` / `(not recorded)` warning. It should not
  reappear.
- `claude plugin list` continues to show the affected plugins as
  installed at the same version.

## Example

Observed on Claude Code 2.1.158 (macOS arm64), 2026-05-30. Four
plugins simultaneously hit this state because their respective
upstream marketplaces (`anthropics/claude-plugins-official`,
`awslabs/agent-plugins`, etc.) had bumped the pinned SHA in
`marketplace.json` in place, and Claude Code's installer had downloaded
the new SHA's payload alongside the old one without garbage-collecting
the prior version.

Stale → current pairs cleaned:

| Plugin                | Keep                     | Delete                   |
|-----------------------|--------------------------|--------------------------|
| `atomic-agents`       | `bb9708ec7c4c`           | `f849087b26bb`           |
| `aws-serverless`      | `9d46cc0a092c-9ac9622d`  | `6cfb70e55aa1-9ac9622d`  |
| `chrome-devtools-mcp` | `2e039c09e1a2`           | `a1612be8e014`           |
| `deploy-on-aws`       | `9d46cc0a092c-efbc3f9b`  | `6cfb70e55aa1-efbc3f9b`  |

Single `rm -rf` of the four stale dirs cleared all four warnings.

## Notes

- Only one of the four plugins printed the warning visibly to the
  user (they noticed `aws-serverless`); the other three were
  silent / not surfaced in the UI but were in the same broken state.
  If you find this for one plugin, scan ALL plugins — likely several
  are affected together.
- The `.in_use/<pid>` files inside cache dirs are not directory
  reference counts; they're per-process touch files left by old
  Claude Code processes and never cleaned up. They're safe to delete
  with the stale dir.
- This is a Claude Code internal-state bug. The garbage-collection
  step should be running on the installer side. If a future Claude
  Code release adds an `installer.gcOldVersions` flag or fixes
  `fk8` to pick the recorded version when multiple are present, this
  skill becomes obsolete — check release notes before assuming this
  fix is still needed on a new CLI version.
- The `fk8` `K.length !== 1` check is consistent with the assumption
  that the cache layer is single-version-per-plugin. Manually adding
  any extra dir under the plugin's cache parent (e.g. for backup,
  staging, testing) will also trip it.

## References

- Source of truth (the only one that exists for this): the strings
  table of the Claude Code binary at
  `/Users/<user>/.local/share/claude/versions/<version>` — search for
  `not cached at`, `not recorded`, and `plugin-cache-miss`.
- Claude Code plugin docs: <https://docs.claude.com/en/docs/claude-code/plugins>
  (note: as of 2026-05, the public docs do not describe the cache
  resolver behavior or the multi-version trap).
