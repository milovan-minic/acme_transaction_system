# Makefile for First Circle Transactions Project

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down -v

migrate:
	docker compose run --rm app alembic upgrade head

seed:
	docker compose run --rm app python seed.py

test:
	docker compose run --rm app pytest

logs:
	docker compose logs -f app 