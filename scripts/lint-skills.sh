#!/bin/bash
# Skill Structure Linter

set -e

ERRORS=0
SKILLS_DIR="skills"

echo "🔍 Linting skill directories..."

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    echo ""
    echo "Checking: $skill_name"
    
    # Check SKILL.md exists (uppercase)
    if [ ! -f "$skill_dir/SKILL.md" ]; then
        echo "  ❌ Missing SKILL.md (uppercase required)"
        
        # Check if lowercase exists
        if [ -f "$skill_dir/skill.md" ]; then
            echo "     Found skill.md - rename to SKILL.md"
        fi
        ERRORS=$((ERRORS + 1))
    else
        echo "  ✅ SKILL.md exists"
    fi
    
    # Check README.md exists
    if [ ! -f "$skill_dir/README.md" ]; then
        echo "  ❌ Missing README.md"
        ERRORS=$((ERRORS + 1))
    else
        echo "  ✅ README.md exists"
    fi
    
    # Check directory name is kebab-case
    if [[ ! "$skill_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
        echo "  ⚠️  Directory name should be kebab-case: $skill_name"
    fi
    
    # Check SKILL.md has title
    if [ -f "$skill_dir/SKILL.md" ]; then
        if ! head -5 "$skill_dir/SKILL.md" | grep -q "^# "; then
            echo "  ⚠️  SKILL.md should start with a # title"
        fi
    fi
    
    # Check SKILL.md has Objective section
    if [ -f "$skill_dir/SKILL.md" ]; then
        if ! grep -q "^## Objective" "$skill_dir/SKILL.md"; then
            echo "  ⚠️  SKILL.md should have an ## Objective section"
        fi
    fi
    
    # Check README.md is not empty
    if [ -f "$skill_dir/README.md" ]; then
        if [ ! -s "$skill_dir/README.md" ]; then
            echo "  ⚠️  README.md should not be empty"
        fi
    fi
    
    # Check examples/ directory if present contains .md files
    if [ -d "$skill_dir/examples" ]; then
        md_count=$(find "$skill_dir/examples" -maxdepth 1 -type f -name "*.md" | wc -l)
        if [ "$md_count" -eq 0 ]; then
            echo "  ⚠️  examples/ directory should contain .md files"
        fi
    fi
    
    # Check config/ directory if present contains valid JSON
    if [ -d "$skill_dir/config" ]; then
        for json_file in "$skill_dir/config"/*.json; do
            if [ -f "$json_file" ]; then
                if ! python3 -m json.tool "$json_file" > /dev/null 2>&1; then
                    echo "  ⚠️  Invalid JSON in $(basename "$json_file")"
                fi
            fi
        done
    fi
    
    # Check for spaces in file/directory names
    if find "$skill_dir" -name "* *" | grep -q .; then
        echo "  ⚠️  Found spaces in file/directory names"
        find "$skill_dir" -name "* *" | while read -r file; do
            echo "     $(basename "$file")"
        done
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -gt 0 ]; then
    echo "❌ Found $ERRORS error(s)"
    exit 1
else
    echo "✅ All skills pass validation"
    exit 0
fi
