# Plan: the claims pilot

Builds what `docs/SPEC.md` asks for: a backend that holds UnderCover's records and enforces the payment rule, the UnderCover Agent that decides claims through the backend's API, and a dashboard where the handlers watch the queue, read each decision, follow the agent step by step and sign off large payouts.

## Approach

- **One source of truth.** The backend owns the data in SQLite and every rule that must hold whatever the agent does. The agent and the dashboard only talk to the backend's API, so the $1,000 sign-off rule is enforced in one place.
- **SQLite with the standard library.** `sqlite3` is enough for one process and 25 claims; no ORM. The database file is created and seeded from `data/` on first start. Its path comes from `UNDERCOVER_DB` (default `undercover.db` at the repo root, already ignored by git), so tests and end-to-end runs use their own file.
- **Records kept as JSON.** Claims, policies and customers are stored as one JSON column per row, as they arrive in `data/`. The fields the workflow changes (status, decision, payment, steps) get their own columns and tables.
- **`data/evals/` is never read.** The seed reads named files only, and a test checks that no route returns anything from the evals.
- **The agent's instructions live in the backend** (`backend/instructions.md`), served read only, so the agent and the dashboard show the same text.
- **Steps are recorded by the agent's run**, not by the model: a callback in `agent/` posts each model turn and tool call to the backend, and the dashboard polls them.
- **No new dependencies.** FastAPI, LangChain, React and Playwright are already installed. The dashboard uses a small hash router instead of a routing library.

## Claim states

| State | Set when |
|---|---|
| `waiting` | Seeded (`open` in `data/claims.json`) |
| `in_progress` | The agent starts work on the claim |
| `waiting_for_signoff` | The agent approves with a payout over $1,000 |
| `decided` | Declined, referred, approved and paid up to $1,000, or signed off and paid |

A claim in `in_progress` can be run again, in case a run ends without a decision.

## API

Every operation has an `operation_id`, a one-line docstring and only required inputs.

| Operation | Route | Used by |
|---|---|---|
| `health` | `GET /api/health` | dashboard |
| `list_claims` | `GET /api/claims` | dashboard |
| `get_claim` | `GET /api/claims/{claim_id}` | agent, dashboard: the claim with its decision and payment |
| `get_policy` | `GET /api/policies/{policy_id}` | agent, dashboard |
| `get_claim_history` | `GET /api/customers/{customer_id}/claims` | agent, dashboard: previous claims only, no contact details |
| `get_plan` | `GET /api/plans/{plan}` | agent: limits, deductible and add-ons |
| `get_policy_wording` | `GET /api/policy-wording` | agent |
| `get_instructions` | `GET /api/instructions` | agent, dashboard |
| `list_handlers` | `GET /api/handlers` | dashboard |
| `start_claim` | `POST /api/claims/{claim_id}/start` | agent run |
| `add_step` | `POST /api/claims/{claim_id}/steps` | agent run |
| `list_steps` | `GET /api/claims/{claim_id}/steps` | dashboard |
| `decide_claim` | `POST /api/claims/{claim_id}/decision` | agent: decision, payout, reason, policy section |
| `pay_claim` | `POST /api/claims/{claim_id}/payment` | agent: takes the amount |
| `sign_off_claim` | `POST /api/claims/{claim_id}/sign-off` | dashboard: takes the handler id, pays the approved payout |
| `run_agent` | `POST /api/claims/{claim_id}/run` | dashboard: starts the agent in the background |

`pay_claim` is refused with 409 unless the claim is approved, the amount equals the approved payout, and the payout is at most $1,000 or a handler has signed off. Refusals come back to the agent as a tool result it can read, not a crash.

## Phase 1: Records and read API

Build `backend/db.py` (schema, connection, seeding from `data/`) and the read operations: `list_claims`, `get_claim`, `get_policy`, `get_claim_history`, `get_plan`, `get_policy_wording`, `get_instructions`, `list_handlers`. Write a first version of `backend/instructions.md`.

- [x] `uv run pytest -q backend` passes, with a fresh database per test.
- [x] Seeding a new database gives 25 claims, all `waiting`; seeding twice does not duplicate them.
- [x] `GET /api/claims` returns 25 rows with `claim_id`, `summary`, `claim_type`, `amount_claimed`, `status`.
- [x] `GET /api/claims/CLM-1001` returns the story, items and documents, with `decision` and `payment` null.
- [x] `GET /api/claims/CLM-9999` returns 404.
- [x] `GET /api/customers/CUS-3001/claims` returns the previous claims and no email, phone or address.
- [x] `GET /api/plans/premium` returns the premium limits, the deductible rule and the add-ons.
- [x] `GET /api/policy-wording` and `GET /api/instructions` return the markdown text.
- [x] A test checks that the seed reads only the named files in `data/`, and that no GET response carries eval fields (`failure_class`, `difficulty`, `tiny`, as listed in `data/README.md`).
- [x] Every route in `app.openapi()` has an `operation_id` and a summary, checked by a test.

## Phase 2: Workflow and the payment rule

Add `start_claim`, `add_step`, `list_steps`, `decide_claim`, `pay_claim` and `sign_off_claim`, with the state changes above.

