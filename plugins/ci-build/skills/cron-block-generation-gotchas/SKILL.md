---
name: cron-block-generation-gotchas
description: |
  Guide for writing or debugging code that programmatically generates cron
  blocks (crontab entries). Use when: (1) a cron job runs fine by hand but
  silently never fires from cron, (2) writing an `enable`/`install`-style
  command that appends entries to a user's crontab, (3) cron jobs referring
  to paths under `~/Documents/...` or `~/Library/...` that contain spaces,
  (4) cron jobs invoking tools installed to `~/.local/bin`, `~/.cargo/bin`,
  `~/go/bin`, or a uv/pipx/npm user-install dir, (5) debugging "works in my
  shell, broken from cron" with no error output. Covers the two interacting
  gotchas — unquoted-space shell splitting and cron's stripped $PATH — plus
  how to reproduce cron's environment locally with `env -i` and how to
  generate a correct block with `shlex.quote()` and `shutil.which()`.
author: Claude Code
version: 1.0.0
date: 2026-04-15
---

# Cron Block Generation Gotchas

## Problem

A tool's "install maintenance cron jobs" command writes entries into the user's
crontab, reports success, and `crontab -l` shows the block — but nothing
actually runs on schedule. No error email arrives. A "status" check that greps
for the job keywords reports `enabled`. The job works when you run the
command by hand in your shell.

Two orthogonal cron gotchas commonly combine to produce this silent failure:

1. **Shell word-splitting of unquoted paths.** `cd /Users/me/Obsidian Vault/wiki
   && kb index` — the shell hands `cd` two arguments (`/Users/me/Obsidian` and
   `Vault/wiki`); `cd` uses only the first; it fails with `No such file or
   directory`; the `&&`-chain short-circuits; `kb` never runs.
2. **cron's stripped `$PATH`.** cron invokes commands via `/bin/sh -c` with
   `PATH=/usr/bin:/bin` (or similar minimal default — not your login shell's
   PATH). Tools installed to `~/.local/bin`, `~/.cargo/bin`, `~/go/bin`,
   `~/.local/share/uv/tools/*/bin`, or Homebrew's `/opt/homebrew/bin` are
   invisible.

Both failures are silent by default because cron's only feedback channel is
local mail (`/var/mail/$USER`) that most users never read.

## Context / Trigger Conditions

Use this skill when any of these are true:

- You are **writing** code (any language) that emits cron entries referencing a
  user-provided path or a user-installed binary.
- You are **debugging** a cron job that won't fire, and:
  - `crontab -l` shows the entry
  - Running the command by hand in your terminal works
  - There's no visible error output anywhere
  - The path contains spaces, OR the command is not a system binary (not in
    `/usr/bin`, `/bin`, `/sbin`)
- You are **reviewing** a PR that adds a cron installer and want to check
  whether it handles these cases.
- You see messages like `/bin/sh: cd: /Users/…/Obsidian: No such file or
  directory` in `/var/mail/$USER` or `log stream --predicate 'process == "cron"'`.

## Solution

### If you're generating cron blocks programmatically

**Rule 1: Shell-quote every path you interpolate.**

Don't wrap in f-string double quotes — use the language's shell-quoting
primitive. In Python:

```python
import shlex

quoted_root = shlex.quote(root)        # handles spaces, apostrophes, $, `, etc.
cron_line = f"0 2 * * * cd {quoted_root} && kb index --incremental"
```

Wrong: `f"cd \"{root}\" && ..."`  — breaks on paths containing `"` or `$`.

**Rule 2: Detect the tool's install dir and put it in the block.**

Don't assume `~/.local/bin` — the tool might be installed via Homebrew, pipx,
uv, a venv, or a vendored path. Detect at install-time:

```python
import shutil
from pathlib import Path

bin_dir = str(Path(shutil.which("my-tool") or "").parent) or "/usr/local/bin"
cron_path = f"{bin_dir}:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
block = f"""# My-tool maintenance
PATH={cron_path}
0 2 * * * cd {quoted_root} && my-tool index
"""
```

In crontab syntax, a line of the form `VAR=value` (no spaces around `=`, must
appear before the schedule entries it applies to) sets the environment for
subsequent entries. This is cron-specific — it is NOT shell syntax.

**Rule 3: Make the block's removal logic tolerate the format evolution.**

