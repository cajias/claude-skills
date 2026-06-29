.PHONY: validate install test-skills help

validate: ## validate plugin structure and marketplace sync
	bash scripts/validate.sh

install: ## symlink all plugins to ~/.claude/plugins/
	mkdir -p ~/.claude/plugins
	for dir in plugins/*/; do name=$$(basename "$$dir"); ln -sf "$$(pwd)/$$dir" ~/.claude/plugins/"$$name"; echo "  linked $$name"; done

test-skills: ## run skill eval harness for all plugins
	bash scripts/test-skills.sh

help: ## show available targets
	grep -E "^[a-zA-Z_-]+:.*?##" $(MAKEFILE_LIST) | awk -F":.*?## " '{printf "  %-15s %s\n", $$1, $$2}'
