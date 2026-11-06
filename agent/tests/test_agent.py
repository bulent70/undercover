import sys
from pathlib import Path

from langchain_core.messages import AIMessage

from agent import __main__ as cli
from agent import main
from backend import db, workflow
from backend.main import app

CLAIM = "/api/claims/CLM-1001"


def tool_call(name, number, **args):
    return {"name": name, "args": args, "id": str(number)}


def deciding(payout, final_reply):
    return [
        AIMessage(
            content="I will read the claim and the policy.",
            tool_calls=[
                tool_call("get_claim", 1, claim_id="CLM-1001"),
                tool_call("get_policy", 2, policy_id="POL-2001"),
                tool_call("get_plan", 3, plan="premium"),
                tool_call("get_claim_history", 4, customer_id="CUS-3001"),
                tool_call("get_policy_wording", 5),
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                tool_call(
                    "decide_claim",
                    6,
                    claim_id="CLM-1001",
                    decision="approve",
                    payout=payout,
                    reason="The flight was canceled. The costs are covered.",
                    section="3. Trip Delay",
                )
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[tool_call("pay_claim", 7, claim_id="CLM-1001", amount=payout)],
        ),
        AIMessage(content=final_reply),
    ]


def test_approve_and_pay(backend, stub_model):
    reply = main.run(
        "CLM-1001", "thread-1", stub_model(deciding(420.0, "Approved and paid."))
    )
    assert reply == "Approved and paid."
    claim = backend.get(CLAIM).json()
    assert claim["status"] == "decided"
    assert claim["decision"]["section"] == "3. Trip Delay"
    assert claim["payment"]["amount"] == 420.0


def test_payment_over_the_limit_is_refused(backend, stub_model):
    reply = main.run(
        "CLM-1001", "thread-1", stub_model(deciding(1250.0, "Waiting for sign-off."))
    )
    assert reply == "Waiting for sign-off."
    claim = backend.get(CLAIM).json()
    assert claim["status"] == "waiting_for_signoff"
    assert claim["payment"] is None
    results = [
        step["text"]
        for step in backend.get(f"{CLAIM}/steps").json()
        if step["text"].startswith("pay_claim:")
    ]
    assert "needs a handler's sign-off" in results[0]


def test_every_step_is_recorded(backend, stub_model):
    main.run("CLM-1001", "thread-1", stub_model(deciding(420.0, "Done.")))
    steps = backend.get(f"{CLAIM}/steps").json()
    kinds = [step["kind"] for step in steps]
    assert kinds.count("tool_call") == 7
    assert kinds.count("tool_result") == 7
    assert steps[0] == steps[0] | {
        "kind": "model",
        "text": "I will read the claim and the policy.",
    }
    assert steps[1]["text"] == 'get_claim {"claim_id": "CLM-1001"}'
    assert steps[-1]["text"] == "Done."


def test_the_agent_cannot_reach_the_evals():
    names = {tool.name for tool in main.TOOLS}
    assert names == {
        "get_claim",
        "get_policy",
        "get_claim_history",
        "get_plan",
        "get_policy_wording",
        "decide_claim",
        "pay_claim",
    }
    assert not [route for route in app.routes if "eval" in getattr(route, "path", "")]
    for source in Path(main.__file__).parent.glob("*.py"):
        assert "evals" not in source.read_text(encoding="utf-8")
    assert "evals" not in main.TOOLS[0].description


def test_run_agent_route(backend, monkeypatch):
    started = []
    monkeypatch.setattr(workflow, "run_in_background", started.append)
    response = backend.post(f"{CLAIM}/run")
    assert response.status_code == 202
    assert response.json()["status"] == "in_progress"
    assert started == ["CLM-1001"]


def test_run_in_background(monkeypatch):
    runs = []
    monkeypatch.setattr(main, "run", lambda claim_id, thread_id: runs.append(claim_id))
    workflow.run_in_background("CLM-1001")
    assert runs == ["CLM-1001"]


def test_command_line(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["agent", "CLM-1001"])
    monkeypatch.setattr(cli, "run", lambda claim_id, thread_id: f"Decided {claim_id}")
    cli.main()
    assert capsys.readouterr().out == "Decided CLM-1001\n"


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    assert main.model().reasoning_effort == "low"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"


def declining(claim_id):
    return [
        AIMessage(
            content="",
            tool_calls=[
                tool_call(
                    "decide_claim",
                    1,
                    claim_id=claim_id,
                    decision="decline",
                    payout=0,
                    reason="Not covered.",
                    section="9. General exclusions",
                )
            ],
        ),
        AIMessage(content=f"Declined {claim_id}."),
    ]


def test_queue_runs_each_waiting_claim_once(backend, stub_model):
    connection = db.connect()
    connection.execute(
        "UPDATE claims SET status = 'decided' WHERE claim_id NOT IN (?, ?)",
        ("CLM-1002", "CLM-1005"),
    )
    connection.commit()
    replies = main.run_queue(stub_model(declining("CLM-1002") + declining("CLM-1005")))
    assert replies == {
        "CLM-1002": "Declined CLM-1002.",
        "CLM-1005": "Declined CLM-1005.",
    }
    statuses = {claim["status"] for claim in backend.get("/api/claims").json()}
    assert statuses == {"decided"}


def test_command_line_queue(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["agent", "--queue"])
    monkeypatch.setattr(cli, "run_queue", lambda: {"CLM-1001": "Approved."})
    cli.main()
    assert capsys.readouterr().out == "CLM-1001: Approved.\n"
