---
name: mutation-verify-render-tests
description: |
  Verify that "scene-capture" / pixel-analysis tests for a graphical renderer (pygame,
  canvas, matplotlib, headless GL, screenshot-diff) actually CATCH a broken render —
  by mutation testing. Use when: (1) you've written or received tests that render a
  frame headlessly and assert properties of the pixels (e.g. "pitch is green", "HUD
  present", "sprites on screen"); (2) an agent reports "N scene tests passing" and you
  need to know if they're REAL or hollow; (3) a pixel/region assertion passes but you
  suspect it's satisfied by the wrong pixels (background, anti-aliasing, adjacent UI);
  (4) before trusting any image-correctness test as a guard. The core technique:
  temporarily break the renderer (stub the draw call) and confirm the test FAILS; then
  restore and confirm it PASSES. A scene test that passes when the thing it checks is
  removed is worthless.
author: Claude Code
version: 1.0.0
date: 2026-06-01
---

# Mutation-Verify Render / Scene-Capture Tests

## Problem

Tests that render a graphical frame and assert properties of the resulting pixels are
easy to write so loosely that they pass no matter what. A green suite of "scene-capture"
tests gives false confidence: the assertion may be satisfied by background pixels, UI
chrome, anti-aliased line art, or an adjacent element — not the thing it claims to check.

A real example: a test asserted "goal nets are present" by counting white/grey pixels in
a screen region. It PASSED even after both `_draw_goal_net()` calls were stubbed out —
because the region also contained the pitch's white boundary lines, which satisfied the
count. The test verified nothing.

## Context / Trigger Conditions

- You have (or were handed) tests that do: render frame headlessly → read pixels
  (`surface.get_at`, `pygame.surfarray`, `np` on a screenshot) → assert color/region/cluster
  properties.
- An agent claims "all scene tests pass" and you're about to trust them as a guard.
- A pixel-region assertion passes but the region overlaps other elements (lines, HUD,
  background) that could satisfy it independently of the feature under test.

## Solution: mutation test every scene assertion

For each scene-capture test, prove it is REAL by breaking the renderer and confirming the
test goes RED, then restoring and confirming GREEN. A test that can't fail isn't testing.

```bash
# 1. Back up the renderer (NOT the test).
cp path/to/renderer.py /tmp/r_backup.py

# 2. Stub the draw call for the feature the test checks (make it draw nothing).
#    e.g. replace the helper invocation with `pass` / early return:
sed -i '' 's/        draw_goal_net(surface, sign)/        pass/' path/to/renderer.py

# 3. Run JUST that test — it MUST FAIL now.
uv run --no-sync pytest tests/test_scene.py::test_goal_nets -q   # expect: 1 failed

# 4. Restore and confirm byte-identical + test passes again.
cp /tmp/r_backup.py path/to/renderer.py
diff -q path/to/renderer.py /tmp/r_backup.py   # must be identical
uv run --no-sync pytest tests/test_scene.py::test_goal_nets -q   # expect: 1 passed
```

Repeat for each feature: stub `draw_players` → player/cluster/perspective tests must fail;
stub `draw_hud` → HUD test must fail; recolor the pitch constant → pitch-green test must
fail; etc. Any test that stays GREEN through its mutation is a false positive — fix it.

### How to FIX a false-positive scene test

1. **Tighten the sampled region** to JUST the feature's screen area, excluding overlapping
   elements (boundary lines, HUD, adjacent sprites).
2. **Use a feature-specific color predicate**, not "any white/bright". The example fix
   distinguished the net mesh (`NET_GREY ~(206,214,224)`: light, slightly blue, *dimmer*
   than pure-white 238 lines) from the pitch lines via a range predicate `is_net_mesh`,
   so the white boundary lines no longer satisfied it.
3. **Require a meaningful count/density**, with a margin well below the real value but
   well above incidental noise (real net ≈1500 px → require ≥600; bare region ≈0).
4. Re-run the mutation proof until RED-when-stubbed / GREEN-when-restored holds.

## Verification

The acceptance criterion for any scene-capture test is the pair:

- **RED** when the feature's draw call is stubbed out.
- **GREEN** when restored (and the renderer is confirmed byte-identical to before).

Do this yourself — do not accept an agent's "it passes". Passing is half the proof;
failing-when-it-should is the other half.

## Notes

- Tolerate anti-aliasing/shading with color **ranges/predicates**, never exact RGB equality.
- 3-tone shaded sprites split into multiple connected components per sprite — cluster-count
  assertions should be "≥ a few", not "== N", unless you control sprite flatness.
- Scope player/cluster checks to the pitch band (above the HUD) so team-colored HUD digits
  aren't miscounted as players — that overlap is itself a common false-positive source.
- Stub via `sed` on the call site (fast, reversible) rather than editing logic; always
  `diff -q` against the backup after restoring so a mutation never leaks into a commit.
- This generalizes beyond pygame: any render-to-buffer-then-assert-pixels test (Playwright
  screenshots, matplotlib `savefig` + array asserts, headless WebGL) should be mutation-verified.

## References

- Mutation testing principle: a test suite's value is measured by the faults it detects,
  not the lines it covers. Here applied manually, per-feature, to image assertions.
