.PHONY: install api web test lint build up down seed clean

install:   ## Install backend (dev+api) and frontend deps
	pip install -e ".[dev,api]"
	cd frontend && npm install

api:       ## Run the backend with autoreload
	uvicorn pls_ct.app.main:app --reload

web:       ## Run the frontend dev server (proxies /api -> :8000)
	cd frontend && npm run dev

seed:      ## Migrate + load the synthetic sample + build the RAG index
	alembic upgrade head
	pls db-load --records data/sample/trials.json
	pls index --records data/sample/trials.json

test:      ## Run backend + frontend tests
	pytest -q
	cd frontend && npm test

lint:      ## Lint the backend
	ruff check .

build:     ## Build the frontend production bundle
	cd frontend && npm run build

up:        ## Build + start the full Docker stack
	docker compose up --build

down:      ## Stop the Docker stack
	docker compose down
