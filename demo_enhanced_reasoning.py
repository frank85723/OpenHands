#!/usr/bin/env python3
"""
Demo script for the Enhanced Reasoning Agent.
This script demonstrates the capabilities of our enhanced reasoning agent
including Chain-of-Thought, Tree of Thoughts, Reflection, and Verification.
"""

from openhands.agenthub.enhanced_reasoning_agent import EnhancedReasoningAgent
from openhands.core.config import AgentConfig
from openhands.core.config.extended_config import ExtendedConfig


class MockLLM:
    """Mock LLM for demonstration purposes."""

    def __init__(self):
        self.call_count = 0
        self.responses = {
            # Strategy selection responses
            'complexity': ['chain_of_thought', 'tree_of_thoughts', 'basic'],
            # Chain of thought responses
            'reasoning': [
                """Let me solve this step by step:

1. First, I need to understand what is being asked: "What is the best way to learn AI Agent development?"

2. I should consider the key components of AI Agent development:
   - Understanding large language models and their capabilities
   - Learning about agent architectures and design patterns
   - Mastering tool integration and function calling
   - Understanding memory and context management
   - Learning about multi-agent systems and collaboration

3. I should recommend a structured learning approach:
   - Start with theoretical foundations
   - Move to hands-on implementation
   - Practice with real projects
   - Study existing frameworks like OpenHands

4. The best approach would be:
   - Begin with LLM fundamentals and prompt engineering
   - Study agent architectures and reasoning patterns
   - Implement basic agents with tool usage
   - Build more complex systems with memory and planning
   - Explore multi-agent coordination and collaboration

5. Practical recommendations:
   - Use frameworks like OpenHands for learning
   - Study research papers on agent reasoning
   - Build projects that solve real problems
   - Join communities and contribute to open source projects""",
                """Let me think through this mathematical problem step by step:

1. The problem asks: "If I have 3 apples and I buy 2 more, then give away 1, how many do I have?"

2. Let me track the changes:
   - Starting amount: 3 apples
   - Add 2 more: 3 + 2 = 5 apples
   - Give away 1: 5 - 1 = 4 apples

3. Therefore, I have 4 apples remaining.

4. Let me verify: 3 + 2 - 1 = 4 ✓""",
            ],
            # Tree of thoughts responses
            'tree_initial': [
                """[
                    {
                        "approach": "Systematic Learning Path",
                        "first_step": "Start with LLM fundamentals",
                        "rationale": "Building strong foundations is crucial for advanced topics"
                    },
                    {
                        "approach": "Project-Based Learning",
                        "first_step": "Build a simple chatbot agent",
                        "rationale": "Hands-on experience accelerates learning"
                    },
                    {
                        "approach": "Research-First Approach",
                        "first_step": "Study recent papers on agent reasoning",
                        "rationale": "Understanding cutting-edge research provides insights"
                    }
                ]""",
                """[
                    {
                        "approach": "Direct Calculation",
                        "first_step": "Add and subtract in sequence",
                        "rationale": "Straightforward arithmetic approach"
                    },
                    {
                        "approach": "Equation Method",
                        "first_step": "Set up equation: 3 + 2 - 1 = x",
                        "rationale": "Mathematical formulation ensures accuracy"
                    }
                ]""",
            ],
            # Scoring responses
            'scoring': ['0.8', '0.9', '0.7', '0.85'],
            # Terminal check responses
            'terminal': ['no', 'yes', 'no', 'yes'],
            # Child generation responses
            'children': [
                '["Study transformer architecture", "Learn about attention mechanisms", "Practice with Hugging Face"]',
                '["Build a tool-using agent", "Implement memory systems", "Add reasoning capabilities"]',
                '["Read Chain-of-Thought papers", "Study ReAct methodology", "Explore Tree of Thoughts"]',
                '["Verify calculation step by step", "Check with alternative method"]',
            ],
            # Reflection responses
            'reflection': [
                """{
                    "reflection_points": [
                        "The learning path could be more specific with timelines",
                        "Should include more practical resources and tools",
                        "Could benefit from mentioning specific projects to build"
                    ],
                    "improved_solution": "To learn AI Agent development effectively: 1) Start with LLM fundamentals (2-3 weeks) using resources like Hugging Face tutorials, 2) Study agent architectures by reading papers like ReAct and Chain-of-Thought (1-2 weeks), 3) Build hands-on projects starting with a simple tool-using agent (2-3 weeks), 4) Implement advanced features like memory and planning (2-3 weeks), 5) Explore multi-agent systems and contribute to projects like OpenHands (ongoing). Focus on building real projects that solve actual problems while studying the theoretical foundations.",
                    "confidence": 0.9
                }""",
                """{
                    "reflection_points": [
                        "The calculation is straightforward and correct",
                        "Could show the work more clearly"
                    ],
                    "improved_solution": "Starting with 3 apples, buying 2 more gives us 3 + 2 = 5 apples. After giving away 1 apple, we have 5 - 1 = 4 apples remaining.",
                    "confidence": 0.95
                }""",
            ],
            # Verification responses
            'verification': [
                'VERIFIED - This is a comprehensive and well-structured learning approach for AI Agent development',
                'VERIFIED - The arithmetic is correct: 3 + 2 - 1 = 4',
                'VERIFIED - Good systematic approach to the problem',
            ],
        }
        self.response_index = {key: 0 for key in self.responses.keys()}

    async def acompletion(self, messages, **kwargs):
        """Mock completion method."""
        self.call_count += 1

        # Determine response type based on message content
        content = messages[-1].content
        if isinstance(content, list):
            # Extract text from TextContent objects
            message_content = ' '.join(
                item.text if hasattr(item, 'text') else str(item) for item in content
            ).lower()
        else:
            message_content = content.lower()

        if 'complexity' in message_content or 'strategy' in message_content:
            response_type = 'complexity'
        elif 'generate' in message_content and 'approaches' in message_content:
            response_type = 'tree_initial'
        elif 'rate' in message_content or 'score' in message_content:
            response_type = 'scoring'
        elif 'complete solution' in message_content or 'terminal' in message_content:
            response_type = 'terminal'
        elif 'next steps' in message_content or 'child' in message_content:
            response_type = 'children'
        elif 'reflect' in message_content:
            response_type = 'reflection'
        elif 'verify' in message_content:
            response_type = 'verification'
        else:
            response_type = 'reasoning'

        # Get response
        responses = self.responses.get(response_type, ['Default response'])
        index = self.response_index[response_type] % len(responses)
        response_content = responses[index]
        self.response_index[response_type] += 1

        # Create mock response object that matches LiteLLM structure
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)

        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]

        return MockResponse(response_content)


