.PHONY: setup demo test check serve transform insights
setup:
	uv sync --frozen --extra dev
	pnpm install --frozen-lockfile
	pnpm build
demo:
	uv run atlasiq demo --month 2025-01 --limit 100000
serve:
	uv run atlasiq serve --port 8020
transform:
	uv run atlasiq transform
insights:
	uv run atlasiq insights
test:
	uv run pytest -q
check:
	uv run ruff check src tests orchestration
	uv run ruff format --check src tests orchestration
	uv run mypy src
	pnpm typecheck
