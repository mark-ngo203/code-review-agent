from google.adk import Agent
from google.adk.events.event import Event
from google.adk.runners import InMemoryRunner
from google.adk.utils.content_utils import extract_text_from_content
from pydantic import TypeAdapter, ValidationError

# Raised when an agent returns no usable structured output.
class AgentOutputError(RuntimeError):

    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"{agent_name}: {message}")


def _find_final_event(events: list[Event]) -> Event:
    for event in reversed(events):
        if event.is_final_response():
            return event
    if not events:
        raise AgentOutputError("unknown", "agent returned no events")
    return events[-1]

# Run an ADK agent and parse its final response into schema.
# Purposely abstracted as python can't assume ContextModel from agent.output_schema, so we have to validate the schema manually.
# Though causes DRY violations.
async def run_structured_agent[T](agent: Agent, prompt: str, schema: type[T]) -> T:
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    events = await runner.run_debug(prompt, quiet=True)
    text = extract_text_from_content(_find_final_event(events).content)

    if not text.strip():
        raise AgentOutputError(agent.name, "empty response")

    try:
        return TypeAdapter(schema).validate_json(text)
    except ValidationError as exc:
        raise AgentOutputError(
            agent.name, f"invalid structured output: {exc}"
        ) from exc