If you ever add the `PATH=` line later (or change the schedule format), your
`disable`/`uninstall` code must recognize BOTH the legacy and new forms, or
upgraded users end up with orphaned lines. Recognize `# HEADER`, then strip
every subsequent line that starts with `0`, `*`, `PATH=`, or is blank,
stopping at the first line that doesn't match.

### If you're debugging a silent cron failure

**Step 1: Reproduce cron's environment in your terminal.**

```bash
env -i HOME="$HOME" PATH="/usr/bin:/bin" bash -c '<your cron command line>'
```

`env -i` wipes every inherited env var. Re-inject only `HOME` and the minimal
`PATH` cron uses. If your command succeeds here, it'll succeed in cron. If it
fails, you see the real error directly.

**Step 2: Test cron's quoting independently from cron's PATH.**

Write the literal crontab command line to a file, then run it:

```bash
cat > /tmp/crontest.sh <<'EOF'
cd /path/with spaces/here && pwd
EOF
bash /tmp/crontest.sh
# → bash: cd: /path/with: No such file or directory  ← the quoting bug
```

**Step 3: Find the actual error when cron runs the job.**

- **Linux**: `grep CRON /var/log/syslog` (or `journalctl -u cron`)
- **macOS**: `log stream --predicate 'process == "cron"'` (live) or
  `log show --predicate 'process == "cron"' --last 1h`
- **Any**: `cat /var/mail/$USER` — cron emails command output (stdout+stderr)
  to the job owner by default

**Step 4: Check whether the status/health check actually runs the job.**

Many tools' `status` commands only grep the crontab for job keywords, so they
report `enabled` even when the job is broken. A real health check runs the
command in cron's reduced environment (Step 1).

## Verification

After applying the fix, verify all three of:

1. **Command works under cron's reduced env** (proves the *command line*):

   ```bash
   env -i HOME="$HOME" PATH="/usr/bin:/bin" bash -c '<your cron command>'
   ```

   Should exit 0 and produce the expected output.

2. **Crontab round-trips byte-identical** (proves cron doesn't mangle the
   block):

   ```bash
   crontab -l > /tmp/before && crontab /tmp/before && diff <(crontab -l) /tmp/before
   ```

   Should produce no output.

3. **Sentinel test** (proves the cron *daemon* actually runs it, including
   FDA/TCC on macOS). This is the only test that catches silent FDA-denied
   failures, because the daemon swallows stderr to `/var/mail/$USER` by
   default and many macs have mail delivery disabled:

   ```bash
   SENTINEL="<path inside FDA-gated dir, e.g. ~/Documents/foo/.cron_test>"
   rm -f "$SENTINEL"
   ( crontab -l; echo "* * * * * date > '$SENTINEL'" ) | crontab -
   # wait past the next minute boundary (60-90s)
   sleep 80
   [ -f "$SENTINEL" ] && echo "WORKS: $(cat "$SENTINEL")" || echo "BROKEN"
   # clean up
   crontab -l | grep -v "$SENTINEL" | crontab -
   rm -f "$SENTINEL"
   ```

   If `SENTINEL` appears with a timestamp matching the next minute
   boundary, the daemon works end-to-end. If missing, FDA is the most
   likely culprit on macOS (check System Settings → Privacy & Security →
   Full Disk Access for `/usr/sbin/cron`).

The `env -i` test (1) and sentinel test (3) are complementary — (1)
isolates *command* problems (quoting, PATH), (3) isolates *daemon*
problems (FDA, launchd state, crontab parse errors). Run both when
debugging.

## Example

**Bad cron block** (what a naive generator emits):

```cron
# Wiki maintenance
0 2 * * * cd /Users/me/Obsidian Vault/wiki && kb index
```

Failure mode under cron:

- `cd` gets two args, uses `/Users/me/Obsidian`, fails
- Even if cd worked, `kb` at `~/.local/bin/kb` is not on PATH
- cron emails the error; user never sees it; `kb` never indexes; the wiki
  silently goes stale for months

**Good cron block**:

```cron
# Wiki maintenance
PATH=/Users/me/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
0 2 * * * cd '/Users/me/Obsidian Vault/wiki' && kb index
```

Why it works:

- `cd` receives a single quoted argument; the space is literal, the path
  resolves, the `&&` proceeds
- `PATH=` line (cron-syntax env var) prepends the install dir, so `kb`
  resolves without a full path
