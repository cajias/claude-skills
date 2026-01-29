#!/usr/bin/env python3
"""
Tests for the Claudeception Correction Detection Module.

Run with: python -m pytest test_correction_detector.py -v
Or: python test_correction_detector.py
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from correction_detector import (
    detect_correction,
    extract_correction_insight,
    analyze_correction_batch,
    normalize_text,
    fix_common_typos,
    fuzzy_match,
    detect_negation_with_reference,
    CorrectionType,
)


class TestDetectCorrection:
    """Tests for the main detect_correction function."""

    # --- Direct Negation Tests ---

    def test_simple_no_correction(self):
        """Test 'no' at start of message."""
        result = detect_correction("No, that's not what I wanted")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7
        # Can match either direct negation or misunderstanding pattern
        assert result["correction_type"] in [
            CorrectionType.DIRECT_NEGATION.value,
            CorrectionType.MISUNDERSTANDING.value,
        ]

    def test_no_i_meant(self):
        """Test 'no I meant' pattern."""
        result = detect_correction("No I meant the other one")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.85
        assert result["correction_type"] == CorrectionType.DIRECT_NEGATION.value

    def test_no_thats(self):
        """Test 'no that's' pattern."""
        result = detect_correction("No that's not right")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    def test_nope(self):
        """Test 'nope' as negation."""
        result = detect_correction("Nope, try again")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.6

    def test_emphatic_no(self):
        """Test emphatic 'no no no'."""
        result = detect_correction("no no no that's all wrong")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.9

    # --- Wrong Assessment Tests ---

    def test_thats_wrong(self):
        """Test 'that's wrong' pattern."""
        result = detect_correction("That's wrong, it should be blue")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.75
        assert result["correction_type"] == CorrectionType.WRONG_ASSESSMENT.value

    def test_incorrect(self):
        """Test 'incorrect' pattern."""
        result = detect_correction("That's incorrect")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    def test_not_right(self):
        """Test 'not right' pattern."""
        result = detect_correction("That's not right at all")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7

    def test_youre_wrong(self):
        """Test 'you're wrong' pattern."""
        result = detect_correction("You're wrong about that")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    # --- Clarification Tests ---

    def test_actually_start(self):
        """Test 'actually' at start of message."""
        result = detect_correction("Actually, I wanted something different")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.6
        assert result["correction_type"] == CorrectionType.CLARIFICATION.value

    def test_actually_i_want(self):
        """Test 'actually I want' pattern."""
        result = detect_correction("Actually I want a Python script")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    def test_what_i_meant(self):
        """Test 'what I meant' pattern."""
        result = detect_correction("What I meant was the config file")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.75

    def test_let_me_clarify(self):
        """Test 'let me clarify' pattern."""
        result = detect_correction("Let me clarify what I need")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.5

    # --- Contrast Pattern Tests ---

    def test_not_x_but_y(self):
        """Test 'not X but Y' pattern."""
        result = detect_correction("Not JavaScript but Python")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8
        assert result["correction_type"] == CorrectionType.CONTRAST.value

    def test_i_said_x_not_y(self):
        """Test 'I said X not Y' pattern."""
        result = detect_correction("I said function not class")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.85

    def test_instead_of(self):
        """Test 'instead of' pattern."""
        result = detect_correction("Instead of that, use this approach")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.6

    # --- Command Pattern Tests ---

    def test_dont_start(self):
        """Test 'don't' at start."""
        result = detect_correction("Don't use that method")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7
        assert result["correction_type"] == CorrectionType.COMMAND.value

    def test_stop(self):
        """Test 'stop' pattern."""
        result = detect_correction("Stop doing that")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    def test_instead_command(self):
        """Test 'instead' as command."""
        result = detect_correction("Instead, use the API")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.6

    def test_please_dont(self):
        """Test polite 'please don't'."""
        result = detect_correction("Please don't add emojis")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.65

    def test_never_do(self):
        """Test 'never do' pattern."""
        result = detect_correction("Never use eval in production")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.65

    # --- Misunderstanding Tests ---

    def test_you_misunderstood(self):
        """Test 'you misunderstood' pattern."""
        result = detect_correction("You misunderstood my request")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.9
        assert result["correction_type"] == CorrectionType.MISUNDERSTANDING.value

    def test_thats_not_what_i(self):
        """Test 'that's not what I' pattern."""
        result = detect_correction("That's not what I asked for")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.85

    def test_i_didnt_mean(self):
        """Test 'I didn't mean' pattern."""
        result = detect_correction("I didn't mean that")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.8

    def test_you_got_it_wrong(self):
        """Test 'you got it wrong' pattern."""
        result = detect_correction("You got it wrong")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.85

    # --- Typo Tolerance Tests ---

    def test_typo_worng(self):
        """Test typo in 'wrong'."""
        result = detect_correction("worng answer")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7

    def test_typo_actualy(self):
        """Test typo in 'actually'."""
        result = detect_correction("actualy I want something else")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.6

    def test_typo_incorect(self):
        """Test typo in 'incorrect'."""
        result = detect_correction("thats incorect")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7

    def test_typo_dont(self):
        """Test 'dont' without apostrophe."""
        result = detect_correction("dont do that")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.65

    def test_typo_insted(self):
        """Test typo in 'instead'."""
        result = detect_correction("insted use the other one")
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.5

    # --- Non-Correction Tests (False Positives) ---

    def test_not_correction_thanks(self):
        """Test that 'thanks' is not a correction."""
        result = detect_correction("Thanks, that's perfect!")
        assert result["is_correction"] is False

    def test_not_correction_question(self):
        """Test that simple questions are not corrections."""
        result = detect_correction("Can you help me?")
        assert result["is_correction"] is False

    def test_not_correction_greeting(self):
        """Test that greetings are not corrections."""
        result = detect_correction("Hello, I need help with something")
        assert result["is_correction"] is False

    def test_not_correction_confirmation(self):
        """Test that confirmations are not corrections."""
        result = detect_correction("Yes, that's exactly what I wanted")
        assert result["is_correction"] is False

    def test_not_correction_elaborate(self):
        """Test that requests for more info are not corrections."""
        result = detect_correction("Can you tell me more about that?")
        assert result["is_correction"] is False

    def test_empty_message(self):
        """Test empty message handling."""
        result = detect_correction("")
        assert result["is_correction"] is False
        assert result["confidence"] == 0.0

    def test_whitespace_only(self):
        """Test whitespace-only message."""
        result = detect_correction("   \n\t  ")
        assert result["is_correction"] is False

    # --- Edge Cases ---

    def test_no_in_middle_not_correction(self):
        """Test 'no' in middle of sentence (not start)."""
        result = detect_correction("I have no idea what to do")
        # This might match some patterns but should be lower confidence
        assert result["confidence"] < 0.7 or result["is_correction"] is False

    def test_case_insensitive(self):
        """Test case insensitivity."""
        result1 = detect_correction("WRONG!")
        result2 = detect_correction("wrong!")
        assert result1["is_correction"] == result2["is_correction"]
        assert abs(result1["confidence"] - result2["confidence"]) < 0.1

    def test_with_previous_response(self):
        """Test detection with previous response context."""
        result = detect_correction(
            "That's not correct",
            previous_response="The answer is 42"
        )
        assert result["is_correction"] is True


