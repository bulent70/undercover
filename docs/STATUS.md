# Status

The claims pilot is being built from `docs/PLAN.md`.

- `backend/`: FastAPI and SQLite. `backend/db.py` creates the database and seeds it from the named files in `data/` on first use; `UNDERCOVER_DB` sets the file (default `undercover.db` at the repo root). Read routes: claims, policies, a customer's claim history, plans, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers.
- `agent/`: the entry point `run(claim_id, thread_id)`, with one tool that calls the health route
- `dashboard/`: one page that shows whether the backend is up
- `e2e/`: one test of that page

`npm run dev` starts the backend on port 8000 and the dashboard on port 5173. Delete `undercover.db` to start again from `data/`.
