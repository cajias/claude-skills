# docker-desktop-stuck-state

Fix Docker Desktop stuck in partial running state on macOS. Use when:
(1) `docker ps` fails with "dial unix ... docker.sock: connect: no such file or directory",
(2) `docker desktop status` says "Could not retrieve status. Is Docker Desktop running?",
(3) `docker desktop start` says "Docker Desktop is already running" but engine won't start,
(4) AppleScript quit or osascript commands timeout with error -1712,
(5) Docker backend process is running but socket doesn't exist at ~/.docker/run/docker.sock.
Covers macOS Docker Desktop recovery when normal restart methods fail.
