"""Executor: invoke a PDCA phase prompt against a scenario input.

Reads a phase prompt markdown file, sends it as system context via the
Anthropic API, and returns the model's response. API key is loaded from
.env (see .env.example).
"""

import re
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048


def strip_decision_probes(text: str) -> str:
    """Remove Decision probe blocks from prompt text before sending to the model.

    Probes are human-facing decision gates; the model should not see them.
    Pattern: **Decision probe...:** header, blank line, bullet list, trailing blank line.
    """
    return re.sub(r"\*\*Decision probe[^\n]*\n\n(?:-[^\n]*\n)+\n?", "", text)


def _make_client() -> Any:
    """Create and return an Anthropic client. Lazy import keeps anthropic
    out of the test dependency group — unit tests inject a mock instead."""
    import anthropic  # type: ignore[import-untyped]
    from dotenv import load_dotenv  # type: ignore[import-untyped]
    load_dotenv()
    return anthropic.Anthropic()


def run_phase(
    phase_prompt_path: Path,
    scenario_input: str,
    model: str = DEFAULT_MODEL,
    _client: Any = None,
    include_skill_prompt: bool = True,
) -> str:
    """Run a PDCA phase prompt against a scenario input.

    Args:
        phase_prompt_path: Path to the phase prompt markdown file to use
                           as system context.
        scenario_input: The user's coding scenario description.
        model: Claude model identifier to use.
        _client: Anthropic client instance. If None, one is created from
                 the environment (production path). Pass a mock for testing.

    Returns:
        The model's response as a string.
    """
    client = _client if _client is not None else _make_client()
    kwargs: dict = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": scenario_input}],
    }
    if include_skill_prompt:
        kwargs["system"] = strip_decision_probes(phase_prompt_path.read_text())
    response = client.messages.create(**kwargs)
    return response.content[0].text
