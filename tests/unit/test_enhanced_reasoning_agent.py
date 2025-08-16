"""Tests for the Enhanced Reasoning Agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from openhands.agenthub.enhanced_reasoning_agent import EnhancedReasoningAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.events.action import MessageAction
from openhands.llm.llm import LLM


class MockLLMResponse:
    """Mock LLM response for testing."""

    def __init__(self, content: str):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content


class TestEnhancedReasoningAgent:
    """Test suite for Enhanced Reasoning Agent."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = MagicMock(spec=LLM)
        return llm

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration for testing."""
        return AgentConfig(
            max_reasoning_steps=5,
            reflection_threshold=0.7,
            tree_depth_limit=3,
            tree_branch_limit=2,
        )

    @pytest.fixture
    def enhanced_agent(self, mock_llm, agent_config):
        """Create an Enhanced Reasoning Agent for testing."""
        return EnhancedReasoningAgent(llm=mock_llm, config=agent_config)

    @pytest.fixture
    def mock_state(self):
        """Create a mock state with message history."""
        state = MagicMock(spec=State)

        # Mock message with content
        mock_message = MagicMock()
        mock_message.content = 'What is 2 + 2?'

        state.history.get_events_as_list.return_value = [mock_message]
        return state

    @pytest.mark.asyncio
    async def test_chain_of_thought_reasoning(self, enhanced_agent, mock_state):
        """Test Chain-of-Thought reasoning functionality."""
        # Mock LLM responses
        strategy_response = MockLLMResponse('chain_of_thought')
        reasoning_response = MockLLMResponse("""
        1. First, I need to understand the problem: What is 2 + 2?
        2. This is a basic arithmetic addition problem
        3. Adding 2 + 2 = 4
        4. The answer is 4
        """)
        verification_response = MockLLMResponse(
            'VERIFIED - This is correct basic arithmetic'
        )

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[strategy_response, reasoning_response, verification_response]
        )

        # Execute the step
        action = await enhanced_agent.step(mock_state)

        # Verify the action is a MessageAction
        assert isinstance(action, MessageAction)
        assert 'Chain Of Thought' in action.content
        assert '4' in action.content
        assert '✅' in action.content  # Verification passed

        # Verify reasoning history was recorded
        assert len(enhanced_agent.reasoning_history) > 0
        assert (
            enhanced_agent.reasoning_history[0].reasoning_type.value
            == 'chain_of_thought'
        )

    @pytest.mark.asyncio
    async def test_tree_of_thoughts_reasoning(self, enhanced_agent, mock_state):
        """Test Tree of Thoughts reasoning functionality."""
        # Mock complex problem
        mock_state.history.get_events_as_list.return_value = [
            MagicMock(content='How can I optimize a sorting algorithm?')
        ]

        # Mock LLM responses
        strategy_response = MockLLMResponse('tree_of_thoughts')
        initial_thoughts_response = MockLLMResponse("""
        [
            {
                "approach": "Improve comparison efficiency",
                "first_step": "Analyze comparison operations",
                "rationale": "Reducing comparisons improves performance"
            },
            {
                "approach": "Use better data structures",
                "first_step": "Consider heap or tree structures",
                "rationale": "Better data structures can reduce complexity"
            }
        ]
        """)
        scoring_response = MockLLMResponse('0.8')
        terminal_response = MockLLMResponse('no')
        child_response = MockLLMResponse(
            '["Implement quicksort optimization", "Use merge sort hybrid"]'
        )
        verification_response = MockLLMResponse('VERIFIED - Good algorithmic approach')

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[
                strategy_response,
                initial_thoughts_response,
                scoring_response,
                terminal_response,
                child_response,
                scoring_response,
                terminal_response,
                verification_response,
            ]
        )

        # Execute the step
        action = await enhanced_agent.step(mock_state)

        # Verify the action
        assert isinstance(action, MessageAction)
        assert 'Tree Of Thoughts' in action.content
        assert len(enhanced_agent.thought_trees) > 0

    @pytest.mark.asyncio
    async def test_reflection_mechanism(self, enhanced_agent, mock_state):
        """Test reflection mechanism for low-confidence solutions."""
        # Mock LLM responses for low confidence scenario
        strategy_response = MockLLMResponse('chain_of_thought')
        reasoning_response = MockLLMResponse(
            "I think the answer might be 5, but I'm not sure."
        )
        reflection_response = MockLLMResponse("""
        {
            "reflection_points": ["The calculation seems incorrect", "Should double-check arithmetic"],
            "improved_solution": "2 + 2 = 4 (corrected from previous error)",
            "confidence": 0.9
        }
        """)
        verification_response = MockLLMResponse('VERIFIED')

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[
                strategy_response,
                reasoning_response,
                reflection_response,
                verification_response,
            ]
        )

        # Set low confidence threshold to trigger reflection
        enhanced_agent.reflection_threshold = 0.8

        # Execute the step
        action = await enhanced_agent.step(mock_state)

        # Verify reflection was applied
        assert len(enhanced_agent.reflection_history) > 0
        assert 'Reflection Points' in action.content
        assert 'corrected' in action.content.lower()

    @pytest.mark.asyncio
    async def test_verification_logic(self, enhanced_agent, mock_state):
        """Test solution verification logic."""
        # Mock responses
        strategy_response = MockLLMResponse('basic')
        basic_response = MockLLMResponse('The answer is 4')
        verification_response = MockLLMResponse('VERIFIED - Correct arithmetic')

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[strategy_response, basic_response, verification_response]
        )

        # Execute the step
        action = await enhanced_agent.step(mock_state)

        # Verify verification was performed
        assert '✅' in action.content
        assert 'Verification: Passed' in action.content
        assert len(enhanced_agent.verification_results) > 0

    @pytest.mark.asyncio
    async def test_verification_failure(self, enhanced_agent, mock_state):
        """Test handling of verification failure."""
        # Mock responses
        strategy_response = MockLLMResponse('basic')
        basic_response = MockLLMResponse('The answer is 5')  # Wrong answer
        verification_response = MockLLMResponse(
            'FAILED - Incorrect arithmetic: 2 + 2 = 4, not 5'
        )

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[strategy_response, basic_response, verification_response]
        )

        # Execute the step
        action = await enhanced_agent.step(mock_state)

        # Verify verification failure was handled
        assert '⚠️' in action.content
        assert 'Verification: Needs review' in action.content

    def test_reasoning_step_parsing(self, enhanced_agent):
        """Test parsing of reasoning steps from text."""
        reasoning_text = """
        1. First, understand the problem
        2. Identify key information
        3. Apply the solution method
        4. Verify the result
        """

        steps = enhanced_agent._parse_reasoning_steps(reasoning_text)

        assert len(steps) == 4
        assert 'understand the problem' in steps[0]
        assert 'Verify the result' in steps[3]

    def test_reasoning_summary(self, enhanced_agent):
        """Test reasoning summary generation."""
        # Add some mock data
        from openhands.agenthub.enhanced_reasoning_agent.agent import (
            ReasoningStep,
            ReasoningType,
        )

        enhanced_agent.reasoning_history = [
            ReasoningStep(0, ReasoningType.CHAIN_OF_THOUGHT, 'Step 1', 0.8, [], 0),
            ReasoningStep(1, ReasoningType.CHAIN_OF_THOUGHT, 'Step 2', 0.9, [], 0),
        ]
        enhanced_agent.verification_results = {'test1': True, 'test2': False}

        summary = enhanced_agent.get_reasoning_summary()

        assert summary['total_reasoning_steps'] == 2
        assert summary['verification_success_rate'] == 0.5
        assert summary['average_confidence'] == 0.85

    @pytest.mark.asyncio
    async def test_empty_message_handling(self, enhanced_agent):
        """Test handling of empty message history."""
        # Mock empty state
        empty_state = MagicMock(spec=State)
        empty_state.history.get_events_as_list.return_value = []

        action = await enhanced_agent.step(empty_state)

        assert isinstance(action, MessageAction)
        assert 'need a task' in action.content.lower()

    @pytest.mark.asyncio
    async def test_json_parsing_fallback(self, enhanced_agent, mock_state):
        """Test fallback behavior when JSON parsing fails."""
        # Mock responses with invalid JSON
        strategy_response = MockLLMResponse('tree_of_thoughts')
        invalid_json_response = MockLLMResponse('This is not valid JSON')
        scoring_response = MockLLMResponse('0.5')
        terminal_response = MockLLMResponse('yes')
        verification_response = MockLLMResponse('VERIFIED')

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[
                strategy_response,
                invalid_json_response,
                scoring_response,
                terminal_response,
                verification_response,
            ]
        )

        # Should not raise an exception
        action = await enhanced_agent.step(mock_state)
        assert isinstance(action, MessageAction)

    @pytest.mark.asyncio
    async def test_confidence_display(self, enhanced_agent, mock_state):
        """Test confidence level display in response."""
        # Mock high confidence response
        strategy_response = MockLLMResponse('basic')
        basic_response = MockLLMResponse('The answer is 4')
        verification_response = MockLLMResponse('VERIFIED')

        enhanced_agent.llm.acompletion = AsyncMock(
            side_effect=[strategy_response, basic_response, verification_response]
        )

        action = await enhanced_agent.step(mock_state)

        # Check confidence display
        assert 'Confidence:' in action.content
        assert '%' in action.content
        assert '█' in action.content or '░' in action.content  # Progress bar characters


if __name__ == '__main__':
    pytest.main([__file__])
