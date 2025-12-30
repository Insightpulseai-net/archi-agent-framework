"""
Basic agent usage example.

Demonstrates creating and using a simple agent with tools.
"""

import asyncio

from pulser_agents import Agent, AgentConfig
from pulser_agents.core.agent import tool
from pulser_agents.providers import OpenAIChatClient
from pulser_agents.core.base_client import ChatClientConfig


# Define tools using the @tool decorator
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Mock implementation
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Cloudy, 55°F",
        "tokyo": "Rainy, 65°F",
        "paris": "Partly cloudy, 68°F",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        # Safe evaluation of basic math expressions
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information."""
    # Mock implementation
    knowledge = {
        "python": "Python is a high-level programming language known for readability.",
        "javascript": "JavaScript is the language of the web, used for frontend and backend.",
        "rust": "Rust is a systems programming language focused on safety and performance.",
    }

    for key, value in knowledge.items():
        if key in query.lower():
            return value

    return f"No results found for: {query}"


async def main():
    """Run the basic agent example."""
    # Create the chat client
    client = OpenAIChatClient(
        config=ChatClientConfig(
            model="gpt-4o-mini",
            temperature=0.7,
        )
    )

    # Create the agent
    agent = Agent(
        config=AgentConfig(
            name="assistant",
            description="A helpful assistant that can check weather, do math, and search a knowledge base.",
            system_prompt="""You are a helpful assistant with access to the following tools:
- get_weather: Check weather for any city
- calculate: Evaluate math expressions
- search_knowledge_base: Search for information

Use these tools when appropriate to help answer user questions.
""",
            max_iterations=5,
        ),
        client=client,
        tools=[get_weather, calculate, search_knowledge_base],
    )

    print("Basic Agent Example")
    print("=" * 50)

    # Example conversations
    queries = [
        "What's the weather like in New York?",
        "What is 25 * 4 + 10?",
        "Tell me about Python programming",
        "What's 15% of 200 and what's the weather in London?",
    ]

    for query in queries:
        print(f"\nUser: {query}")
        result = await agent.run(query)
        print(f"Assistant: {result.content}")
        print(f"  (Iterations: {result.iterations}, Tokens: {result.total_usage.total_tokens})")

    # Clean up
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
