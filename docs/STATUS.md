# Status

The claims pilot is being built from `docs/PLAN.md`.

- `backend/`: FastAPI and SQLite. `backend/db.py` creates the database and seeds it from the named files in `data/` on first use; `UNDERCOVER_DB` sets the file (default `undercover.db` at the repo root). Read routes: claims, policies, a customer's claim history, plans, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers. Workflow routes (`backend/workflow.py`): start a claim, record and list the agent's steps, decide, pay and sign off. The backend enforces the payment rule: `pay_claim` is refused with 409 unless the claim is approved, the amount equals the payout and the payout is at most $1,000; larger payouts wait in `waiting_for_signoff` until a handler signs off, which pays them.
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter (`openai/gpt-6-luna` with low reasoning effort, or `MODEL_NAME`). `run(claim_id, thread_id)` fetches its instructions from the backend, starts the claim and records every model reply, tool call and tool result as a step. Its tools read the claim, policy, plan, claim history and policy wording, decide and pay, all through the backend's API. `POST /api/claims/{claim_id}/run` starts it in the background.
- `dashboard/`: React with a small hash router. The queue (`#/`) with a count per state, a claim (`#/claims/CLM-1001`) with its decision, story, items, documents, policy and history, and the agent's instructions, read only (`#/instructions`). Brand fonts and colors, light and dark mode from the system setting. `src/api.ts` is the typed API client.
- `e2e/`: one test of that page

Run the agent on one claim with the backend running: `uv run -m agent CLM-1001`.

`npm run dev` starts the backend on port 8000 and the dashboard on port 5173. Delete `undercover.db` to start again from `data/`.
