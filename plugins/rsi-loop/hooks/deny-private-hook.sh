#!/usr/bin/env sh
# Cheap pre-filter in front of deny-private.py.
#
# The PreToolUse matcher is `*`, so this runs on EVERY tool call in a session
# where the plugin is enabled. Spawning python3 each time (~30-50ms) on the
# overwhelmingly common clean payload is pure tax. This POSIX-sh guard reads
# the payload once and only invokes the Python firewall when the payload
# mentions something the firewall could possibly act on. The trigger set is a
# strict superset of every path/flag deny-private.py inspects, so a payload
# that skips python here would have been allowed there anyway.
IN=$(cat)
# Trigger set is a strict SUPERSET of everything deny-private.py can act on.
# Besides the protected-tree tokens, route every recursive-read tool (Grep/Glob)
# and recursive-read shell command (grep/rg/ag) plus any `rsi-loop`-rooted path
# to python, since the ancestor-recursion rule can deny those even when the
# payload names no `private`/`tasks` path. Over-triggering only costs a python
# spawn on a clean payload; under-triggering would silently disable the firewall.
case "$IN" in
  *private* | *rsi-runs* | *holdout-tasks* | *tasks* | *score.py* | *sandbox* \
  | *rsi-loop* | *Grep* | *Glob* | *grep* | *rg\ * | *ag\ *)
    printf '%s' "$IN" | python3 "$(dirname "$0")/deny-private.py"
    ;;
  *)
    exit 0
    ;;
esac
