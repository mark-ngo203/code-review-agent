import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agents.tools import InputError, ResolvedCodeInput, resolve_code_input
from agents.workflow import review_workflow
from models.review_state import ReviewState

DEMO_CODE = """
    def fetch_user_data(user_id):
        # Connect to DB
        db = connect('financial_db')
        # Vulnerability: string interpolation in SQL
        query = f"SELECT account_balance, ssn FROM users WHERE id = {user_id}"
        user = db.execute(query).fetchone()

        # Bottleneck: N+1 loop with blocking sleep
        txs = []
        for tx_id in db.execute(f"SELECT tx_id FROM tx_map WHERE user_id={user_id}").fetchall():
            import time; time.sleep(0.1)
            txs.append(db.execute(f"SELECT * FROM transactions WHERE id={tx_id}").fetchone())

        return {"user": user, "transactions": txs}
    """


REPORTS_DIR = Path("reports")


def resolve_output_path(output: str) -> Path:
    path = Path(output)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == REPORTS_DIR.name:
        return path
    return REPORTS_DIR / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the multi-agent code review pipeline.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--code",
        help="Raw source code string to review.",
    )
    source.add_argument(
        "--file",
        help="Path to a source file (use - for stdin).",
    )
    source.add_argument(
        "--pr",
        help="GitHub PR URL or owner/repo#number.",
    )
    source.add_argument(
        "--demo",
        action="store_true",
        help="Run with the built-in sample code.",
    )
    parser.add_argument(
        "--output",
        default="report.md",
        help="Report filename or path (default: reports/report.md).",
    )
    return parser


def load_review_input(args: argparse.Namespace):
    if args.demo:
        return ResolvedCodeInput(
            code=DEMO_CODE,
            source_type="string",
            source_label="demo sample",
        )

    return resolve_code_input(code=args.code, file=args.file, pr=args.pr)


async def main() -> None:
    args = build_parser().parse_args()

    try:
        resolved = load_review_input(args)
    except InputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Reviewing {resolved.source_label} ({resolved.source_type})...")

    initial_state = ReviewState(
        code_snippet=resolved.code,
        source_type=resolved.source_type,
        source_label=resolved.source_label,
    )

    final_state = await review_workflow.execute(initial_state)

    print("\n[4/4] Pipeline Complete. Saving report!...")

    output_path = resolve_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not final_state.final_report:
        raise RuntimeError("Pipeline finished without a final report")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_state.final_report)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
