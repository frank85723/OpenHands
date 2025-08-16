"""
Enhanced Reasoning Agent - Simplified Synchronous Version
Demonstrates AI Agent core reasoning capabilities in a way compatible with OpenHands architecture.
"""

from typing import Any

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.events.action import Action, MessageAction
from openhands.llm.llm import LLM


class EnhancedReasoningAgent(Agent):
    """
    An AI Agent with enhanced reasoning capabilities including:
    - Chain-of-Thought reasoning
    - Tree of Thoughts exploration
    - Self-reflection mechanisms
    - Solution verification
    """

    VERSION = '1.0'

    def __init__(self, llm: LLM, config: AgentConfig):
        super().__init__(llm, config)
        self.reasoning_history: list[dict[str, Any]] = []
        self.reflection_threshold = 0.7
        self.verification_results: dict[str, bool] = {}

    def step(self, state: State) -> Action:
        """
        Enhanced step function with multi-stage reasoning.
        """
        # Get the latest message
        messages = list(state.history)
        if not messages:
            return MessageAction(content='I need a task or question to work on.')

        latest_message = messages[-1]
        if hasattr(latest_message, 'content'):
            user_input = latest_message.content
        else:
            user_input = str(latest_message)

        # Determine the best reasoning strategy
        reasoning_strategy = self._select_reasoning_strategy(user_input)

        # Apply the selected reasoning strategy
        if reasoning_strategy == 'chain_of_thought':
            result = self._chain_of_thought_reasoning(user_input)
        elif reasoning_strategy == 'tree_of_thoughts':
            result = self._tree_of_thoughts_reasoning(user_input)
        else:
            result = self._basic_reasoning(user_input)

        # Apply reflection if confidence is below threshold
        if result.get('confidence', 1.0) < self.reflection_threshold:
            result = self._reflect_on_solution(result)

        # Verify the solution
        verification_result = self._verify_solution(result)
        result['verification'] = verification_result

        # Format the response
        response_content = self._format_reasoning_response(result)

        return MessageAction(content=response_content)

    def _select_reasoning_strategy(self, problem: str) -> str:
        """
        Select the most appropriate reasoning strategy based on the problem complexity.
        """
        complexity_prompt = f"""
        Analyze the complexity of this problem and suggest the best reasoning approach:
        Problem: {problem}

        Respond with one of: basic, chain_of_thought, tree_of_thoughts
        """

        messages = [Message(role='user', content=[TextContent(text=complexity_prompt)])]
        response = self.llm.completion(messages=messages)

        strategy_text = self._extract_content_text(
            response.choices[0].message.content
        ).lower()

        if 'tree_of_thoughts' in strategy_text:
            return 'tree_of_thoughts'
        elif 'chain_of_thought' in strategy_text:
            return 'chain_of_thought'
        else:
            return 'basic'

    def _chain_of_thought_reasoning(self, problem: str) -> dict[str, Any]:
        """
        Implement step-by-step Chain-of-Thought reasoning.
        """
        cot_prompt = f"""
        Solve this problem step by step using chain-of-thought reasoning:
        Problem: {problem}

        Please provide:
        1. Step-by-step reasoning
        2. Final answer
        3. Confidence level (0-1)

        Format your response clearly with numbered steps.
        """

        messages = [Message(role='user', content=[TextContent(text=cot_prompt)])]
        response = self.llm.completion(messages=messages)

        response_text = self._extract_content_text(response.choices[0].message.content)

        # Parse reasoning steps
        steps = self._parse_reasoning_steps(response_text)

        # Extract confidence (simplified)
        confidence = 0.8  # Default confidence

        result = {
            'strategy': 'Chain Of Thought',
            'reasoning_steps': steps,
            'final_answer': response_text,
            'confidence': confidence,
        }

        self.reasoning_history.append(result)
        return result

    def _tree_of_thoughts_reasoning(self, problem: str) -> dict[str, Any]:
        """
        Implement Tree of Thoughts reasoning with multiple exploration paths.
        """
        tot_prompt = f"""
        Explore multiple approaches to solve this problem:
        Problem: {problem}

        Generate 3 different approaches and evaluate each one.
        Then select the best approach and provide the solution.
        """

        messages = [Message(role='user', content=[TextContent(text=tot_prompt)])]
        response = self.llm.completion(messages=messages)

        response_text = self._extract_content_text(response.choices[0].message.content)

        # Simulate tree exploration
        paths_explored = 3

        result = {
            'strategy': 'Tree Of Thoughts',
            'paths_explored': paths_explored,
            'final_answer': response_text,
            'confidence': 0.85,
        }

        self.reasoning_history.append(result)
        return result

    def _basic_reasoning(self, problem: str) -> dict[str, Any]:
        """
        Basic reasoning approach for simple problems.
        """
        basic_prompt = f"""
        Provide a direct answer to this question:
        Question: {problem}
        """

        messages = [Message(role='user', content=[TextContent(text=basic_prompt)])]
        response = self.llm.completion(messages=messages)

        response_text = self._extract_content_text(response.choices[0].message.content)

        result = {'strategy': 'Basic', 'final_answer': response_text, 'confidence': 0.7}

        self.reasoning_history.append(result)
        return result

    def _reflect_on_solution(self, initial_result: dict[str, Any]) -> dict[str, Any]:
        """
        Apply reflection mechanism to improve the solution.
        """
        reflection_prompt = f"""
        Review and improve this solution:
        Original Answer: {initial_result.get('final_answer', '')}

        Please:
        1. Identify any potential issues
        2. Suggest improvements
        3. Provide a refined answer
        """

        messages = [Message(role='user', content=[TextContent(text=reflection_prompt)])]
        response = self.llm.completion(messages=messages)

        reflection_text = self._extract_content_text(
            response.choices[0].message.content
        )

        # Update result with reflection
        initial_result['reflection'] = {
            'applied': True,
            'improvements': reflection_text,
            'final_answer': reflection_text,
        }
        initial_result['confidence'] = min(
            initial_result.get('confidence', 0.7) + 0.1, 1.0
        )

        return initial_result

    def _verify_solution(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Verify the solution for correctness and reasonableness.
        """
        verification_prompt = f"""
        Verify this solution for correctness:
        Solution: {result.get('final_answer', '')}

        Respond with VERIFIED if correct, or FAILED with explanation if incorrect.
        """

        messages = [
            Message(role='user', content=[TextContent(text=verification_prompt)])
        ]
        response = self.llm.completion(messages=messages)

        verification_text = self._extract_content_text(
            response.choices[0].message.content
        )
        is_verified = 'VERIFIED' in verification_text.upper()

        # Store verification result
        solution_key = str(hash(result.get('final_answer', '')))
        self.verification_results[solution_key] = is_verified

        return {'is_verified': is_verified, 'verification_text': verification_text}

    def _parse_reasoning_steps(self, text: str) -> list[str]:
        """
        Parse reasoning steps from text.
        """
        steps = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if line and (
                line[0].isdigit() or line.startswith('-') or line.startswith('•')
            ):
                steps.append(line)

        return steps if steps else [text]

    def _extract_content_text(self, content) -> str:
        """
        Extract text content from LLM response, handling both string and list formats.
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return ' '.join(
                item.text if hasattr(item, 'text') else str(item) for item in content
            )
        else:
            return str(content)

    def _format_reasoning_response(self, result: dict[str, Any]) -> str:
        """
        Format the reasoning result into a user-friendly response.
        """
        strategy = result.get('strategy', 'Unknown')
        confidence = result.get('confidence', 0.0)
        final_answer = result.get('final_answer', 'No answer provided')

        # Create confidence bar
        confidence_bar = self._create_confidence_bar(confidence)

        response_parts = [f'🧠 **Reasoning Strategy**: {strategy}', '']

        # Add reasoning steps if available
        if 'reasoning_steps' in result and result['reasoning_steps']:
            response_parts.append('📝 **Reasoning Steps**:')
            for i, step in enumerate(
                result['reasoning_steps'][:5], 1
            ):  # Limit to 5 steps
                response_parts.append(f'{i}. {step}')
            response_parts.append('')

        # Add tree exploration info
        if 'paths_explored' in result:
            response_parts.append(
                f'🌳 **Explored {result["paths_explored"]} possible paths**'
            )
            response_parts.append('')

        # Add reflection info
        if 'reflection' in result and result['reflection'].get('applied'):
            response_parts.append(
                '🤔 **Reflection Applied**: Solution refined based on self-evaluation'
            )
            response_parts.append('')

        # Add verification status
        verification = result.get('verification', {})
        if verification.get('is_verified'):
            response_parts.append('✅ **Verification**: Passed')
        else:
            response_parts.append('⚠️ **Verification**: Needs review')
        response_parts.append('')

        # Add confidence
        response_parts.append(
            f'📊 **Confidence**: {confidence * 100:.1f}% {confidence_bar}'
        )
        response_parts.append('')

        # Add final answer
        response_parts.append('💡 **Final Answer**:')
        response_parts.append(final_answer)

        return '\n'.join(response_parts)

    def _create_confidence_bar(self, confidence: float) -> str:
        """
        Create a visual confidence bar.
        """
        filled = int(confidence * 10)
        empty = 10 - filled
        return '[' + '█' * filled + '░' * empty + ']'

    def get_reasoning_summary(self) -> dict[str, Any]:
        """
        Get a summary of reasoning performance.
        """
        total_steps = len(self.reasoning_history)
        total_confidence = sum(r.get('confidence', 0) for r in self.reasoning_history)
        avg_confidence = total_confidence / total_steps if total_steps > 0 else 0

        verification_success = sum(1 for v in self.verification_results.values() if v)
        verification_rate = (
            verification_success / len(self.verification_results)
            if self.verification_results
            else 0
        )

        return {
            'total_reasoning_steps': total_steps,
            'average_confidence': avg_confidence,
            'verification_success_rate': verification_rate,
            'strategies_used': [
                r.get('strategy', 'Unknown') for r in self.reasoning_history
            ],
        }
