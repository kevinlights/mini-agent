# Context Window Management System
# 上下文窗口管理系统

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ContextConfig:
    """Configuration for context management.
    上下文管理的配置。
    """

    max_tokens: int = 4096  # Maximum context length in tokens
    compression_threshold: float = 0.8  # Compress when 80% full
    keep_recent_count: int = 5  # Always keep last N messages
    summarize_tool_results: bool = True  # Summarize tool results
    preserve_important: bool = True  # Preserve important information


class ContextManager:
    """Manages context window with compression and summarization.
    管理上下文窗口，支持压缩和摘要。
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize context manager.
        初始化上下文管理器。

        Args:
            config: Context configuration.
                上下文配置。
        """
        self.config = config or ContextConfig()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        估算文本的 token 数量。

        Args:
            text: Input text.
                输入文本。

        Returns:
            Estimated token count.
                估算的 token 数量。
        """
        # Simple estimation: ~4 chars per token for English
        # 简单估算：英文约 4 字符/token
        return len(text) // 4

    def compress_context(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Compress context to fit within token limits.
        压缩上下文以适应 token 限制。

        Args:
            messages: List of message dictionaries.
                消息字典列表。

        Returns:
            Compressed message list.
                压缩后的消息列表。
        """
        # Calculate total tokens
        total_tokens = sum(
            self.estimate_tokens(msg.get("content", ""))
            for msg in messages
        )

        # If under threshold, return as-is
        if total_tokens <= self.config.max_tokens * self.config.compression_threshold:
            return messages

        # Keep recent messages
        recent_messages = messages[-self.config.keep_recent_count:]

        # Compress older messages
        older_messages = messages[:-self.config.keep_recent_count]
        compressed = self._compress_messages(older_messages)

        # Combine compressed + recent
        return compressed + recent_messages

    def _compress_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Compress a list of messages.
        压缩消息列表。

        Args:
            messages: Messages to compress.
                要压缩的消息。

        Returns:
            Compressed messages.
                压缩后的消息。
        """
        if not messages:
            return []

        # Group by conversation turns
        turns = self._group_into_turns(messages)

        # Summarize each turn
        summarized_turns = []
        for turn in turns:
            summarized = self._summarize_turn(turn)
            if summarized:
                summarized_turns.append(summarized)

        return summarized_turns

    def _group_into_turns(
        self, messages: List[Dict[str, str]]
    ) -> List[List[Dict[str, str]]]:
        """Group messages into conversation turns.
        将消息分组为对话轮次。

        Args:
            messages: List of messages.
                消息列表。

        Returns:
            List of turns, where each turn is a list of messages.
            轮次列表，每个轮次是消息列表。
        """
        turns = []
        current_turn = []

        for msg in messages:
            role = msg.get("role", "")
            if role == "user" and current_turn:
                turns.append(current_turn)
                current_turn = []
            current_turn.append(msg)

        if current_turn:
            turns.append(current_turn)

        return turns

    def _summarize_turn(self, turn: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Summarize a conversation turn.
        总结对话轮次。

        Args:
            turn: List of messages in the turn.
                轮次中的消息列表。

        Returns:
            Summarized message or None.
            总结后的消息或 None。
        """
        if not turn:
            return None

        # Extract user input and assistant response
        user_content = ""
        assistant_content = ""
        tool_results = []

        for msg in turn:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                user_content = content
            elif role == "assistant":
                assistant_content = content
            elif role == "tool":
                tool_results.append(content)

        # If has tool results, summarize them
        if tool_results and self.config.summarize_tool_results:
            tool_summary = self._summarize_tool_results(tool_results)
            assistant_content = f"{assistant_content}\n[Tool Results: {tool_summary}]"

        # If we have content, return summarized turn
        if user_content or assistant_content:
            summary = self._create_summary(user_content, assistant_content)
            return {"role": "assistant", "content": summary}

        return None

    def _summarize_tool_results(self, results: List[str]) -> str:
        """Summarize tool execution results.
        总结工具执行结果。

        Args:
            results: List of tool result strings.
                工具结果字符串列表。

        Returns:
            Summarized tool results.
                总结后的工具结果。
        """
        if not results:
            return "No tool results."

        # Count successful vs failed
        success_count = 0
        error_count = 0
        key_info = []

        for result in results:
            if result.startswith("Error"):
                error_count += 1
            else:
                success_count += 1
                # Extract key information (first 100 chars)
                key_info.append(result[:100])

        summary = f"{success_count} succeeded, {error_count} failed"
        if key_info:
            summary += f". Key info: {'; '.join(key_info[:3])}"

        return summary

    def _create_summary(
        self, user_content: str, assistant_content: str
    ) -> str:
        """Create a summary of a conversation turn.
        创建对话轮次的摘要。

        Args:
            user_content: User's message content.
                用户的消息内容。
            assistant_content: Assistant's response content.
                助手的响应内容。

        Returns:
            Summarized content.
                摘要内容。
        """
        # Truncate long content
        user_truncated = self._truncate_text(user_content, 200)
        assistant_truncated = self._truncate_text(assistant_content, 300)

        if user_truncated and assistant_truncated:
            return f"[Summary] User: {user_truncated} | Assistant: {assistant_truncated}"
        elif user_truncated:
            return f"[Summary] User: {user_truncated}"
        elif assistant_truncated:
            return f"[Summary] Assistant: {assistant_truncated}"

        return "[Summary] Empty turn"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length.
        将文本截断到最大长度。

        Args:
            text: Input text.
                输入文本。
            max_length: Maximum length.
                最大长度。

        Returns:
            Truncated text.
                截断后的文本。
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def extract_important_info(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Extract and preserve important information from messages.
        从消息中提取并保留重要信息。

        Args:
            messages: List of messages.
                消息列表。

        Returns:
            Messages marked as important.
            标记为重要的消息。
        """
        if not self.config.preserve_important:
            return []

        important_messages = []
        important_patterns = [
            r'IMPORTANT:',
            r'CRITICAL:',
            r'KEY:',
            r'NOTE:',
            r'WARNING:',
            r'ERROR:',
            r'must',
            r'should',
            r'always',
            r'never',
        ]

        for msg in messages:
            content = msg.get("content", "")
            # Check if message contains important patterns
            if any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in important_patterns
            ):
                important_messages.append(msg)

        return important_messages

    def build_optimized_context(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Build optimized context with all management strategies.
        构建优化的上下文，包含所有管理策略。

        Args:
            messages: Original message list.
                原始消息列表。

        Returns:
            Optimized message list.
                优化后的消息列表。
        """
        # Step 1: Extract important information
        important_messages = self.extract_important_info(messages)

        # Step 2: Compress context
        compressed = self.compress_context(messages)

        # Step 3: Ensure important messages are preserved
        # Add important messages at the beginning if not already included
        important_ids = {id(msg) for msg in compressed}
        for imp_msg in important_messages:
            if id(imp_msg) not in important_ids:
                compressed.insert(0, imp_msg)

        return compressed

    def get_context_stats(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get statistics about the context.
        获取上下文的统计信息。

        Args:
            messages: Message list.
                消息列表。

        Returns:
            Dictionary with context statistics.
            包含上下文统计信息的字典。
        """
        total_tokens = sum(
            self.estimate_tokens(msg.get("content", ""))
            for msg in messages
        )

        role_counts = {}
        for msg in messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_messages": len(messages),
            "total_tokens": total_tokens,
            "max_tokens": self.config.max_tokens,
            "usage_percent": (total_tokens / self.config.max_tokens) * 100,
            "role_counts": role_counts,
            "needs_compression": total_tokens > self.config.max_tokens * self.config.compression_threshold,
        }
