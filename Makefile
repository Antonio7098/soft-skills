.PHONY: run stop

run:
	cd backend && PYTHONPATH=src python -m uvicorn soft_skills_backend.app:app --reload &
	cd frontend && npm run dev

stop:
	pkill -f "uvicorn soft_skills_backend" || true
	pkill -f "vite" || true