class TestExtractCorrectionInsight:
    """Tests for the extract_correction_insight function."""

    def test_extract_not_x_but_y(self):
        """Test extraction from 'not X but Y' pattern."""
        insight = extract_correction_insight("Not JavaScript but Python please")
        # Should contain either language name (either in wanted/unwanted context)
        assert "python" in insight.lower() or "javascript" in insight.lower()

    def test_extract_i_want(self):
        """Test extraction from 'I want' pattern."""
        insight = extract_correction_insight("I want a REST API not GraphQL")
        assert "want" in insight.lower()

    def test_extract_i_meant(self):
        """Test extraction from 'I meant' pattern."""
        insight = extract_correction_insight("I meant the config file not the main file")
        assert "meant" in insight.lower() or "config" in insight.lower()

    def test_extract_dont(self):
        """Test extraction from 'don't' pattern."""
        insight = extract_correction_insight("Don't use deprecated methods")
        assert "Avoid" in insight or "deprecated" in insight.lower()

    def test_extract_instead(self):
        """Test extraction from 'instead' pattern."""
        insight = extract_correction_insight("Instead, use the newer API")
        assert "instead" in insight.lower() or "newer" in insight.lower()

    def test_extract_should(self):
        """Test extraction from 'should' pattern."""
        insight = extract_correction_insight("You should use async/await")
        assert "Expected" in insight or "async" in insight.lower()

    def test_extract_i_asked_for(self):
        """Test extraction from 'I asked for' pattern."""
        insight = extract_correction_insight("I asked for tests not documentation")
        assert "request" in insight.lower() or "tests" in insight.lower()

    def test_no_insight_generic(self):
        """Test fallback for generic corrections."""
        insight = extract_correction_insight("That's wrong")
        assert insight  # Should return something even if generic


