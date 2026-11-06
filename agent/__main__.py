"""Run the UnderCover Agent from the terminal: uv run -m agent CLM-1001."""

import argparse
from uuid import uuid4

from agent.main import run


def main() -> None:
    """Run the agent on the claim named on the command line."""
    parser = argparse.ArgumentParser(prog="uv run -m agent")
    parser.add_argument("claim_id", help="the claim to decide, such as CLM-1001")
    arguments = parser.parse_args()
    print(run(arguments.claim_id, uuid4().hex))


if __name__ == "__main__":
    main()
