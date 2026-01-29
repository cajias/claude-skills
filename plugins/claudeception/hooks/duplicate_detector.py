#!/usr/bin/env python3
"""
Claudeception v4.0 - TF-IDF Based Duplicate Detection

Detects similar skills using TF-IDF + Cosine Similarity without external ML dependencies.
Replaces weak keyword matching with proper text similarity.

Multi-signal similarity formula:
  similarity = tfidf_cosine * 0.4 + tag_jaccard * 0.2 + trigger_overlap * 0.25 + name_similarity * 0.15

Thresholds:
  0.65 - Flag for review
  0.85 - Auto-reject as duplicate
"""

import json
import math
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Configuration
SKILLS_DIR = Path(os.environ.get('CLAUDECEPTION_SKILLS_DIR',
                                  os.path.expanduser('~/.claude/my-claude-skills/skills')))
LOG_FILE = Path(os.environ.get('CLAUDECEPTION_LOG_FILE',
                                os.path.expanduser('~/.claude/claudeception.log')))
DEBUG = os.environ.get('CLAUDECEPTION_DEBUG', 'true').lower() == 'true'

# Similarity weights
WEIGHT_TFIDF = 0.4
WEIGHT_TAGS = 0.2
WEIGHT_TRIGGERS = 0.25
WEIGHT_NAME = 0.15

# Thresholds
THRESHOLD_FLAG = 0.65
THRESHOLD_REJECT = 0.85


def log(message: str) -> None:
    """Append message to log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} - [duplicate-detector] {message}"
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{log_entry}\n")
    except Exception:
        pass
    if DEBUG:
        print(log_entry, file=sys.stderr)


# ============================================================================
# Text Processing
# ============================================================================

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words, removing punctuation."""
    if not text:
        return []
    # Remove markdown formatting
    text = re.sub(r'[#*`\[\]()]', ' ', text)
    # Split on non-alphanumeric, keep hyphens within words
    words = re.findall(r'\b[a-z][a-z0-9-]*[a-z0-9]\b|\b[a-z]\b', text.lower())
    return words


def remove_stopwords(tokens: List[str]) -> List[str]:
    """Remove common stopwords."""
    stopwords = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it',
        'its', 'you', 'your', 'we', 'our', 'they', 'their', 'what', 'which',
        'who', 'whom', 'use', 'using', 'when', 'skill', 'skills'
    }
    return [t for t in tokens if t not in stopwords]


# ============================================================================
# TF-IDF Implementation
# ============================================================================

class TFIDFVectorizer:
    """Simple TF-IDF vectorizer using only Python stdlib."""

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.documents: List[List[str]] = []

    def fit(self, documents: List[str]) -> 'TFIDFVectorizer':
        """Build vocabulary and compute IDF from documents."""
        self.documents = [remove_stopwords(tokenize(doc)) for doc in documents]

        # Build vocabulary
        all_tokens = set()
        for doc in self.documents:
            all_tokens.update(doc)
        self.vocabulary = {token: idx for idx, token in enumerate(sorted(all_tokens))}

        # Compute IDF
        n_docs = len(self.documents)
        doc_freq: Counter = Counter()
        for doc in self.documents:
            doc_freq.update(set(doc))

        for token, freq in doc_freq.items():
            # IDF = log(N / df) + 1 (smoothed)
            self.idf[token] = math.log(n_docs / freq) + 1

        return self

    def transform(self, text: str) -> Dict[str, float]:
        """Transform a single document to TF-IDF vector."""
        tokens = remove_stopwords(tokenize(text))
        if not tokens:
            return {}

        # Compute TF (term frequency)
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1

        # Compute TF-IDF
        vector = {}
        for token, count in tf.items():
            if token in self.vocabulary:
                normalized_tf = 0.5 + 0.5 * (count / max_tf)  # Augmented TF
                vector[token] = normalized_tf * self.idf.get(token, 1.0)

        return vector

    def fit_transform(self, documents: List[str]) -> List[Dict[str, float]]:
        """Fit and transform in one step."""
        self.fit(documents)
        return [self.transform(doc) for doc in documents]


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    if not vec_a or not vec_b:
        return 0.0

    # Dot product
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)

    # Magnitudes
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot_product / (mag_a * mag_b)


# ============================================================================
# Other Similarity Metrics
# ============================================================================

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union if union > 0 else 0.0


def name_similarity(name_a: str, name_b: str) -> float:
    """Compute similarity between skill names."""
    if not name_a or not name_b:
        return 0.0

    # Normalize names
    tokens_a = set(name_a.lower().replace('-', ' ').split())
    tokens_b = set(name_b.lower().replace('-', ' ').split())

    return jaccard_similarity(tokens_a, tokens_b)


