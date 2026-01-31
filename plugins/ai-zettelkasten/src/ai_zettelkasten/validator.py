"""Link validation using Claude Haiku for Zettelkasten connections.

This module provides LLM-based validation of proposed links between notes,
ensuring meaningful Zettelkasten connections rather than just topical similarity.
"""

import json
from dataclasses import dataclass

import boto3


VALIDATION_PROMPT = """You are a Zettelkasten link validator. Your job is to determine if two notes should be linked and classify their relationship.

Source Note: {source_title}
---
{source_content_preview}
---

Target Note: {target_title}
---
{target_content_preview}
---

TASK: Determine if these notes should be linked and classify the relationship.

CRITERIA FOR LINKING:
- Links should connect IDEAS, not just similar topics
- Ask: "Why would knowing A help me understand B?"
- A good link creates insight when followed
- Avoid links that just group similar content

RELATIONSHIP TYPES:
- SOLVES: Source addresses problem described in Target
- ENABLES: Source is prerequisite for Target
- ELABORATES: Source expands/details concept in Target
- CONTRADICTS: Source challenges or limits Target
- SUPPORTS: Source provides evidence for Target
- APPLIES: Source applies principle from Target
- ABSTRACTS: Source generalizes from Target
- SEQUENCE: Source logically follows Target

OUTPUT ONLY VALID JSON (no markdown, no explanation):
{{"should_link": true, "relationship": "ELABORATES", "confidence": 0.85, "reason": "brief explanation"}}"""


@dataclass
class ValidationResult:
    """Result of LLM validation for a proposed link."""

    should_link: bool
    relationship: str
    confidence: float
    reason: str


class LinkValidator:
    """Validates proposed Zettelkasten links using Claude Haiku.

    Uses semantic understanding to determine if two notes should be linked
    and classifies the relationship type.
    """

    def __init__(self, min_confidence: float = 0.7, region: str = "us-west-2"):
        """Initialize the validator.

        Args:
            min_confidence: Minimum confidence threshold to accept a link (0.0-1.0)
            region: AWS region for Bedrock
        """
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        self.min_confidence = min_confidence

    def validate(
        self,
        source_title: str,
        source_content: str,
        target_title: str,
        target_content: str,
    ) -> ValidationResult:
        """Validate a single link candidate.

        Args:
            source_title: Title of the source note
            source_content: Content preview of source note (first ~500 chars)
            target_title: Title of the target note
            target_content: Content preview of target note (first ~500 chars)

        Returns:
            ValidationResult with link decision, relationship type, and confidence
        """
        prompt = VALIDATION_PROMPT.format(
            source_title=source_title,
            source_content_preview=source_content[:500],
            target_title=target_title,
            target_content_preview=target_content[:500],
        )

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 200,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            )

            result = json.loads(response["body"].read())
            output_text = result["content"][0]["text"].strip()

            # Parse JSON response - handle potential markdown wrapping
            if output_text.startswith("```"):
                # Extract JSON from code block
                lines = output_text.split("\n")
                json_lines = [line for line in lines if not line.startswith("```")]
                output_text = "\n".join(json_lines)

            output = json.loads(output_text)

            confidence = float(output.get("confidence", 0))
            should_link = (
                output.get("should_link", False) and confidence >= self.min_confidence
            )

            return ValidationResult(
                should_link=should_link,
                relationship=output.get("relationship", "ELABORATES"),
                confidence=confidence,
                reason=output.get("reason", ""),
            )

        except json.JSONDecodeError as e:
            # If LLM returns invalid JSON, reject the link
            return ValidationResult(
                should_link=False,
                relationship="UNKNOWN",
                confidence=0.0,
                reason=f"Invalid response format: {e}",
            )
        except Exception as e:
            # On any error, reject conservatively
            return ValidationResult(
                should_link=False,
                relationship="UNKNOWN",
                confidence=0.0,
                reason=f"Validation error: {e}",
            )

    def validate_batch(
        self,
        source_title: str,
        source_content: str,
        candidates: list[dict],
    ) -> list[tuple[dict, ValidationResult]]:
        """Validate multiple link candidates for a source note.

        Args:
            source_title: Title of the source note
            source_content: Content of the source note
            candidates: List of candidate dicts with 'title' and 'content' keys

        Returns:
            List of (candidate, ValidationResult) tuples
        """
        results = []
        for candidate in candidates:
            result = self.validate(
                source_title=source_title,
                source_content=source_content,
                target_title=candidate.get("title", ""),
                target_content=candidate.get("content", ""),
            )
            results.append((candidate, result))
        return results
