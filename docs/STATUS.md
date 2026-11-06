# Status

The claims pilot is being built from `docs/PLAN.md`.

- `backend/`: FastAPI and SQLite. `backend/db.py` creates the database and seeds it from the named files in `data/` on first use; `UNDERCOVER_DB` sets the file (default `undercover.db` at the repo root). Read routes: claims, policies, a customer's claim history, plans, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers. Workflow routes (`backend/workflow.py`): start a claim, record and list the agent's steps, decide, pay and sign off. The backend enforces the payment rule: `pay_claim` is refused with 409 unless the claim is approved, the amount equals the payout and the payout is at most $1,000; larger payouts wait in `waiting_for_signoff` until a handler signs off, which pays them.
- `agent/`: the entry point `run(claim_id, thread_id)`, with one tool that calls the health route
- `dashboard/`: one page that shows whether the backend is up
- `e2e/`: one test of that page

`npm run dev` starts the backend on port 8000 and the dashboard on port 5173. Delete `undercover.db` to start again from `data/`.