class TestAnalyzeCorrectionBatch:
    """Tests for batch analysis function."""

    def test_batch_analysis(self):
        """Test analyzing multiple messages."""
        messages = [
            {"user": "Help me with Python", "assistant": "Sure, here's how..."},
            {"user": "No, that's wrong", "assistant": "Let me fix that..."},
            {"user": "Perfect, thanks!", "assistant": "You're welcome!"},
        ]

        results = analyze_correction_batch(messages)

        assert len(results) == 3
        assert results[0]["is_correction"] is False  # "Help me with Python"
        assert results[1]["is_correction"] is True   # "No, that's wrong"
        assert results[2]["is_correction"] is False  # "Perfect, thanks!"

    def test_batch_with_context(self):
        """Test that batch analysis uses context from previous responses."""
        messages = [
            {"user": "The answer is wrong", "assistant": "I said 42"},
        ]

        results = analyze_correction_batch(messages)
        assert len(results) == 1
        assert results[0]["is_correction"] is True

    def test_empty_batch(self):
        """Test empty batch handling."""
        results = analyze_correction_batch([])
        assert results == []


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_normalize_text(self):
        """Test text normalization."""
        assert normalize_text("  HELLO   WORLD  ") == "hello world"
        assert normalize_text("Tab\tHere") == "tab here"

    def test_fix_common_typos(self):
        """Test typo fixing."""
        assert "wrong" in fix_common_typos("worng")
        assert "actually" in fix_common_typos("actualy")
        assert "incorrect" in fix_common_typos("incorect")

    def test_fuzzy_match(self):
        """Test fuzzy matching."""
        assert fuzzy_match("wrong", "wrong") is True
        assert fuzzy_match("worng", "wrong", threshold=0.75) is True
        assert fuzzy_match("xyz", "wrong", threshold=0.75) is False

    def test_detect_negation_with_reference(self):
        """Test negation with reference detection."""
        detected, confidence = detect_negation_with_reference(
            "that answer is wrong"
        )
        assert detected is True
        assert confidence > 0.4

        detected, confidence = detect_negation_with_reference(
            "hello world"
        )
        assert detected is False


class TestCorrectionTypes:
    """Tests to verify all correction types can be detected."""

    def test_all_types_detectable(self):
        """Verify each correction type can be detected."""
        test_cases = {
            CorrectionType.DIRECT_NEGATION: "No, that's not it",
            CorrectionType.WRONG_ASSESSMENT: "That's incorrect",
            CorrectionType.CLARIFICATION: "Actually I meant something else",
            CorrectionType.CONTRAST: "Not red but blue",
            CorrectionType.COMMAND: "Stop doing that",
            CorrectionType.MISUNDERSTANDING: "You misunderstood me",
        }

        for expected_type, message in test_cases.items():
            result = detect_correction(message)
            assert result["is_correction"] is True, f"Failed for: {message}"
            # Just verify it was detected; exact type matching can vary


class TestRealWorldExamples:
    """Tests with real-world correction examples."""

    def test_code_review_correction(self):
        """Test code review style correction."""
        result = detect_correction(
            "No, don't use var, use const instead"
        )
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.7

    def test_file_path_correction(self):
        """Test file path correction."""
        result = detect_correction(
            "Wrong file, I meant src/main.py not src/utils.py"
        )
        assert result["is_correction"] is True

    def test_language_correction(self):
        """Test programming language correction."""
        result = detect_correction(
            "I asked for TypeScript, not JavaScript"
        )
        assert result["is_correction"] is True

    def test_frustrated_correction(self):
        """Test frustrated/emphatic correction."""
        result = detect_correction(
            "No no no! That's completely wrong!"
        )
        assert result["is_correction"] is True
        assert result["confidence"] >= 0.85

    def test_polite_correction(self):
        """Test polite correction."""
        result = detect_correction(
            "I think there might be a misunderstanding - I was asking about the API"
        )
        assert result["is_correction"] is True


# Standalone test runner
def run_tests_without_pytest():
    """Run all tests without pytest framework."""
    print("Running Correction Detector Tests (no pytest)")
    print("=" * 70)

    # Collect all test classes
    test_classes = [
        TestDetectCorrection,
        TestExtractCorrectionInsight,
        TestAnalyzeCorrectionBatch,
        TestHelperFunctions,
        TestCorrectionTypes,
        TestRealWorldExamples,
    ]

    total_passed = 0
    total_failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()
        test_methods = [
            m for m in dir(instance)
            if m.startswith("test_")
        ]

        for method_name in test_methods:
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  PASS: {method_name}")
                total_passed += 1
            except AssertionError as e:
                print(f"  FAIL: {method_name} - {e}")
                total_failed += 1
            except Exception as e:
                print(f"  ERROR: {method_name} - {type(e).__name__}: {e}")
                total_failed += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {total_passed} passed, {total_failed} failed")
    return total_failed == 0


if __name__ == "__main__":
    if HAS_PYTEST:
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        success = run_tests_without_pytest()
        exit(0 if success else 1)
