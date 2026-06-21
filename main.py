import asyncio
from models.review_state import ReviewState
from workflow import review_workflow

async def main(code: str):
    # print("Hello from code-review-agent!")
    # Initalize typed states
    initial_state = ReviewState(code)

    final_state = await review_workflow.execute(initial_state)

    print("\n[4/4] Pipeline Complete. Saving report!...")   

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(final_state.final_report)
        
    print("Saved to report.md")

if __name__ == "__main__":
    asyncio.run(main())
