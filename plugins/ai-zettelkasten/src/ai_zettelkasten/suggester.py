"""Proactive suggestion detection for extractable knowledge."""
import re
from dataclasses import dataclass
from typing import Optional

from .obsidian import KnowledgeType


# Detection patterns
FACT_PATTERNS = [
    r'#\s*NOTE:\s*(.+)',
    r'#\s*IMPORTANT:\s*(.+)',
    r'#\s*INFO:\s*(.+)',
]

DECISION_PATTERNS = [
    r'#.*\b(chose|decided|selected|picked|went with)\b.*',
    r'#.*\bbecause\b.*',
]

PATTERN_PATTERNS = [
    r'#.*\b(always|never|pattern|rule)\b.*',
]

CORRECTION_PATTERNS = [
    r'#.*\b(fixed|was wrong|actually|correction|bug)\b.*',
]

# Tag extraction patterns
TAG_KEYWORDS = {
    'aws': ['aws', 'amazon', 'lambda', 's3', 'bedrock', 'dynamodb', 'cloudformation'],
    'python': ['python', 'pip', 'pytest', 'uvx', 'virtualenv'],
    'testing': ['test', 'pytest', 'mock', 'assert', 'fixture'],
    'database': ['database', 'sql', 'postgres', 'dynamodb', 'vector'],
    'api': ['api', 'rest', 'graphql', 'endpoint', 'request'],
    'lambda': ['lambda', 'cold start', 'function'],
}


@dataclass
class Suggestion:
    """A detected extractable knowledge item."""
    content: str
    knowledge_type: KnowledgeType
    tags: list[str]
    confidence: float
    source_line: int


class Suggester:
    """Detects extractable knowledge from code content."""

    def analyze(self, file_path: str, content: str) -> list[Suggestion]:
        """Analyze content for extractable knowledge patterns."""
        suggestions = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            suggestion = self._analyze_line(line, i + 1)
            if suggestion:
                # Enhance tags based on file path
                suggestion.tags.extend(self._tags_from_path(file_path))
                suggestion.tags = list(set(suggestion.tags))
                suggestions.append(suggestion)

        return suggestions

    def _analyze_line(self, line: str, line_num: int) -> Optional[Suggestion]:
        """Check a single line for extractable knowledge."""
        line_stripped = line.strip()

        # Skip non-comment lines
        if not line_stripped.startswith('#'):
            return None

        # Check correction patterns first (highest priority)
        for pattern in CORRECTION_PATTERNS:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return Suggestion(
                    content=self._extract_content(line_stripped),
                    knowledge_type=KnowledgeType.CORRECTION,
                    tags=self._extract_tags(line_stripped),
                    confidence=0.85,
                    source_line=line_num
                )

        # Check decision patterns
        for pattern in DECISION_PATTERNS:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return Suggestion(
                    content=self._extract_content(line_stripped),
                    knowledge_type=KnowledgeType.DECISION,
                    tags=self._extract_tags(line_stripped),
                    confidence=0.80,
                    source_line=line_num
                )

        # Check pattern patterns
        for pattern in PATTERN_PATTERNS:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                return Suggestion(
                    content=self._extract_content(line_stripped),
                    knowledge_type=KnowledgeType.PATTERN,
                    tags=self._extract_tags(line_stripped),
                    confidence=0.75,
                    source_line=line_num
                )

        # Check fact patterns (NOTE:, IMPORTANT:, etc.)
        for pattern in FACT_PATTERNS:
            match = re.search(pattern, line_stripped, re.IGNORECASE)
            if match:
                return Suggestion(
                    content=match.group(1).strip(),
                    knowledge_type=KnowledgeType.FACT,
                    tags=self._extract_tags(line_stripped),
                    confidence=0.90,
                    source_line=line_num
                )

        return None

    def _extract_content(self, line: str) -> str:
        """Extract the meaningful content from a comment line."""
        # Remove # prefix and common markers
        content = re.sub(r'^#\s*', '', line)
        content = re.sub(r'^(NOTE|IMPORTANT|INFO|Fixed|FIXME):\s*', '', content, flags=re.IGNORECASE)
        return content.strip()

    def _extract_tags(self, text: str) -> list[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()

        for tag, keywords in TAG_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)

        return tags

    def _tags_from_path(self, file_path: str) -> list[str]:
        """Infer tags from file path."""
        tags = []
        path_lower = file_path.lower()

        if 'test' in path_lower:
            tags.append('testing')
        if 'lambda' in path_lower:
            tags.extend(['aws', 'lambda'])
        if 'api' in path_lower:
            tags.append('api')

        return tags

    def format_suggestion(self, suggestion: Suggestion) -> str:
        """Format a suggestion for CLI output."""
        tags_str = ", ".join(suggestion.tags) if suggestion.tags else "general"
        return f"""
Worth capturing: "{suggestion.content}"
Type: {suggestion.knowledge_type.value} | Tags: {tags_str}
[y] Add  [n] Skip  [e] Edit
"""