class MockState:
    """Mock state for demonstration."""

    def __init__(self, message_content: str):
        self.message_content = message_content
        self.history = self

    def get_events_as_list(self):
        """Return mock message."""

        class MockMessage:
            def __init__(self, content):
                self.content = content

        return [MockMessage(self.message_content)]


def demo_enhanced_reasoning():
    """Demonstrate the Enhanced Reasoning Agent capabilities."""

    print('🚀 Enhanced Reasoning Agent Demo')
    print('=' * 50)

    # Create mock LLM and agent
    mock_llm = MockLLM()
    extended_config = ExtendedConfig(
        {
            'max_reasoning_steps': 5,
            'reflection_threshold': 0.7,
            'tree_depth_limit': 3,
            'tree_branch_limit': 3,
        }
    )
    config = AgentConfig(extended=extended_config)

    agent = EnhancedReasoningAgent(llm=mock_llm, config=config)

    # Test cases
    test_cases = [
        {
            'name': 'Learning Path Question',
            'input': 'What is the best way to learn AI Agent development?',
            'description': 'Complex question requiring structured reasoning',
        },
        {
            'name': 'Simple Math Problem',
            'input': 'If I have 3 apples and I buy 2 more, then give away 1, how many do I have?',
            'description': 'Basic arithmetic with verification',
        },
        {
            'name': 'Algorithm Optimization',
            'input': 'How can I optimize a sorting algorithm for large datasets?',
            'description': 'Technical question requiring tree of thoughts',
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f'\n📝 Test Case {i}: {test_case["name"]}')
        print(f'Description: {test_case["description"]}')
        print(f'Input: {test_case["input"]}')
        print('-' * 50)

        # Create mock state
        state = MockState(test_case['input'])

        # Execute reasoning
        try:
            action = agent.step(state)
            print('🤖 Agent Response:')
            print(action.content)

        except Exception as e:
            import traceback

            print(f'❌ Error: {e}')
            print(f'📍 Traceback: {traceback.format_exc()}')

        print('-' * 50)

    # Show reasoning summary
    print('\n📊 Reasoning Summary:')
    summary = agent.get_reasoning_summary()
    for key, value in summary.items():
        print(f'  {key}: {value}')

    print(f'\n🔧 Total LLM calls made: {mock_llm.call_count}')
    print('\n✅ Demo completed successfully!')


def interactive_demo():
    """Interactive demo where users can ask questions."""

    print('\n🎯 Interactive Enhanced Reasoning Agent')
    print('=' * 50)
    print("Ask me any question and I'll demonstrate advanced reasoning!")
    print("Type 'quit' to exit, 'summary' to see reasoning statistics.")
    print('-' * 50)

    # Create mock LLM and agent
    mock_llm = MockLLM()
    extended_config = ExtendedConfig(
        {
            'max_reasoning_steps': 8,
            'reflection_threshold': 0.6,
            'tree_depth_limit': 4,
            'tree_branch_limit': 3,
        }
    )
    config = AgentConfig(extended=extended_config)

    agent = EnhancedReasoningAgent(llm=mock_llm, config=config)

    while True:
        try:
            user_input = input('\n💭 Your question: ').strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'summary':
                summary = agent.get_reasoning_summary()
                print('\n📊 Reasoning Summary:')
                for key, value in summary.items():
                    print(f'  {key}: {value}')
                continue
            elif not user_input:
                continue

            print('\n🤖 Thinking...')

            # Create state and get response
            state = MockState(user_input)
            action = agent.step(state)

            print('\n' + '=' * 50)
            print(action.content)
            print('=' * 50)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f'❌ Error: {e}')

    print('\n👋 Thanks for trying the Enhanced Reasoning Agent!')


if __name__ == '__main__':
    print('Enhanced Reasoning Agent Demo')
    print('Choose demo mode:')
    print('1. Automated demo with test cases')
    print('2. Interactive demo')

    try:
        choice = input('Enter choice (1 or 2): ').strip()

        if choice == '1':
            demo_enhanced_reasoning()
        elif choice == '2':
            interactive_demo()
        else:
            print('Invalid choice. Running automated demo...')
            demo_enhanced_reasoning()

    except KeyboardInterrupt:
        print('\n👋 Demo interrupted. Goodbye!')
    except Exception as e:
        print(f'❌ Demo error: {e}')
