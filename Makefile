.PHONY: install test lint discover rank shortlist run

install:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check .

discover:
	job-search discover

rank:
	job-search rank data/raw/jobs.json --max-age-days 7

shortlist:
	job-search shortlist data/ranked/jobs.json

run:
	job-search run-all
