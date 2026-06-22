import asyncio
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
    response = await context_agent.run(state.code_snippet)
    state.context = response.data
    return state

async def run_reviews(state: ReviewState) -> ReviewState:
    print(f"[2/4] Running Security & Performance Audits concurrently...")
    # Give agents the code and context
    prompt_payload = f"Code:\n{state.code_snippet}\n\nContext:\n{state.context.model_dump_()}"

    # ADK executing them concurrently
    security_task = security_agent.run_async(prompt_payload)
    performance_task = performance_agent.run_async(prompt_payload)

    security_result, performance_result = await asyncio.gather(security_task, performance_task)

    state.security_findings = security_result
    state.performance_findings = performance_result
    
    return state

async def combination_report(state: ReviewState) -> ReviewState:
    print("[3/4] Arbitrating conflicts and formatting final report...")
    
    prompt_payload = f"""
    Context: {state.context.model_dump_json()}
    Security Findings: {[f.model_dump for f in state.seucrity_findings]}
    Performance Findings: {[f.model_dump for f in state.performance_findings]}
    """
    response = await coordinator_agent.run(prompt_payload)
    state.final_report = response.data
    return state

# 3. Mapping the Directed Graph 
review_workflow = Workflow(
    name="pr_review_pipeline",
    initial_state=ReviewState
)

# 4. Map the steps
review_workflow.add_step(generate_context)
review_workflow.add_step(run_reviews)
review_workflow.add_step(combination_report)