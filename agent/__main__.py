"""Run the UnderCover Agent from the terminal.

uv run -m agent CLM-1001 decides one claim; uv run -m agent --queue decides
every waiting claim in turn.
"""

import argparse
from uuid import uuid4

from agent.main import run, run_queue


def main() -> None:
    """Run the agent on the claim named on the command line, or on the queue."""
    parser = argparse.ArgumentParser(prog="uv run -m agent")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("claim_id", nargs="?", help="the claim to decide")
    target.add_argument("--queue", action="store_true", help="every waiting claim")
    arguments = parser.parse_args()
    if not arguments.queue:
        print(run(arguments.claim_id, uuid4().hex))
        return
    for claim_id, reply in run_queue().items():
        print(f"{claim_id}: {reply}")


if __name__ == "__main__":
    main()
