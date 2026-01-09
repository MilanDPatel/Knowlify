"""Prompts for Maniflow document processing."""

from maniflow.prompts.animate import (
    MANIM_CODING_AGENT_PROMPT,
    SCENE_BOILERPLATE,
    format_storyboard_prompt,
)
from maniflow.prompts.breakdown import BREAKDOWN_PROMPT
from maniflow.prompts.storyboard import STORYBOARD_PROMPT, format_topic_input

__all__ = [
    "BREAKDOWN_PROMPT",
    "MANIM_CODING_AGENT_PROMPT",
    "SCENE_BOILERPLATE",
    "STORYBOARD_PROMPT",
    "format_storyboard_prompt",
    "format_topic_input",
]

