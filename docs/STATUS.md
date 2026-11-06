# Status

The claims pilot from `docs/PLAN.md` is built.

## What is built

- `backend/`: FastAPI and SQLite. `backend/db.py` creates the database on first use and seeds it from the named files in `data/`, never `data/evals/`. Read routes serve claims, policies, a customer's previous claims, plans, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers. Workflow routes (`backend/workflow.py`) start a claim, record and list the agent's steps, decide, pay, sign off and run the agent in the background.
- The payment rule lives in the backend: `pay_claim` is refused with 409 unless the claim is approved, the amount equals the payout and the payout is at most $1,000. A larger approval waits in `waiting_for_signoff` until a handler signs off, which pays it.
- Claim states: `waiting`, `in_progress`, `waiting_for_signoff`, `decided`.
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter with `openai/gpt-6-luna` at low reasoning effort, or the model in `MODEL_NAME`. `run(claim_id, thread_id)` fetches its instructions from the backend, starts the claim and records every model reply, tool call and tool result as a step. Its tools reach the claim, policy, plan, claim history and policy wording, and decide and pay, all through the backend's API.
- `dashboard/`: the queue with a count per state (`#/`), a claim with its decision, the agent's steps, story, items, documents, policy and history (`#/claims/CLM-1001`), and the agent's instructions, read only (`#/instructions`). A claim page can run the agent and polls its steps every two seconds while it works; a claim waiting for sign-off has a handler picker and "Sign off and pay". Light and dark mode follow the system setting.
- `e2e/`: Playwright tests of the queue, a claim page and the sign-off of a payout over $1,000, with no model call.

## How to run it

- `npm run dev` starts the backend on port 8000 and the dashboard on http://localhost:5173.
- With the backend running, `uv run -m agent CLM-1001` decides one claim and `uv run -m agent --queue` decides every waiting claim in turn. Both need `OPENROUTER_API_KEY` in `.env`; set `MODEL_NAME=openrouter/free` for a free model.
- `UNDERCOVER_DB` sets the database file, by default `undercover.db` at the repo root. Delete the file to start again from `data/`.
- `npm run check` runs every check. The end-to-end tests start their own backend on port 8001 with `e2e/undercover-e2e.db`, deleted at the start of each run, and the dashboard on port 5174, so they never touch the development data.

## Notes

- On this machine, Norton sets `SSLKEYLOGFILE`, which makes Python exit silently when it opens a TLS connection. Clear it in the shell before running Python (`Remove-Item Env:SSLKEYLOGFILE` in PowerShell).
- Not in the pilot: the claims manual, sign-in, real payments, messages to customers and scoring the agent against `data/evals/`.
