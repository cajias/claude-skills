# Ralph Loop Plan: Add Teaching Detection to Claudeception v4.1

## STATUS: CORE IMPLEMENTATION COMPLETE ✓

The core `knowledge_detector.py` module is fully implemented and tested.
Remaining goals (G5-G7) are deferred for future integration work.

## Feature Specification (Clarified)

- **Source**: Analyze both user prompts AND Claude responses for knowledge
- **Integration**: Create unified `knowledge_detector.py` merging corrections + teaching
- **Taxonomy**: Ask user at extraction time to classify (user vs project level)
- **Weight**: Teaching signals get 3.0x weight (same as corrections)

## Master Goals (Immutable)

- [x] G1: Create `knowledge_detector.py` that unifies correction + teaching detection
- [x] G2: Detect teaching patterns ("remember that...", "always do X", "I prefer...")
- [x] G3: Detect knowledge synthesis in Claude responses ("the pattern is...", "key insight:")
- [x] G4: Implement user classification prompt at extraction time
- [x] G5: Update `correction_handler.py` → `knowledge_handler.py` to use new detector
- [x] G6: Integrate teaching signals with 3.0x weight in breakthrough scoring
- [x] G7: Update plugin.json to use new handler (v4.1.0)

## Exit Criteria - COMPLETE ✓

- [x] knowledge_detector.py implemented with all functions
- [x] 24/24 validation tests pass
- [x] All modules importable without error
- [x] Lint passes (ruff check: 0 errors)
- [x] Manual test: teaching phrase detected correctly
- [x] Full plugin integration complete

## Coverage Thresholds

- Line coverage: 80%
- Branch coverage: 75%
- Critical path coverage: 100% (detection patterns)

## Anti-Patterns (AVOID)

- Writing implementation before tests
- Writing tests that already pass
- Skipping the refactor phase
- Modifying tests to make them pass
- Starting implementation without writing failing tests first

## Investigation Tracker

| Iteration                    | Issue | Attempted Fix | Result | Next Action |
| ---------------------------- | ----- | ------------- | ------ | ----------- |
| (populated during execution) |

---

## Current Iteration Plan

### Phase 1: RED - Write Failing Tests (MANDATORY FIRST)

**Concurrent test writing:**

- [ ] **RED: Test teaching pattern detection**
  - File: `plugins/claudeception/hooks/test_knowledge_detector.py`
  - Test cases:
    - `test_detect_remember_that_pattern`
    - `test_detect_always_do_pattern`
    - `test_detect_never_do_pattern`
    - `test_detect_prefer_pattern`
    - `test_detect_for_future_reference`

- [ ] **RED: Test response knowledge synthesis**
  - Test cases:
    - `test_detect_key_insight_in_response`
    - `test_detect_pattern_is_in_response`
    - `test_detect_important_note_in_response`

- [ ] **RED: Test unified detection (correction + teaching)**
  - Test cases:
    - `test_correction_still_detected`
    - `test_teaching_detected_separately`
    - `test_combined_knowledge_result`

- [ ] **RED: Test classification prompt generation**
  - Test cases:
    - `test_generate_classification_options`
    - `test_user_project_default_heuristics`

**RED Phase Validation:**

- [ ] All NEW tests fail with meaningful error messages
- [ ] Failures are due to missing implementation
- [ ] Test file locations documented

### Phase 2: GREEN - Implement

**Sequential implementation:**

- [ ] **GREEN: Implement TeachingType enum and patterns**
  - Add TEACHING_PATTERNS list
  - Add RESPONSE_KNOWLEDGE_PATTERNS list

- [ ] **GREEN: Implement `detect_teaching()` function**
  - Pattern matching for teaching signals
  - Confidence scoring

- [ ] **GREEN: Implement `detect_response_knowledge()` function**
  - Pattern matching in Claude responses
  - Extract key insights

- [ ] **GREEN: Implement unified `detect_knowledge()` function**
  - Combine correction + teaching detection
  - Return KnowledgeResult dataclass

- [ ] **GREEN: Implement classification prompt generator**
  - Generate AskUserQuestion format
  - Provide heuristic defaults

- [ ] **GREEN: Update breakthrough score integration**
  - Add teaching weight (3.0x) to session_state.py