def trigger_overlap(triggers_a: str, triggers_b: str) -> float:
    """Compute overlap between trigger conditions."""
    if not triggers_a or not triggers_b:
        return 0.0

    # Extract key phrases
    def extract_phrases(text: str) -> Set[str]:
        # Look for quoted strings, bullet points, specific patterns
        phrases = set()
        # Bullet points
        for match in re.findall(r'[-•*]\s*(.+?)(?:\n|$)', text):
            phrases.add(match.strip().lower())
        # Quoted strings
        for match in re.findall(r'"([^"]+)"', text):
            phrases.add(match.lower())
        # If no structured content, fall back to sentences
        if not phrases:
            phrases = set(remove_stopwords(tokenize(text)))
        return phrases

    phrases_a = extract_phrases(triggers_a)
    phrases_b = extract_phrases(triggers_b)

    return jaccard_similarity(phrases_a, phrases_b)


# ============================================================================
# Skill Loading
# ============================================================================

def load_skill(skill_path: Path) -> Optional[Dict]:
    """Load a skill from its SKILL.md file."""
    try:
        content = skill_path.read_text()

        # Parse YAML frontmatter
        skill_data = {'name': skill_path.parent.name}

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]

                # Simple YAML parsing for key fields
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key in ['name', 'description']:
                            skill_data[key] = value
                        elif key == 'tags':
                            # Parse tags array
                            if value.startswith('['):
                                tags = re.findall(r'[\w-]+', value)
                                skill_data['tags'] = tags

                skill_data['body'] = body
        else:
            skill_data['body'] = content

        # Extract sections from body
        body = skill_data.get('body', '')

        # Problem section
        problem_match = re.search(r'##\s*Problem.*?\n(.*?)(?=##|\Z)', body, re.DOTALL | re.IGNORECASE)
        if problem_match:
            skill_data['problem'] = problem_match.group(1).strip()

        # Solution section
        solution_match = re.search(r'##\s*Solution.*?\n(.*?)(?=##|\Z)', body, re.DOTALL | re.IGNORECASE)
        if solution_match:
            skill_data['solution'] = solution_match.group(1).strip()

        # Triggers section
        triggers_match = re.search(r'##\s*When to Use.*?\n(.*?)(?=##|\Z)', body, re.DOTALL | re.IGNORECASE)
        if triggers_match:
            skill_data['triggers'] = triggers_match.group(1).strip()

        return skill_data

    except Exception as e:
        log(f"Error loading skill {skill_path}: {e}")
        return None


def load_all_skills(skills_dir: Path = SKILLS_DIR) -> List[Dict]:
    """Load all skills from the skills directory."""
    skills = []

    if not skills_dir.exists():
        log(f"Skills directory does not exist: {skills_dir}")
        return skills

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / 'SKILL.md'
            if skill_file.exists():
                skill = load_skill(skill_file)
                if skill:
                    skills.append(skill)

    log(f"Loaded {len(skills)} existing skills from {skills_dir}")
    return skills


# ============================================================================
# Main Duplicate Detection
# ============================================================================

def skill_to_text(skill: Dict) -> str:
    """Convert skill to searchable text."""
    parts = [
        skill.get('name', '').replace('-', ' '),
        skill.get('description', ''),
        skill.get('problem', ''),
        skill.get('solution', ''),
        ' '.join(skill.get('tags', []))
    ]
    return ' '.join(parts)


def calculate_multi_signal_similarity(skill_a: Dict, skill_b: Dict,
                                       vectorizer: TFIDFVectorizer) -> float:
    """
    Calculate combined similarity score using multiple signals.

    Formula: tfidf_cosine * 0.4 + tag_jaccard * 0.2 + trigger_overlap * 0.25 + name_similarity * 0.15
    """
    # TF-IDF cosine similarity
    text_a = skill_to_text(skill_a)
    text_b = skill_to_text(skill_b)
    vec_a = vectorizer.transform(text_a)
    vec_b = vectorizer.transform(text_b)
    tfidf_sim = cosine_similarity(vec_a, vec_b)

    # Tag Jaccard similarity
    tags_a = set(skill_a.get('tags', []))
    tags_b = set(skill_b.get('tags', []))
    tag_sim = jaccard_similarity(tags_a, tags_b)

    # Trigger overlap
    triggers_a = skill_a.get('triggers', '')
    triggers_b = skill_b.get('triggers', '')
    trigger_sim = trigger_overlap(triggers_a, triggers_b)

    # Name similarity
    name_sim = name_similarity(skill_a.get('name', ''), skill_b.get('name', ''))

    # Combined score
    combined = (
        tfidf_sim * WEIGHT_TFIDF +
        tag_sim * WEIGHT_TAGS +
        trigger_sim * WEIGHT_TRIGGERS +
        name_sim * WEIGHT_NAME
    )

    log(f"Similarity {skill_a.get('name')} vs {skill_b.get('name')}: "
        f"tfidf={tfidf_sim:.2f}, tags={tag_sim:.2f}, triggers={trigger_sim:.2f}, "
        f"name={name_sim:.2f}, combined={combined:.2f}")

    return combined


