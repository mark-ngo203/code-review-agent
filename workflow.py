from google.adk import Agent, Workflow
from models.context_model import ContextModel
from models.finding_model import FindingModel 
from models.review_state import ReviewState
from agents.instructions import (
    CONTEXT_PROMPT, 
    SECURITY_PROMPT, 
    PERFORMANCE_PROMPT, 
    COORDINATOR_PROMPT
)

# 1. Definding Agents, with structural output for consistency. 
context_agent = Agent(
    name="context_architect",
    model="gemini-2.5-flash",
    instruction=CONTEXT_PROMPT,
    output_schema=ContextModel
)

security_agent = Agent(
    name="security_reviewer",
    model="gemini-2.5-flash",
    instruction=SECURITY_PROMPT,
    output_schema=list[FindingModel]
)

performance_agent = Agent(
    name="performance_reviewer",
    model="gemini-2.5-flash",
    instruction=PERFORMANCE_PROMPT,
    output_schema=list[FindingModel]
)

coordinator_agent = Agent(
    name="coordinator",
    model="gemini-2.5-flash",
    instruction=COORDINATOR_PROMPT,
    # The coordinator outputs a raw string for the markdown file
    output_schema=str 
)

# 2. Defining State Functions
async def generate_context(state: ReviewState) -> ReviewState:
    print("[1/4] Generating Architectural Context...")
    # TODO 
    # Call context_agent
    return

async def run_reviews(state: ReviewState) -> ReviewState:
    print(f"[2/4] Running Security & Performance Audits concurrently...")
    # TODO 
    # Using state.context.model_dump_json() to get all the information from context
    # Running each agent
    return

async def combination_report(state: ReviewState) -> ReviewState:
    print("[3/4] Arbitrating conflicts and formatting final report...")
    # TODO 
    # Using state.context.model_dump_json() for context
    # Loop through findings for both using state.security_finding and state.performance_findings
    # [f.model_dump() for f in state.security_findings]
    return

# 3. Mapping the Directed Graph 
review_workflow = Workflow(
    name="pr_review_pipeline",
    initial_state=ReviewState
)

# 4. Map the steps
review_workflow.add_step(generate_context)
review_workflow.add_step(run_reviews)
review_workflow.add_step(combination_report)