#!/usr/bin/env python3
"""Claudeception v4.0 - Skill Taxonomy Classifier.

Classifies skills as user-level or project-level based on content analysis.

Decision Tree:
1. Contains project identifiers? (paths, AWS IDs, team names) → PROJECT
2. About specific codebase structure? → PROJECT
3. Would help any developer? (tool limitation, framework quirk) → USER
4. None of above → SKIP

User-level skills go to: ~/.claude/my-claude-skills/skills/
Project-level skills go to: {cwd}/.claude/skills/
"""

import json
import os
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# Configuration
LOG_FILE = Path(os.environ.get("CLAUDECEPTION_LOG_FILE", os.path.expanduser("~/.claude/claudeception.log")))
DEBUG = os.environ.get("CLAUDECEPTION_DEBUG", "true").lower() == "true"
USER_SKILLS_DIR = Path(os.path.expanduser("~/.claude/my-claude-skills/skills"))


class SkillLevel(Enum):
    """Classification levels for extracted skills."""

    USER = "user"
    PROJECT = "project"
    SKIP = "skip"


def log(message: str) -> None:
    """Append message to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - [taxonomy-classifier] {message}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception:
        pass
    if DEBUG:
        print(log_entry, file=sys.stderr)


# ============================================================================
# Project Identifier Detection
# ============================================================================

# Patterns that indicate project-specific content
PROJECT_PATTERNS = [
    # Absolute paths with usernames
    r"/Users/[^/]+/(?:Projects|Documents|repos|src)/[^/]+",
    r"/home/[^/]+/(?:projects|repos|src)/[^/]+",
    r"C:\\Users\\[^\\]+\\(?:Projects|Documents|repos)",
    # AWS account IDs (12 digits)
    r"\b\d{12}\b",
    # AWS resource ARNs with account IDs
    r"arn:aws:[^:]+:[^:]*:\d{12}:",
    # Specific project names in paths
    r"(?:Projects|repos)/[a-zA-Z0-9_-]{3,30}/",
    # Team/org specific references
    r"\b(?:our team|my team|our org|my org|our company)\b",
    # Specific file references that seem project-local
    r"(?:src|lib|app)/[a-zA-Z0-9_/-]+\.(?:ts|js|py|go|rs|java)",
    # Environment-specific config
    r"\.env\.(?:local|development|staging|production)",
    # Specific database names
    r'database[_-]?name["\']?\s*[:=]\s*["\'][^"\']+["\']',
    # Specific API endpoints with custom domains
    r"https?://(?!(?:github|gitlab|npm|pypi|docs\.))[a-z0-9-]+\.[a-z]+/api/",
]

# Patterns that indicate user-level/universal content
UNIVERSAL_PATTERNS = [
    # Tool/framework names
    r"\b(?:docker|kubernetes|terraform|aws|gcp|azure|react|vue|angular|nextjs|"
    r"fastapi|django|flask|express|prisma|postgresql|mysql|redis|mongodb|"
    r"graphql|grpc|rest|mcp|claude|anthropic|openai|git|npm|yarn|pip|cargo)\b",
    # Error messages
    r"\b(?:error|exception|failed|timeout|refused|denied|invalid|cannot)\b",
    # Framework/library issues
    r"\b(?:bug|issue|limitation|workaround|quirk|gotcha|caveat)\b",
    # General developer actions
    r"\b(?:debugging|profiling|optimizing|refactoring|testing|deploying)\b",
]


def detect_project_identifiers(text: str) -> list[dict]:
    """Find project-specific identifiers in text.

    Returns list of {pattern, match, location}
    """
    return [
        {
            "pattern": pattern[:50] + "..." if len(pattern) > 50 else pattern,
            "match": match.group(),
            "location": match.start(),
        }
        for pattern in PROJECT_PATTERNS
        for match in re.finditer(pattern, text, re.IGNORECASE)
    ]


def detect_universal_indicators(text: str) -> list[str]:
    """Find indicators that this is universal knowledge."""
    indicators = []

    for pattern in UNIVERSAL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        indicators.extend(matches)

    return list(set(indicators))


# ============================================================================
# Classification Logic
# ============================================================================


def analyze_skill_content(skill_data: dict) -> dict:
    """Analyze skill content for classification signals.

    Returns analysis dict with signals and scores.
    """
    # Combine all text fields
    all_text = " ".join(
        [
            skill_data.get("name", ""),
            skill_data.get("description", ""),
            skill_data.get("problem", ""),
            skill_data.get("solution", ""),
            skill_data.get("triggers", ""),
            " ".join(skill_data.get("tags", [])),
        ]
    )

    analysis = {
        "project_identifiers": detect_project_identifiers(all_text),
        "universal_indicators": detect_universal_indicators(all_text),
        "has_absolute_paths": bool(re.search(r"/(?:Users|home)/[^/]+/", all_text)),
        "has_aws_account_ids": bool(re.search(r"\b\d{12}\b", all_text)),
        "references_specific_files": bool(re.search(r"\b(?:src|lib|app)/[^/]+\.[a-z]+\b", all_text)),
        "mentions_tool_limitation": bool(
            re.search(r"\b(?:limitation|bug|workaround|quirk|cannot|doesn\'t support)\b", all_text, re.IGNORECASE)
        ),
        "mentions_error_pattern": bool(
            re.search(r"\b(?:error|exception|failed|timeout)\b.*\b(?:when|if|during)\b", all_text, re.IGNORECASE)
        ),
    }

    # Calculate scores
    project_score = (
        len(analysis["project_identifiers"]) * 2
        + (3 if analysis["has_absolute_paths"] else 0)
        + (3 if analysis["has_aws_account_ids"] else 0)
        + (2 if analysis["references_specific_files"] else 0)
    )

    universal_score = (
        len(analysis["universal_indicators"]) * 1
        + (3 if analysis["mentions_tool_limitation"] else 0)
        + (2 if analysis["mentions_error_pattern"] else 0)
    )

    analysis["project_score"] = project_score
    analysis["universal_score"] = universal_score

    return analysis


def classify_skill(skill_data: dict, cwd: str = "") -> str:
    """Classify a skill as user-level, project-level, or skip.

    Returns: "user" | "project" | "skip"
    """
    analysis = analyze_skill_content(skill_data)

    log(f"Classifying skill '{skill_data.get('name', 'unknown')}'")
    log(f"  Project score: {analysis['project_score']}, Universal score: {analysis['universal_score']}")
    log(f"  Project identifiers: {len(analysis['project_identifiers'])}")
    log(f"  Universal indicators: {analysis['universal_indicators'][:5]}")

    # Decision tree
    reasons = []

    # Check 1: Contains strong project identifiers?
    if analysis["has_absolute_paths"] or analysis["has_aws_account_ids"]:
        reasons.append("Contains absolute paths or AWS account IDs")
        if analysis["project_score"] > analysis["universal_score"]:
            log("  → PROJECT (strong project identifiers)")
            return SkillLevel.PROJECT.value

    # Check 2: Has many project-specific references?
    if analysis["project_score"] >= 5 and analysis["project_score"] > analysis["universal_score"] * 2:
        reasons.append(f"High project score ({analysis['project_score']})")
        log("  → PROJECT (high project score)")
        return SkillLevel.PROJECT.value

    # Check 3: Is about a tool/framework limitation?
    if analysis["mentions_tool_limitation"] or analysis["mentions_error_pattern"]:
        if analysis["universal_score"] > analysis["project_score"]:
            log("  → USER (tool/framework knowledge)")
            return SkillLevel.USER.value

    # Check 4: Has universal indicators and low project score?
    if analysis["universal_score"] >= 3 and analysis["project_score"] <= 2:
        log("  → USER (universal knowledge)")
        return SkillLevel.USER.value

    # Check 5: Mixed signals - default based on ratio
    if analysis["universal_score"] > 0 and analysis["project_score"] > 0:
        ratio = analysis["universal_score"] / (analysis["project_score"] + 0.1)
        if ratio > 1.5:
            log(f"  → USER (universal/project ratio: {ratio:.2f})")
            return SkillLevel.USER.value
        if ratio < 0.5:
            log(f"  → PROJECT (universal/project ratio: {ratio:.2f})")
            return SkillLevel.PROJECT.value

    # Check 6: No strong signals either way
    if analysis["universal_score"] == 0 and analysis["project_score"] == 0:
        # Check tags for hints
        tags = skill_data.get("tags", [])
        tool_tags = {"docker", "kubernetes", "aws", "terraform", "react", "python", "typescript", "git"}
        if {t.lower() for t in tags} & tool_tags:
            log("  → USER (tool-related tags)")
            return SkillLevel.USER.value

        log("  → SKIP (no strong signals)")
        return SkillLevel.SKIP.value

    # Default: user-level if we have any universal indicators
    if analysis["universal_indicators"]:
        log("  → USER (default with universal indicators)")
        return SkillLevel.USER.value

    log("  → SKIP (default - too specific)")
    return SkillLevel.SKIP.value


def get_target_directory(classification: str, cwd: str = "") -> Optional[Path]:
    """Get the target directory for a classified skill.

    - "user" → ~/.claude/my-claude-skills/skills/
    - "project" → {cwd}/.claude/skills/
    - "skip" → None
    """
    if classification == SkillLevel.USER.value:
        return USER_SKILLS_DIR

    if classification == SkillLevel.PROJECT.value:
        if cwd:
            return Path(cwd) / ".claude" / "skills"
        # Fall back to user level if no cwd
        log("No cwd provided for project-level skill, falling back to user-level")
        return USER_SKILLS_DIR

    # skip
    return None


def extract_generalization(skill_data: dict) -> Optional[dict]:
    """If a project-level skill could be generalized, suggest how.

    Returns modified skill_data with project-specific parts removed,
    or None if cannot be generalized.
    """
    analysis = analyze_skill_content(skill_data)

    # If too many project identifiers, can't easily generalize
    if len(analysis["project_identifiers"]) > 3:
        log("Too many project identifiers to generalize")
        return None

    # If no universal indicators, probably not generalizable
    if not analysis["universal_indicators"]:
        log("No universal indicators found")
        return None

    # Create generalized version
    generalized = skill_data.copy()

    # Remove/replace project-specific content
    for field in ["description", "problem", "solution", "triggers"]:
        if field in generalized:
            text = generalized[field]

            # Replace absolute paths with placeholders
            text = re.sub(r"/Users/[^/]+/[^\s]+", "<project-path>", text)
            text = re.sub(r"/home/[^/]+/[^\s]+", "<project-path>", text)

            # Replace AWS account IDs
            text = re.sub(r"\b\d{12}\b", "<aws-account-id>", text)

            # Replace specific file paths
            text = re.sub(r"(?:src|lib|app)/[a-zA-Z0-9_/-]+\.[a-z]+", "<source-file>", text)

            generalized[field] = text

    # Update name to indicate it's generalized
    if "name" in generalized:
        generalized["original_name"] = generalized["name"]
        # Don't change name, just note it

    generalized["_generalized"] = True
    generalized["_original_project_identifiers"] = [p["match"] for p in analysis["project_identifiers"]]

    log("Created generalized version of skill")
    return generalized


# ============================================================================
# CLI Interface
# ============================================================================


def main() -> None:
    """CLI for testing taxonomy classification."""
    import argparse

    parser = argparse.ArgumentParser(description="Claudeception Taxonomy Classifier")
    parser.add_argument("action", choices=["classify", "analyze", "test"], help="Action to perform")
    parser.add_argument("--name", help="Skill name")
    parser.add_argument("--description", help="Skill description")
    parser.add_argument("--problem", help="Problem statement")
    parser.add_argument("--solution", help="Solution")
    parser.add_argument("--tags", nargs="+", help="Skill tags")
    parser.add_argument("--cwd", help="Current working directory")

    args = parser.parse_args()

    if args.action == "classify":
        skill = {
            "name": args.name or "test-skill",
            "description": args.description or "",
            "problem": args.problem or "",
            "solution": args.solution or "",
            "tags": args.tags or [],
        }

        classification = classify_skill(skill, args.cwd or "")
        target_dir = get_target_directory(classification, args.cwd or "")

        print(f"Classification: {classification}")
        print(f"Target directory: {target_dir}")

    elif args.action == "analyze":
        skill = {
            "name": args.name or "test-skill",
            "description": args.description or "",
            "problem": args.problem or "",
            "solution": args.solution or "",
            "tags": args.tags or [],
        }

        analysis = analyze_skill_content(skill)
        print(json.dumps(analysis, indent=2, default=str))

    elif args.action == "test":
        # Test with sample skills
        test_cases = [
            {
                "name": "docker-desktop-stuck-state",
                "description": "Fix Docker Desktop stuck in partial running state on macOS",
                "tags": ["docker", "macos", "debugging"],
                "expected": "user",
            },
            {
                "name": "omega-api-authentication",
                "description": "How to authenticate with the Omega API using /Users/cajias/Projects/omega/config.json",
                "problem": "Need AWS account 123456789012 credentials",
                "tags": ["omega", "api", "auth"],
                "expected": "project",
            },
            {
                "name": "react-usestate-gotcha",
                "description": "useState does not immediately update the state",
                "problem": "State appears stale in event handlers",
                "tags": ["react", "hooks", "state"],
                "expected": "user",
            },
        ]

        print("Running classification tests:\n")
        for test in test_cases:
            classification = classify_skill(test)
            expected = test.pop("expected")
            status = "✓" if classification == expected else "✗"
            print(f"{status} {test['name']}")
            print(f"  Expected: {expected}, Got: {classification}\n")


if __name__ == "__main__":
    main()
