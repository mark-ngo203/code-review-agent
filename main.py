import asyncio
import os
from models.review_state import ReviewState
from agents.workflow import review_workflow
from dotenv import load_dotenv

load_dotenv()

TEST_CODE = """
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


async def main():
    # print("Hello from code-review-agent!")
    # Initalize typed states
    initial_state = ReviewState(code_snippet=TEST_CODE)

    final_state = await review_workflow.execute(initial_state)

    print("\n[4/4] Pipeline Complete. Saving report!...")

    os.makedirs("reports", exist_ok=True)
    if not final_state.final_report:
        raise RuntimeError("Pipeline finished without a final report")

    with open("reports/report.md", "w", encoding="utf-8") as f:
        f.write(final_state.final_report)

    print("Saved to reports/report.md")

if __name__ == "__main__":
    asyncio.run(main())
