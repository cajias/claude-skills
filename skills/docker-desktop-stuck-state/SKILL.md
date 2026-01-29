---
name: docker-desktop-stuck-state
description: |
  Fix Docker Desktop stuck in partial running state on macOS. Use when:
  (1) `docker ps` fails with "dial unix ... docker.sock: connect: no such file or directory",
  (2) `docker desktop status` says "Could not retrieve status. Is Docker Desktop running?",
  (3) `docker desktop start` says "Docker Desktop is already running" but engine won't start,
  (4) AppleScript quit or osascript commands timeout with error -1712,
  (5) Docker backend process is running but socket doesn't exist at ~/.docker/run/docker.sock.
  Covers macOS Docker Desktop recovery when normal restart methods fail.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# Docker Desktop Stuck State Recovery

## Problem
Docker Desktop on macOS can enter a stuck state where the backend process is running but
the Docker engine/VM hasn't started. Normal restart methods (quit app, `docker desktop stop`,
AppleScript) all hang or timeout, leaving Docker unusable.

## Context / Trigger Conditions

Any of these symptoms indicate this stuck state:

1. **Socket missing**: `docker ps` or `docker info` fails with:
   ```
   failed to connect to the docker API at unix:///Users/<user>/.docker/run/docker.sock
   dial unix /Users/<user>/.docker/run/docker.sock: connect: no such file or directory
   ```

2. **Status contradiction**:
   - `docker desktop status` → "Could not retrieve status. Is Docker Desktop running?"
   - `docker desktop start` → "Docker Desktop is already running"

3. **Restart methods hang**:
   - `osascript -e 'quit app "Docker"'` → timeout error -1712
   - `open -a Docker` → error -1712 (LSOpenURLsWithCompletionHandler failed)
   - Docker menu bar quit option unresponsive

4. **Process state**:
   - `ps aux | grep docker` shows `com.docker.backend` running
   - `ls ~/.docker/run/` shows empty directory (no `docker.sock`)

## Solution

### Quick Fix (one-liner)

```bash
killall -9 com.docker.backend && sleep 3 && open -a Docker
```

### Step-by-Step

1. **Identify the stuck backend process**:
   ```bash
   ps aux | grep -i docker | grep -v grep
   # Look for: com.docker.backend
   ```

2. **Force kill the backend**:
   ```bash
   killall -9 com.docker.backend
   # OR if you have the PID:
   kill -9 <pid>
   ```

3. **Wait for cleanup**:
   ```bash
   sleep 3
   ```

4. **Relaunch Docker Desktop**:
   ```bash
   open -a Docker
   ```

5. **Wait for engine startup** (~10 seconds):
   ```bash
   sleep 10 && docker ps
   ```

### If Still Stuck

If the above doesn't work, try a complete reset:

```bash
# Kill all Docker processes (vmnetd runs as root, ignore the permission error)
pkill -9 -f "com.docker" 2>/dev/null

# Clear potentially corrupted state
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/

# Restart
open -a Docker
```

## Verification

After recovery, verify Docker is fully operational:

```bash
# Check engine responds
docker info | head -10

# Check containers work
docker ps

# Check socket exists
ls -la ~/.docker/run/docker.sock
```

Expected: All commands succeed, socket file exists.

## Example

```bash
$ docker ps
Cannot connect to the Docker daemon at unix:///Users/user/.docker/run/docker.sock

$ docker desktop status
Could not retrieve status. Is Docker Desktop running?

$ docker desktop start
Docker Desktop is already running

$ killall -9 com.docker.backend && sleep 3 && open -a Docker
[no output = success]

$ sleep 10 && docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

## Notes

- The `vmnetd` process runs as root and cannot be killed by regular users—this is normal
  and doesn't affect the fix
- Error -1712 is an AppleEvent timeout, indicating the app isn't responding to messages
- The socket location `~/.docker/run/docker.sock` is the default for Docker Desktop on macOS;
  some configurations may use `/var/run/docker.sock` symlinked to this location
- If this happens frequently, check Docker Desktop logs at:
  `~/Library/Containers/com.docker.docker/Data/log/host/docker-desktop.log`
- AutoStart being false in settings (at `~/Library/Group Containers/group.com.docker/settings-store.json`)
  means Docker won't start the engine automatically on launch

## See Also

- cdk-temp-folder-disk-bloat (Docker can accumulate disk space issues)