def find_similar_skills(new_skill: Dict, threshold: float = THRESHOLD_FLAG,
                        skills_dir: Path = SKILLS_DIR) -> List[Dict]:
    """
    Find skills similar to the new skill.

    Returns list of {skill_name, similarity_score, recommendation}
    """
    existing_skills = load_all_skills(skills_dir)

    if not existing_skills:
        return []

    # Build vectorizer from all skills including new one
    all_texts = [skill_to_text(s) for s in existing_skills]
    all_texts.append(skill_to_text(new_skill))

    vectorizer = TFIDFVectorizer()
    vectorizer.fit(all_texts)

    # Compare new skill against all existing
    similar = []
    for skill in existing_skills:
        similarity = calculate_multi_signal_similarity(new_skill, skill, vectorizer)

        if similarity >= threshold:
            if similarity >= THRESHOLD_REJECT:
                recommendation = 'reject'
            elif similarity >= THRESHOLD_FLAG:
                recommendation = 'review'
            else:
                recommendation = 'ok'

            similar.append({
                'skill_name': skill.get('name', 'unknown'),
                'similarity_score': round(similarity, 3),
                'recommendation': recommendation
            })

    # Sort by similarity descending
    similar.sort(key=lambda x: x['similarity_score'], reverse=True)

    return similar


def should_reject_duplicate(new_skill: Dict, threshold: float = THRESHOLD_REJECT,
                            skills_dir: Path = SKILLS_DIR) -> Tuple[bool, str]:
    """
    Check if the new skill should be rejected as a duplicate.

    Returns (should_reject, reason)
    """
    similar = find_similar_skills(new_skill, threshold=THRESHOLD_FLAG, skills_dir=skills_dir)

    for match in similar:
        if match['similarity_score'] >= threshold:
            reason = (f"Too similar to existing skill '{match['skill_name']}' "
                     f"(similarity: {match['similarity_score']:.2f}, threshold: {threshold})")
            log(f"Rejecting duplicate: {reason}")
            return True, reason

    if similar:
        names = [m['skill_name'] for m in similar[:3]]
        log(f"New skill has similar skills but below rejection threshold: {names}")

    return False, ""


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI for testing duplicate detection."""
    import argparse

    parser = argparse.ArgumentParser(description='Claudeception Duplicate Detector')
    parser.add_argument('action', choices=['check', 'list', 'test'],
                       help='Action to perform')
    parser.add_argument('--name', help='Skill name to check')
    parser.add_argument('--description', help='Skill description')
    parser.add_argument('--tags', nargs='+', help='Skill tags')
    parser.add_argument('--threshold', type=float, default=THRESHOLD_FLAG,
                       help='Similarity threshold')

    args = parser.parse_args()

    if args.action == 'list':
        skills = load_all_skills()
        print(f"Found {len(skills)} skills:")
        for skill in skills:
            print(f"  - {skill.get('name')}: {skill.get('description', 'No description')[:50]}...")

    elif args.action == 'check':
        if not args.name:
            print("Error: --name required for check action")
            sys.exit(1)

        new_skill = {
            'name': args.name,
            'description': args.description or '',
            'tags': args.tags or []
        }

        similar = find_similar_skills(new_skill, args.threshold)

        if similar:
            print(f"Found {len(similar)} similar skills:")
            for match in similar:
                print(f"  - {match['skill_name']}: {match['similarity_score']:.2f} ({match['recommendation']})")
        else:
            print("No similar skills found")

        should_reject, reason = should_reject_duplicate(new_skill)
        if should_reject:
            print(f"\nREJECT: {reason}")
        else:
            print("\nOK to create")

    elif args.action == 'test':
        # Test with sample skills
        test_skill = {
            'name': 'docker-container-stuck',
            'description': 'Fix Docker containers stuck in restart loop',
            'tags': ['docker', 'container', 'debugging'],
            'problem': 'Docker container keeps restarting',
            'solution': 'Check logs and resource limits'
        }

        print("Testing with sample skill:")
        print(f"  Name: {test_skill['name']}")
        print(f"  Description: {test_skill['description']}")

        similar = find_similar_skills(test_skill)
        if similar:
            print(f"\nFound {len(similar)} similar:")
            for match in similar[:5]:
                print(f"  - {match['skill_name']}: {match['similarity_score']:.2f}")


if __name__ == '__main__':
    main()