- If the user moves their `kb` install, re-running the generator picks up
  the new location via `shutil.which()`

**Python generator** (the fix pattern, condensed):

```python
import shlex, shutil
from pathlib import Path

def cron_block(root: str, header: str, jobs: list[str]) -> str:
    quoted = shlex.quote(root)
    kb_path = shutil.which("kb")
    bin_dir = str(Path(kb_path).parent) if kb_path else ""
    path_dirs = [d for d in [bin_dir,
                             "/usr/local/bin",
                             "/opt/homebrew/bin",
                             "/usr/bin", "/bin"] if d]
    lines = [header, "PATH=" + ":".join(path_dirs)]
    for tmpl in jobs:                  # jobs contain "{root}" placeholders
        lines.append(tmpl.format(root=quoted))
    return "\n".join(lines)
```

## Notes

- **macOS Full Disk Access**: On macOS, `cron` and `crontab` require FDA to
  access `~/Documents`, `~/Desktop`, and iCloud-synced folders. Even a
  perfectly-quoted, PATH-corrected block will fail if `cron` (binary at
  `/usr/sbin/cron`) isn't in System Settings → Privacy → Full Disk Access.
  Symptom: `Operation not permitted` in `log show --predicate 'process == "cron"' --last 8h`.

  **`crontab` ≠ `cron` — FDA is per-binary.** Users who ran `kb maintenance
  enable` (or any `crontab -e`/`crontab -l`) may see `crontab` already listed
  in FDA because the CLI got auto-prompted when it tried to read user files.
  That grant applies to **`/usr/bin/crontab`** (the editor), not to
  **`/usr/sbin/cron`** (the daemon that actually runs jobs at the scheduled
  times). You need both entries in the FDA list for scheduled jobs under
  `~/Documents` etc. to execute. If only `crontab` is listed, the schedule
  installs fine but never fires.

  **How to add `/usr/sbin/cron` to FDA** (cannot be fully automated — Apple
  requires GUI consent for TCC grants; `tccutil` only has `reset`, not `add`):
  1. `open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`
     — deep-link straight to the FDA pane
  2. Click **+**, then in the file picker press **⌘⇧G** (Go to Folder),
     because `/usr/sbin` is hidden in Finder by default
  3. Type `/usr/sbin/cron`, Enter, Open — a "cron" row appears with the toggle on
  4. No reboot needed; next cron tick picks it up
  5. Verify by waiting for the next scheduled run and checking
     `log show --predicate 'process == "cron"' --last 1h --style compact` for a
     clean invocation (no permission-denied errors)

  Same procedure applies to any system binary needing FDA (launchd agents
  running non-app binaries, custom schedulers, dtrace tools). The `⌘⇧G`
  trick is the key — without it the file picker won't let you select
  anything under `/usr/`, `/System/`, `/private/`, etc.
- **Prefer absolute binary paths when portability matters more than
  discoverability**. Embedding `/Users/me/.local/bin/kb` in the cron line
  avoids the PATH question entirely but breaks if the binary is reinstalled
  elsewhere. The `PATH=` approach is more resilient.
- **`launchd` is macOS-native** and bypasses both gotchas (plist fields are
  XML strings, no shell splitting; `EnvironmentVariables` dict sets PATH
  directly). For macOS-only tools, consider `launchd` over `cron`.
- **The status check anti-pattern**: if your tool has a `status` subcommand
  that only greps the crontab, document that it doesn't prove the job runs —
  or make it actually dry-run the command in a cron-like env.
- **`shlex.quote()` returns single-quoted output** on POSIX shells. Paths
  with embedded `'` become `'part1'"'"'part2'` — ugly but POSIX-safe. Don't
  "clean up" this output.

## References

- [POSIX cron specification](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/crontab.html) — crontab file format, env-var lines
- [Python `shlex.quote()`](https://docs.python.org/3/library/shlex.html#shlex.quote) — shell-safe quoting
- [Python `shutil.which()`](https://docs.python.org/3/library/shutil.html#shutil.which) — cross-platform binary discovery
- [macOS cron and Full Disk Access](https://apple.stackexchange.com/questions/378553/cron-permission-denied-in-macos-catalina) — why cron silently fails on `~/Documents`
- Reference fix in the wild: cajias/second-brain-plugins#1 — exact patch for a real karpathy-llm-wiki plugin bug matching this pattern.
