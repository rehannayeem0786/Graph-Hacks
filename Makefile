.PHONY: setup run ingest ask stats serve test clean

setup:
	python -m venv .venv
	.venv/Scripts/pip install -r requirements.txt

run:
	docker-compose up -d

ingest:
	python -m src.cli ingest ./src

ask:
	python -m src.cli ask "What is the most critical module?"

stats:
	python -m src.cli stats

serve:
	python -m src.cli serve

test:
	python -m pytest tests/ -v

clean:
	docker-compose down -v