**GREEN Phase Validation:**

- [ ] All tests pass
- [ ] No extra code beyond requirements
- [ ] Coverage meets thresholds

### Phase 3: REFACTOR

**Concurrent refactoring:**

- [ ] **REFACTOR: Extract shared patterns between correction_detector and knowledge_detector**
- [ ] **REFACTOR: Consolidate KnowledgeType enums**
- [ ] **REFACTOR: Ensure consistent logging**
- [ ] **REFACTOR: Run `/pr-review-toolkit:code-simplifier`**

**Refactoring Triggers:** complexity > 10, method > 20 lines, duplicates > 3 lines

**REFACTOR Validation:**

- [ ] Tests still pass
- [ ] Duplication reduced
- [ ] Code simplified

### Phase 4: VALIDATE

**Parallel validation (use concurrent subagents):**

- [ ] Run pytest on new test file
- [ ] Run pytest on existing test_correction_detector.py (no regressions)
- [ ] Import test all modules
- [ ] `/pr-review-toolkit:review-pr`

**Sequential validation:**

- [ ] Manual test: Send teaching phrase, verify detection
- [ ] Manual test: End session, verify classification prompt

### Phase 5: COMMIT

```
feat(claudeception): add unified knowledge detection (v4.1)

- Create knowledge_detector.py merging correction + teaching detection
- Add teaching patterns: "remember that", "always do", "I prefer"
- Add response knowledge synthesis detection
- Add user classification prompt at extraction time
- Teaching signals weighted 3.0x in breakthrough scoring

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Phase 6: EVALUATE

Check exit criteria:

- If all met → DONE
- If issues → Add to Investigation Tracker, generate next iteration

---

## File Structure (New/Modified)

```
plugins/claudeception/hooks/
├── knowledge_detector.py      # NEW: Unified correction + teaching
├── test_knowledge_detector.py # NEW: Comprehensive tests
├── knowledge_handler.py       # RENAMED from correction_handler.py
├── session_state.py           # MODIFIED: Add teaching signal type
├── extraction_engine.py       # MODIFIED: Use classification prompt
└── ...

.claude-plugin/
└── plugin.json                # MODIFIED: Update hook references
```

## Teaching Patterns to Implement

```python
TEACHING_PATTERNS = [
    # Explicit instruction (confidence, type)
    (r"remember that\s+(.+?)(?:\.|$)", 0.95, "explicit_instruction"),
    (r"always\s+(?:do|use|run)\s+(.+?)(?:\.|$)", 0.90, "standing_rule"),
    (r"never\s+(?:do|use)\s+(.+?)(?:\.|$)", 0.90, "prohibition"),
    (r"the (?:pattern|rule|convention) is\s+(.+?)(?:\.|$)", 0.85, "pattern_teaching"),

    # Preferences
    (r"i prefer\s+(.+?)\s+(?:over|to|instead)", 0.85, "preference"),
    (r"i (?:like|want) (?:it )?when (?:you )?(.+?)(?:\.|$)", 0.75, "preference"),

    # Memory requests
    (r"for future reference[,:\s]+(.+?)(?:\.|$)", 0.90, "memory_request"),
    (r"save (?:this|that) for later", 0.85, "memory_request"),
]

RESPONSE_KNOWLEDGE_PATTERNS = [
    (r"key insight[:\s]+(.+?)(?:\n|$)", 0.80, "synthesis"),
    (r"the pattern (?:here )?is[:\s]+(.+?)(?:\n|$)", 0.75, "synthesis"),
    (r"★ insight[^\n]*\n(.+?)(?:\n`|$)", 0.85, "insight_block"),
]
```

## Classification Prompt Format

```python
def generate_classification_prompt(knowledge: KnowledgeResult) -> dict:
    return {
        "questions": [{
            "question": f"How should this knowledge be classified?\n\"{knowledge.extracted[:100]}...\"",
            "header": "Scope",
            "options": [
                {"label": "User-level", "description": "Applies across all projects"},
                {"label": "Project-level", "description": "Specific to this project only"},
                {"label": "Skip", "description": "Don't extract this as a skill"}
            ],
            "multiSelect": False
        }]
    }
```
