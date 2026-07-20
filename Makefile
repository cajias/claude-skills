.PHONY: validate install test-skills lint lint-fix format format-check fix lint-file deps-python help

validate: ## validate plugin structure and marketplace sync
	bash scripts/validate.sh

install: ## symlink all plugins to ~/.claude/plugins/
	mkdir -p ~/.claude/plugins
	for dir in plugins/*/; do name=$$(basename "$$dir"); ln -sf "$$(pwd)/$$dir" ~/.claude/plugins/"$$name"; echo "  linked $$name"; done

test-skills: ## run skill eval harness for all plugins
	bash scripts/test-skills.sh

node_modules: package.json ## install npm dev dependencies
	npm install
	@touch node_modules

deps-python: ## install semantic-search python deps (HEAVY: pulls torch, multi-GB)
	cd plugins/semantic-search && uv sync

lint: node_modules ## lint markdown + filenames
	npm run lint

lint-fix: node_modules ## auto-fix markdown lint issues
	npm run lint:fix

format: node_modules ## format md/json/yaml with prettier
	npm run format

format-check: node_modules ## check formatting without writing
	npm run format:check

fix: node_modules ## auto-fix lint issues then format
	npm run lint:fix
	npm run format

lint-file: node_modules ## format+lint one file: make lint-file FILE=path
	@test -n "$(FILE)" || { echo "usage: make lint-file FILE=path" >&2; exit 2; }
	@case "$(FILE)" in \
	  plugins/*.py) f='$(FILE)'; d=$${f#plugins/}; d="plugins/$${d%%/*}"; r=$${f#$$d/}; \
	    if [ -f "$$d/pyproject.toml" ]; then \
	      uv run --directory "$$d" --all-extras ruff format "$$r" && uv run --directory "$$d" --all-extras ruff check --fix "$$r" && uv run --directory "$$d" --all-extras ruff check "$$r"; \
	    fi ;; \
	  *.md) npx prettier --write "$(FILE)" && npx markdownlint --fix "$(FILE)" && npx markdownlint "$(FILE)" ;; \
	  *.json|*.yml|*.yaml) npx prettier --write "$(FILE)" ;; \
	  *.ts|*.tsx|*.mjs|*.js) npx prettier --write "$(FILE)" ;; \
	  *) : ;; \
	esac

help: ## show available targets
	grep -E "^[a-zA-Z_-]+:.*?##" $(MAKEFILE_LIST) | awk -F":.*?## " '{printf "  %-15s %s\n", $$1, $$2}'
