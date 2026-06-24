import asyncio
import os

from google.adk import Agent
from agents.instructions import (
    CONTEXT_PROMPT, 
    SECURITY_PROMPT, 
    PERFORMANCE_PROMPT, 
    COORDINATOR_PROMPT
)
from agents.mock_data import (
    MOCK_CONTEXT,
    MOCK_PERFORMANCE_FINDINGS,
    MOCK_SECURITY_FINDINGS,
)
from agents.prompts import build_coordinator_prompt, build_review_prompt
from agents.runner import run_structured_agent
from models.context_model import ContextModel
from models.finding_model import FindingModel
from models.report_output import ReportOutput
from models.review_state import ReviewState

context_agent = Agent(
    name="context_architect",
    model="gemini-2.5-flash",
    instruction=CONTEXT_PROMPT,
    output_schema=ContextModel,
)

security_agent = Agent(
    name="security_reviewer",
    model="gemini-2.5-flash",
    instruction=SECURITY_PROMPT,
    output_schema=list[FindingModel],
)

performance_agent = Agent(
    name="performance_reviewer",
    model="gemini-2.5-flash",
    instruction=PERFORMANCE_PROMPT,
    output_schema=list[FindingModel],
)

coordinator_agent = Agent(
    name="coordinator",
    model="gemini-2.5-flash",
    instruction=COORDINATOR_PROMPT,
    output_schema=ReportOutput,
)


# 2. Defining State Functions
async def generate_context(state: ReviewState) -> ReviewState:
    print("[1/4] Generating Architectural Context...")
    state.context = await run_structured_agent(
        context_agent, state.code_snippet, ContextModel
    )
    return state


async def run_reviews(state: ReviewState) -> ReviewState:
    print("[2/4] Running Security & Performance Reviews...")
    prompt = build_review_prompt(state)

    security_task = run_structured_agent(
        security_agent, prompt, list[FindingModel]
    )
    performance_task = run_structured_agent(
        performance_agent, prompt, list[FindingModel]
    )

    state.security_findings, state.performance_findings = await asyncio.gather(
        security_task, performance_task
    )
    return state

# 3. Combining Reports
async def combination_report(state: ReviewState) -> ReviewState:
    print("[3/4] Arbitrating conflicts and formatting final report...")
    report = await run_structured_agent(
        coordinator_agent,
        build_coordinator_prompt(state),
        ReportOutput,
    )
    state.final_report = report.markdown
    return state

# Custom pipeline coordinator
class PRReviewPipeline:
    def __init__(self):
        self.steps = []

    def add_step(self, func):
        self.steps.append(func)

    async def execute(self, state: ReviewState) -> ReviewState:
        current_state = state
        for step in self.steps:
            current_state = await step(current_state)
        return current_state

# Testing — injects mock context/findings; coordinator still calls Gemini
async def mock_context_and_reviews(state: ReviewState) -> ReviewState:
    print("[TEST] Injecting mock context and findings (coordinator will still run)...")

    state.context = MOCK_CONTEXT
    state.security_findings = MOCK_SECURITY_FINDINGS
    state.performance_findings = MOCK_PERFORMANCE_FINDINGS

    return state


MOCK_MODE = os.getenv("MOCK_MODE", "").lower() in ("true")

# 4. Map the steps
review_workflow = PRReviewPipeline()

if MOCK_MODE:
    review_workflow.add_step(mock_context_and_reviews)
    review_workflow.add_step(combination_report)
else:
    review_workflow.add_step(generate_context)
    review_workflow.add_step(run_reviews)
    review_workflow.add_step(combination_report)
