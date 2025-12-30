"""
Multi-agent orchestration example.

Demonstrates sequential, concurrent, and group chat orchestration patterns.
"""

import asyncio

from pulser_agents import Agent, AgentConfig
from pulser_agents.providers import OpenAIChatClient
from pulser_agents.core.base_client import ChatClientConfig
from pulser_agents.orchestration import (
    SequentialOrchestrator,
    ConcurrentOrchestrator,
    GroupChatOrchestrator,
    GroupChatConfig,
    SpeakerSelectionMode,
    OrchestratorConfig,
)


def create_client() -> OpenAIChatClient:
    """Create a chat client."""
    return OpenAIChatClient(
        config=ChatClientConfig(
            model="gpt-4o-mini",
            temperature=0.7,
        )
    )


async def sequential_example():
    """
    Sequential orchestration: Research -> Write -> Review pipeline.
    """
    print("\n" + "=" * 50)
    print("Sequential Orchestration Example")
    print("=" * 50)

    # Create specialized agents
    researcher = Agent(
        config=AgentConfig(
            name="researcher",
            description="Researches topics and gathers information",
            system_prompt="""You are a research specialist. Given a topic, provide
key facts, statistics, and insights that would be useful for writing an article.
Be concise but comprehensive.""",
        ),
        client=create_client(),
    )

    writer = Agent(
        config=AgentConfig(
            name="writer",
            description="Writes engaging content based on research",
            system_prompt="""You are a content writer. Given research notes,
write an engaging article or summary. Focus on clarity and flow.
Keep it under 200 words.""",
        ),
        client=create_client(),
    )

    editor = Agent(
        config=AgentConfig(
            name="editor",
            description="Edits and improves written content",
            system_prompt="""You are an editor. Review the provided content and
improve it for clarity, grammar, and engagement. Provide the improved version.""",
        ),
        client=create_client(),
    )

    # Create sequential orchestrator
    orchestrator = SequentialOrchestrator(
        agents=[researcher, writer, editor],
        config=OrchestratorConfig(
            name="content-pipeline",
            max_iterations=10,
        ),
    )

    # Run the pipeline
    result = await orchestrator.run(
        "Write about the benefits of meditation for mental health"
    )

    print(f"\nFinal Output:\n{result.content}")
    print(f"\nAgents involved: {result.agents_involved}")
    print(f"Total iterations: {result.iterations}")

    # Clean up
    await researcher.close()
    await writer.close()
    await editor.close()


async def concurrent_example():
    """
    Concurrent orchestration: Multiple analysts reviewing same data.
    """
    print("\n" + "=" * 50)
    print("Concurrent Orchestration Example")
    print("=" * 50)

    # Create multiple analyst agents
    analyst1 = Agent(
        config=AgentConfig(
            name="technical-analyst",
            system_prompt="""You are a technical analyst. Analyze the given topic
from a technical/implementation perspective. Be brief (50 words max).""",
        ),
        client=create_client(),
    )

    analyst2 = Agent(
        config=AgentConfig(
            name="business-analyst",
            system_prompt="""You are a business analyst. Analyze the given topic
from a business/market perspective. Be brief (50 words max).""",
        ),
        client=create_client(),
    )

    analyst3 = Agent(
        config=AgentConfig(
            name="risk-analyst",
            system_prompt="""You are a risk analyst. Analyze the given topic
for potential risks and challenges. Be brief (50 words max).""",
        ),
        client=create_client(),
    )

    # Create concurrent orchestrator
    orchestrator = ConcurrentOrchestrator(
        agents=[analyst1, analyst2, analyst3],
        config=OrchestratorConfig(name="multi-analysis"),
    )

    # Run all analysts in parallel
    result = await orchestrator.run(
        "Adopting AI agents for customer service automation"
    )

    print(f"\nCombined Analysis:\n{result.content}")
    print(f"\nAgents involved: {result.agents_involved}")

    # Clean up
    await analyst1.close()
    await analyst2.close()
    await analyst3.close()


async def group_chat_example():
    """
    Group chat orchestration: Team discussion.
    """
    print("\n" + "=" * 50)
    print("Group Chat Orchestration Example")
    print("=" * 50)

    # Create team members
    developer = Agent(
        config=AgentConfig(
            name="developer",
            description="Software developer with technical expertise",
            system_prompt="""You are a software developer in a team discussion.
Contribute your technical perspective. Keep responses under 50 words.
Say TERMINATE when you think the discussion has reached a conclusion.""",
        ),
        client=create_client(),
    )

    designer = Agent(
        config=AgentConfig(
            name="designer",
            description="UX designer focused on user experience",
            system_prompt="""You are a UX designer in a team discussion.
Contribute your design perspective. Keep responses under 50 words.
Say TERMINATE when you think the discussion has reached a conclusion.""",
        ),
        client=create_client(),
    )

    pm = Agent(
        config=AgentConfig(
            name="product-manager",
            description="Product manager coordinating the team",
            system_prompt="""You are a product manager in a team discussion.
Help coordinate and summarize. Keep responses under 50 words.
Say TERMINATE when you think the discussion has reached a conclusion.""",
        ),
        client=create_client(),
    )

    # Create group chat orchestrator
    orchestrator = GroupChatOrchestrator(
        agents=[developer, designer, pm],
        config=GroupChatConfig(
            name="team-chat",
            speaker_selection=SpeakerSelectionMode.ROUND_ROBIN,
            max_iterations=6,
            termination_phrase="TERMINATE",
        ),
    )

    # Start the discussion
    result = await orchestrator.run(
        "Let's discuss how to improve our mobile app's onboarding experience"
    )

    print(f"\nDiscussion Transcript:")
    print(orchestrator.get_transcript())
    print(f"\nTotal turns: {result.iterations}")

    # Clean up
    await developer.close()
    await designer.close()
    await pm.close()


async def main():
    """Run all orchestration examples."""
    print("Multi-Agent Orchestration Examples")
    print("=" * 50)

    await sequential_example()
    await concurrent_example()
    await group_chat_example()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
