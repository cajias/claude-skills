# gitlab-yamllint-reference-tags

Fix yamllint failures on GitLab CI `!reference` tags. Use when:
(1) yamllint fails with "unknown tag" on `.gitlab-ci.yml`,
(2) Pre-commit hooks reject valid GitLab CI syntax,
(3) CI lint job fails but GitLab accepts the YAML,
(4) Error mentions `!reference` or custom YAML tags.
Covers yamllint configuration for GitLab-specific tags.
