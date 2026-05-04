.PHONY: pack check outdated help

pack: ## regenerate .claude-plugin/marketplace.json from apm.yml
	apm pack

check: ## validate apm.yml schema and plugin reachability
	apm marketplace check --offline

outdated: ## report drift between resolved versions and upstream tags
	apm marketplace outdated

help: ## show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
	  | awk -F':.*?## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
