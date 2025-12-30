"""
Multi-agent orchestration patterns.

Provides various patterns for coordinating multiple agents including:
- Sequential orchestration
- Concurrent/parallel execution
- Group chat with turn-taking
- Hierarchical delegation
- Handoff patterns
"""

from pulser_agents.orchestration.base import (
    Orchestrator,
    OrchestratorConfig,
    OrchestrationResult,
)
from pulser_agents.orchestration.sequential import SequentialOrchestrator
from pulser_agents.orchestration.concurrent import ConcurrentOrchestrator
from pulser_agents.orchestration.group_chat import (
    GroupChatOrchestrator,
    GroupChatConfig,
    SpeakerSelectionMode,
)
from pulser_agents.orchestration.handoff import (
    HandoffOrchestrator,
    HandoffStrategy,
)

__all__ = [
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestrationResult",
    "SequentialOrchestrator",
    "ConcurrentOrchestrator",
    "GroupChatOrchestrator",
    "GroupChatConfig",
    "SpeakerSelectionMode",
    "HandoffOrchestrator",
    "HandoffStrategy",
]
