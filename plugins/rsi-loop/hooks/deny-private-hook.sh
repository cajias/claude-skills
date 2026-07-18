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
case "$IN" in
  *private* | *rsi-runs* | *holdout-tasks* | *tasks* | *score.py* | *sandbox*)
    printf '%s' "$IN" | python3 "$(dirname "$0")/deny-private.py"
    ;;
  *)
    exit 0
    ;;
esac
