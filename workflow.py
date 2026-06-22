import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
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

# ADK 2.0+ requires to run agent in a Runner function for internal handling
async def execute_agent(agent: Agent, prompt: str) -> str:
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    events = await runner.run_debug(prompt)
    final_event = events[-1]
    print(f"\n[DEBUG] final_event attributes: {dir(final_event)}")
    return final_event

# 2. Defining State Functions
async def generate_context(state: ReviewState) -> ReviewState:
    print("[1/4] Generating Architectural Context...")
    state.context = await execute_agent(context_agent, state.code_snippet)
    
    # DEBUG: See what ADK actually gave us
    print(f"  -> DEBUG: Data came back as: {type(state.context)}")
    return state

async def run_reviews(state: ReviewState) -> ReviewState:
    print(f"[2/4] Running Security & Performance Audits concurrently...")
    # Give agents the code and context
    prompt_payload = f"Code:\n{state.code_snippet}\n\nContext:\n{state.context.model_dump_json()}"

    # ADK executing them concurrently
    security_task = execute_agent(security_agent, prompt_payload)
    performance_task = execute_agent(performance_agent, prompt_payload)

    state.security_findings, state.performance_findings = await asyncio.gather(security_task, performance_task)
    
    return state

async def combination_report(state: ReviewState) -> ReviewState:
    print("[3/4] Arbitrating conflicts and formatting final report...")
    
    prompt_payload = f"""
    Context: {state.context.model_dump_json()}
    Security Findings: {state.security_findings}
    Performance Findings: {state.performance_findings}
    """
    state.final_report = await execute_agent(coordinator_agent, prompt_payload)
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

# 4. Map the steps

review_workflow = PRReviewPipeline()

review_workflow.add_step(generate_context)
review_workflow.add_step(run_reviews)
review_workflow.add_step(combination_report)