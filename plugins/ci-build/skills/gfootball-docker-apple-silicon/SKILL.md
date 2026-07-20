---
name: gfootball-docker-apple-silicon
description: |
  Build and run Google Research Football (gfootball 2.10.2) in Docker on Apple Silicon
  (macOS arm64) / Python 3.12, where native pip install fails. Use when: (1) `pip install
  gfootball` fails with "Google Research Football compilation failed", (2)
  "ModuleNotFoundError: No module named 'psutil'" during gfootball's C++ build,
  (3) "ModuleNotFoundError: No module named 'six'" at gfootball import time,
  (4) "ValueError: too many values to unpack (expected 2)" on env.reset(),
  (5) CMake "Compatibility with CMake < 3.5 has been removed" during the build,
  (6) the `cmake` pip package tries to git-clone CMake from github and fails.
  Covers the full ubuntu:24.04 Dockerfile recipe + the gym/six runtime pins.
author: Claude Code
version: 1.0.0
date: 2026-05-31
---

# gfootball in Docker on Apple Silicon

## Problem

gfootball 2.10.2 does **not** build natively on macOS arm64 with Python 3.12. The blocker
is a Boost.Python ABI lock: gfootball's C++ engine needs `libboost_python312`, but Homebrew
only ships `libboost_python314` (built for Python 3.14). There is no prebuilt wheel and no
conda package for osx-arm64. The clean solution is to run it in a Linux Docker container —
but that path has its own chain of non-obvious failures.

## Context / Trigger Conditions

Any of these while trying to get gfootball working:

- Native macOS: `error: Google Research Football compilation failed` → Boost.Python version
  mismatch (libboost_python314 vs the 312 gfootball needs). Don't fight this natively — use Docker.
- In Docker: `ModuleNotFoundError: No module named 'psutil'` during the gfootball wheel build.
- In Docker: `cmake not found. Trying to build using https://github.com/Kitware/CMake.git`
  then `Could not resolve host: github.com`.
- At runtime: `ModuleNotFoundError: No module named 'six'` on `import gfootball`.
- At runtime: `ValueError: too many values to unpack (expected 2)` at `env.reset()`.

## Solution

### Base image: ubuntu:24.04 (NOT python:3.12-slim)

Debian bookworm's apt `libboost-python-dev` is built against Python 3.11, not the slim
image's 3.12 → revives the Boost ABI mismatch. ubuntu:24.04's native `python3` IS 3.12 AND
its apt `libboost-all-dev` ships a matching libboost_python for 3.12. Matching the apt
Boost.Python build to the interpreter version is the whole game.

### apt deps

`build-essential cmake libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev libsdl2-gfx-dev
libboost-all-dev libdirectfb-dev libst-dev mesa-utils` (plus python3-venv).

### The gfootball install — two root causes, one flag

Both the psutil error AND the cmake-git-clone error are the SAME root cause: pip's PEP517
**build isolation** creates a clean env that hides system tools. gfootball's setup.py imports
psutil/numpy at build time (not present in the isolated env), and tries to pip-install the
`cmake` *package* (no aarch64 wheel → falls back to git-cloning CMake, which the build sandbox
can't reach). Fix: pre-install the build deps and disable isolation so the build sees the
system cmake 3.28 + psutil/numpy:

```dockerfile
RUN pip install --upgrade pip setuptools wheel \
    && pip install psutil "numpy>=1.26" \
    && pip install --no-build-isolation gfootball==2.10.2
```

Do NOT pip-install the `cmake` wheel — it's 4.x and would shadow apt cmake 3.28, reviving the
CMake "cmake_minimum_required < 3.5 removed" policy error.

### Two undeclared/mismatched runtime deps

```dockerfile
RUN pip install "gym==0.22.0" six \
    && pip install "fastmcp>=2.0" "anthropic>=0.40" "pygame>=2.6" requests
```

- **`six`**: gfootball does `from six.moves import range/zip` in ~9 modules but omits six from
  install_requires → ModuleNotFoundError at import.
- **`gym==0.22.0`** (this exact version): gfootball declares `gym>=0.11.0` unpinned, so pip
  pulls gym 0.26.x, whose wrapper does `obs, info = env.reset()`. gfootball 2.10.2 returns a
  SINGLE-value reset → `ValueError: too many values to unpack`. gym must be downgraded.
  **0.21.0 does NOT work** — its ancient sdist fails to build on Python 3.12 / modern
  setuptools even with `setuptools<66`. **0.22.0 is the oldest gym that BOTH builds cleanly
  AND keeps gfootball's old single-value reset API.** No `numpy<2` pin needed — 0.22.0 runs
  fine against numpy 2.4.x (the gfootball .so ABI is built against it, so don't downgrade numpy).

### Headless

Set `ENV SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` (or pass `-e`) — no display needed; skips
OpenGL entirely during simulation. The renderer is only for live visual output, which headless
sims don't need.

## Verification

Inside the built image (the real gate — verify by OUTPUT, not exit code):

```bash
docker run --rm -e SDL_VIDEODRIVER=dummy agentic-soccer:latest python -c "
import gfootball.env as fe
env = fe.create_environment(env_name='11_vs_11_stochastic', representation='simple115v2',
    render=False, number_of_left_players_agent_controls=11,
    number_of_right_players_agent_controls=11)
r = env.reset(); print('RESET_OK', type(r).__name__, len(r))   # -> ndarray 22
env.step([0]*22); print('STEP_OK')
"
```

Expect `RESET_OK ndarray 22` and `STEP_OK`. With `simple115v2` + 11+11 agent control, reset
returns a list of 22 obs arrays; raw per-team score is at `env.unwrapped.observation()[0]['score']`
(NOT `info`, which only carries `score_reward` as a scalar delta).

## Notes

- **simple115v2 obs layout** (per the 115-float vector): `[0:22]` left positions, `[22:44]`
  left direction, `[44:66]` right positions, `[66:88]` right direction, `[88:91]` ball xyz.
- **gfootball has no FootballAction enum** — the default action set is module-level
  `action_*` objects; the discrete action space is ints 0–18 (0=idle, 1=left, 2=top_left,
  3=top, 4=top_right, 5=right, 6=bottom_right, 7=bottom, 8=bottom_left, 9..18=pass/shot/sprint…).
- **Verify by real stdout, never exit code.** `docker run` of a *missing* image and various
  build steps can exit 0 or print misleading fragments. A same-tag `docker build` UNTAGS
  `:latest` mid-build, so a concurrent `docker run` reports "No such image" transiently — this
  looks like the image "vanished" but it's just the rebuild. Use only ONE docker actor at a time.
- The gfootball C++ wheel compile is the slow layer (several minutes); once built it Docker-
  layer-caches, so changing the *later* runtime-deps layer (gym/six) rebuilds in seconds.

## References

- gfootball: <https://github.com/google-research/football>
- The Boost.Python ABI / version-coupling is the core reason native arm64 builds fail; Docker
  on a base image whose apt Boost matches the interpreter is the reliable fix.
