.PHONY: install server frontend dev clean

install:
	pip install -e .

server:
	uvicorn app.server:app --port 5173 --reload

frontend:
	cd app/frontend && npm run dev

dev:
	$(MAKE) server & $(MAKE) frontend &

clean:
	rm -rf __pycache__ app/__pycache__