- [x] `start_claim` moves a `waiting` claim to `in_progress`; on a `decided` claim it returns 409.
- [x] `decide_claim` with `decline` or `refer` and payout 0 moves the claim to `decided`.
- [x] `decide_claim` with `approve` and payout $420.00, then `pay_claim` with 420.00, records the payment and moves the claim to `decided`.
- [x] `decide_claim` with `approve` and payout $1,250.00 moves the claim to `waiting_for_signoff`.
- [x] Then `pay_claim` with 1250.00 returns 409 and no payment is recorded: the rule holds even when the agent tries to pay.
- [x] `pay_claim` with an amount other than the approved payout returns 409.
- [x] `sign_off_claim` with `HND-01` records the payment of $1,250.00, the handler and the date, and moves the claim to `decided`.
- [x] `sign_off_claim` on a claim that is not waiting for sign-off returns 409; an unknown handler returns 404.
- [x] Steps posted with `add_step` come back from `list_steps` in order.
- [x] Python coverage stays at or above 80%.

## Phase 3: The UnderCover Agent

Rewrite `agent/main.py` around the API. Tools: `get_claim`, `get_policy`, `get_claim_history`, `get_plan`, `get_policy_wording`, `decide_claim`, `pay_claim`. `run(claim_id, thread_id)` fetches the instructions from `get_instructions`, calls `start_claim`, runs `create_agent` and records every step through a callback. Add `run_agent` to the backend, which runs `agent.main.run` as a background task, and `uv run -m agent CLM-1001` to run one claim from the terminal. Finish `backend/instructions.md`: read everything, decide from the policy wording, work out the payout as in its section 10, give a reason of two or three sentences and the section, pay approved claims, and never mention or look for handler decisions.

- [x] Stub-model test: the agent reads the claim, decides `approve` with $420.00 and pays; the claim ends `decided` with a payment.
- [x] Stub-model test: the agent approves $1,250.00 and tries to pay; it receives the refusal as a tool result, the run finishes, and the claim is `waiting_for_signoff` with no payment.
- [x] Stub-model test: each tool call and model reply appears in `list_steps`.
- [x] A test checks that the agent has no tool or route that reaches `data/evals/`, and that `agent/` has no path to it.
- [x] `run` uses `MODEL_NAME` when set, otherwise `openai/gpt-6-luna` with low reasoning effort (existing test kept).
- [x] `POST /api/claims/CLM-1001/run` returns 202 and the claim moves to `in_progress` (stub model in the test).
- [x] Live check, one claim, done by me with the student's key: `uv run -m agent CLM-1001` ends with a decision, a reason and a section, and `GET /api/claims/CLM-1001` shows it. Costs a few cents, or nothing with `MODEL_NAME=openrouter/free`.

## Phase 4: Dashboard: queue, claim and instructions

Three pages with a hash router: the queue (`#/`), a claim (`#/claims/CLM-1001`) and the agent's instructions (`#/instructions`). Typed API client in `dashboard/src/api.ts`. Brand from `docs/BRAND.md`: Instrument Sans, Instrument Serif and JetBrains Mono from Google Fonts; state chips in Sea Green, Marigold, Coral and Cerulean; light and dark mode from the system setting; money as $1,250.00.

- [ ] Vitest: the queue renders rows from a stubbed API with their state labels (Waiting, In progress, Waiting for sign-off, Decided) and amounts formatted as US dollars.
- [ ] Vitest: the claim page shows the story, items, documents, policy and history, and the decision, payout, reason and section when there is one.
- [ ] Vitest: the instructions page shows the text with no way to edit it.
- [ ] TypeScript coverage at or above 80%; ESLint, Prettier and tsc clean, no `any`.
- [ ] Browser check with the Playwright MCP server: the queue shows 25 claims, a claim opens, the instructions page opens, in light and dark mode.

## Phase 5: Watching the agent and signing off

On the claim page: a "Run agent" button for claims that are waiting or in progress, the agent's steps polled every two seconds while the claim is in progress, and for claims waiting for sign-off, a handler picker and a "Sign off and pay" button. The queue refreshes its states while any claim is in progress.

- [ ] Vitest: steps appear as they arrive and polling stops when the claim leaves `in_progress`.
- [ ] Vitest: signing off calls `sign_off_claim` with the chosen handler and shows the payment.
- [ ] Playwright: the queue lists 25 claims and a claim page opens.
- [ ] Playwright: a claim given an approval over $1,000 through the API shows "Waiting for sign-off"; signing off as Dana Whitfield shows it decided and paid. No model is called.
- [ ] End-to-end runs use their own database file, emptied at the start, so they never change the development data.
- [ ] Browser check with the Playwright MCP server: run the agent on one claim from the dashboard and watch the steps appear, then the decision.

## Phase 6: Working the queue and handover

Add `uv run -m agent --queue`, which runs the agent on every waiting claim in turn. Bring `docs/STATUS.md` up to date with what is built and how to run it.

- [ ] Stub-model test: `--queue` runs each waiting claim once and skips decided ones.
- [ ] `docs/STATUS.md` says what is built, how to start it (`npm run dev`), how to run the agent on a claim and on the queue, and the `UNDERCOVER_DB` setting.
- [ ] `npm run check` passes: ruff, pyright, pytest, ESLint, Prettier, tsc, vitest and Playwright.
- [ ] Every phase is committed, with the pre-commit hook passing and no `--no-verify`.

## Not in the pilot

From `docs/SPEC.md`: the claims manual, sign-in, real payments and messages to customers. Scoring the agent against `data/evals/` is a later step; the pilot only keeps the evals out of the agent's reach.

## Risks

- **Cost and model limits.** Live runs are limited to one claim in Phase 3 and one in Phase 5. Working the whole queue live is left to the student.
- **The Norton SSL setting on this machine.** If `SSLKEYLOGFILE` is set, Python dies on import of `langchain_openai`; it must be cleared in the shell before live runs.
- **The Playwright MCP server** did not connect in this session. If it is still down at implementation time, browser checks fall back to the Playwright end-to-end tests and screenshots.
