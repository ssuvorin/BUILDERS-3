.PHONY: run eval lint

run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

eval:
	uv run pytest -q

lint:
	uv run ruff check app tests
