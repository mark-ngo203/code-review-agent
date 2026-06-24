import json

from models.review_state import ReviewState


class PipelineStateError(ValueError):
    """Raised when a pipeline step runs with incomplete state."""


def build_review_prompt(state: ReviewState) -> str:
    if state.context is None:
        raise PipelineStateError("Context must be generated before running reviews")

    source = f"Source ({state.source_type}): {state.source_label}\n" if state.source_label else ""
    return (
        f"{source}"
        f"Code:\n{state.code_snippet}\n\n"
        f"Context:\n{state.context.model_dump_json()}"
    )


def build_coordinator_prompt(state: ReviewState) -> str:
    if state.context is None:
        raise PipelineStateError("Context is required for the coordinator")

    source = f"Source ({state.source_type}): {state.source_label}\n" if state.source_label else ""
    return (
        f"{source}"
        f"Context: {state.context.model_dump_json()}\n"
        f"Security Findings: {json.dumps([f.model_dump() for f in state.security_findings])}\n"
        f"Performance Findings: {json.dumps([f.model_dump() for f in state.performance_findings])}"
    )
