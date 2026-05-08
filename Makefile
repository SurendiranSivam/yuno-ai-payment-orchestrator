.PHONY: setup up down logs backend-logs frontend-logs db-shell seed test

# Full setup: build and start all services
setup:
	docker-compose up --build -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Seeding database..."
	docker-compose exec backend python seed.py
	@echo "\n✅ Yuno AI Orchestrator is ready!"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

frontend-logs:
	docker-compose logs -f frontend

db-shell:
	docker-compose exec postgres psql -U yuno -d yuno_orchestrator

seed:
	docker-compose exec backend python seed.py

test:
	docker-compose exec backend pytest tests/ -v
