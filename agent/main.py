"""The UnderCover Agent: decides one claim through the backend's API."""

import json
import os
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://127.0.0.1:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
RECURSION_LIMIT = 50


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    """Call the backend for the run itself, raising on any error."""
    with backend() as client:
        response = client.request(method, path, json=body)
    response.raise_for_status()
    return response.json()


def call(method: str, path: str, body: dict[str, Any] | None = None) -> str:
    """Call the backend for a tool; refusals come back as text the model can read."""
    with backend() as client:
        response = client.request(method, path, json=body)
    if response.is_server_error:
        response.raise_for_status()
    return response.text


@tool
def get_claim(claim_id: str) -> str:
    """Get a claim: the story, the items claimed, the documents and its status."""
    return call("GET", f"/api/claims/{claim_id}")


@tool
def get_policy(policy_id: str) -> str:
    """Get a policy by the policy_id on the claim, such as POL-2001."""
    return call("GET", f"/api/policies/{policy_id}")


@tool
def get_claim_history(customer_id: str) -> str:
    """Get previous claims by the customer_id on the claim, such as CUS-3001."""
    return call("GET", f"/api/customers/{customer_id}/claims")


@tool
def get_plan(plan: str) -> str:
    """Get a plan's limits, waiting periods, deductible and the add-ons."""
    return call("GET", f"/api/plans/{plan}")


@tool
def get_policy_wording() -> str:
    """Get the policy wording, the contract that decisions follow."""
    return call("GET", "/api/policy-wording")


@tool
def decide_claim(
    claim_id: str,
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    reason: str,
    section: str,
) -> str:
    """Record the decision, the payout in US dollars (0 unless approved), a reason of
    two or three sentences and the section of the policy wording it rests on."""
    body = {
        "decision": decision,
        "payout": payout,
        "reason": reason,
        "section": section,
    }
    return call("POST", f"/api/claims/{claim_id}/decision", body)


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Pay an approved claim the approved payout in US dollars."""
    return call("POST", f"/api/claims/{claim_id}/payment", {"amount": amount})


TOOLS = [
    get_claim,
    get_policy,
    get_claim_history,
    get_plan,
    get_policy_wording,
    decide_claim,
    pay_claim,
]


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def steps(message: BaseMessage) -> list[dict[str, str]]:
    """Turn one message of the run into the steps the dashboard shows."""
    if isinstance(message, ToolMessage):
        return [{"kind": "tool_result", "text": f"{message.name}: {message.text}"}]
    if not isinstance(message, AIMessage):
        return []
    replies = [{"kind": "model", "text": message.text}] if message.text else []
    return replies + [
        {"kind": "tool_call", "text": f"{call['name']} {json.dumps(call['args'])}"}
        for call in message.tool_calls
    ]


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Run the agent on one claim, recording each step, and return its final reply."""
    instructions = request("GET", "/api/instructions")["text"]
    request("POST", f"/api/claims/{claim_id}/start")
    agent = create_agent(llm or model(), tools=TOOLS, system_prompt=instructions)
    reply = ""
    for update in agent.stream(
        {"messages": [{"role": "user", "content": f"Please decide claim {claim_id}."}]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": RECURSION_LIMIT,
        },
        stream_mode="updates",
    ):
        for node in update.values():
            for message in node["messages"]:
                for step in steps(message):
                    request("POST", f"/api/claims/{claim_id}/steps", step)
                if isinstance(message, AIMessage):
                    reply = message.text
    return reply
