"""
Maniflow - Educational video generation from documents
"""

from maniflow.client import ManiflowAnimationClient, ManiflowBreakdownClient, ManiflowClient
from maniflow.models import AnimationResult, AtomicTopic, Breakdown, Scene, TopicStoryboard

__version__ = "0.1.0"

__all__ = [
    "AnimationResult",
    "AtomicTopic",
    "Breakdown",
    "ManiflowAnimationClient",
    "ManiflowBreakdownClient",
    "ManiflowClient",  # Backwards compatibility alias for ManiflowBreakdownClient
    "Scene",
    "TopicStoryboard",
]

