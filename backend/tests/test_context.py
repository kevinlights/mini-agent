# Context Management Tests
# 上下文管理测试

import pytest
from app.core.context import ContextManager, ContextConfig


class TestContextConfig:
    """Tests for ContextConfig dataclass.
    ContextConfig 数据类的测试。
    """

    def test_default_config(self):
        """Test default configuration values.
        测试默认配置值。
        """
        config = ContextConfig()
        assert config.max_tokens == 4096
        assert config.compression_threshold == 0.8
        assert config.keep_recent_count == 5
        assert config.summarize_tool_results is True
        assert config.preserve_important is True

    def test_custom_config(self):
        """Test custom configuration values.
        测试自定义配置值。
        """
        config = ContextConfig(
            max_tokens=2048,
            compression_threshold=0.9,
            keep_recent_count=3,
            summarize_tool_results=False,
            preserve_important=False
        )
        assert config.max_tokens == 2048
        assert config.compression_threshold == 0.9
        assert config.keep_recent_count == 3


class TestContextManager:
    """Tests for ContextManager class.
    ContextManager 类的测试。
    """

    def setup_method(self):
        """Setup test environment.
        设置测试环境。
        """
        self.config = ContextConfig(max_tokens=1000)
        self.manager = ContextManager(config=self.config)

    def test_estimate_tokens(self):
        """Test token estimation.
        测试 token 估算。
        """
        assert self.manager.estimate_tokens("Hello world") == 2  # 11 chars // 4
        assert self.manager.estimate_tokens("") == 0
        assert self.manager.estimate_tokens("1234") == 1

    def test_compress_context_under_threshold(self):
        """Test no compression when under threshold.
        测试低于阈值时不压缩。
        """
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = self.manager.compress_context(messages)
        assert result == messages

    def test_compress_context_over_threshold(self):
        """Test compression when over threshold.
        测试超过阈值时压缩。
        """
        # Create messages that exceed threshold
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"Message {i}" * 50})
            messages.append({"role": "assistant", "content": f"Response {i}" * 50})

        result = self.manager.compress_context(messages)
        # Should keep recent messages and compress older ones
        assert len(result) > 0
        # Recent messages should be preserved
        assert any(f"Message 19" in msg.get("content", "") for msg in result[-5:])

    def test_compress_empty_context(self):
        """Test compressing empty context.
        测试压缩空上下文。
        """
        result = self.manager.compress_context([])
        assert result == []

    def test_group_into_turns(self):
        """Test grouping messages into turns.
        测试将消息分组为轮次。
        """
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Good"},
        ]
        turns = self.manager._group_into_turns(messages)
        assert len(turns) == 2
        assert len(turns[0]) == 2  # First turn: user + assistant
        assert len(turns[1]) == 2  # Second turn: user + assistant

    def test_summarize_turn(self):
        """Test summarizing a conversation turn.
        测试总结对话轮次。
        """
        turn = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
        ]
        result = self.manager._summarize_turn(turn)
        assert result is not None
        assert "[Summary]" in result["content"]
        assert "User:" in result["content"]
        assert "Assistant:" in result["content"]

    def test_summarize_turn_with_tool_results(self):
        """Test summarizing turn with tool results.
        测试总结带工具结果的轮次。
        """
        turn = [
            {"role": "user", "content": "Read file.txt"},
            {"role": "assistant", "content": "Called tool: file_tool"},
            {"role": "tool", "content": "File contents: hello world"},
        ]
        result = self.manager._summarize_turn(turn)
        assert result is not None
        assert "Tool Results:" in result["content"]

    def test_summarize_tool_results(self):
        """Test summarizing tool results.
        测试总结工具结果。
        """
        results = [
            "Contents of file.txt: hello world",
            "Error: file not found",
            "List: file1.txt, file2.txt",
        ]
        summary = self.manager._summarize_tool_results(results)
        assert "2 succeeded" in summary
        assert "1 failed" in summary

    def test_summarize_tool_results_empty(self):
        """Test summarizing empty tool results.
        测试总结空工具结果。
        """
        summary = self.manager._summarize_tool_results([])
        assert summary == "No tool results."

    def test_create_summary(self):
        """Test creating a summary.
        测试创建摘要。
        """
        summary = self.manager._create_summary(
            "What is Python?",
            "Python is a programming language."
        )
        assert "[Summary]" in summary
        assert "User:" in summary
        assert "Assistant:" in summary

    def test_truncate_text(self):
        """Test text truncation.
        测试文本截断。
        """
        short_text = "Hello"
        assert self.manager._truncate_text(short_text, 10) == "Hello"

        long_text = "A" * 200
        truncated = self.manager._truncate_text(long_text, 10)
        assert len(truncated) == 13  # 10 + "..."
        assert truncated.endswith("...")

    def test_extract_important_info(self):
        """Test extracting important information.
        测试提取重要信息。
        """
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "IMPORTANT: Always use tools correctly"},
            {"role": "user", "content": "Thanks"},
            {"role": "assistant", "content": "WARNING: This is critical"},
        ]
        important = self.manager.extract_important_info(messages)
        assert len(important) == 2
        assert "IMPORTANT" in important[0]["content"]
        assert "WARNING" in important[1]["content"]

    def test_extract_important_info_disabled(self):
        """Test with important info extraction disabled.
        测试禁用重要信息提取。
        """
        config = ContextConfig(preserve_important=False)
        manager = ContextManager(config=config)
        messages = [
            {"role": "assistant", "content": "IMPORTANT: Always use tools"},
        ]
        important = manager.extract_important_info(messages)
        assert important == []

    def test_build_optimized_context(self):
        """Test building optimized context.
        测试构建优化上下文。
        """
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "IMPORTANT: Remember this"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Good"},
        ]
        result = self.manager.build_optimized_context(messages)
        assert len(result) > 0
        # Important message should be preserved
        assert any("IMPORTANT" in msg.get("content", "") for msg in result)

    def test_get_context_stats(self):
        """Test getting context statistics.
        测试获取上下文统计信息。
        """
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        stats = self.manager.get_context_stats(messages)
        assert stats["total_messages"] == 3
        assert stats["total_tokens"] > 0
        assert stats["max_tokens"] == 1000
        assert stats["usage_percent"] > 0
        assert stats["role_counts"]["user"] == 2
        assert stats["role_counts"]["assistant"] == 1
        assert stats["needs_compression"] is False

    def test_get_context_stats_needs_compression(self):
        """Test stats when compression is needed.
        测试需要压缩时的统计信息。
        """
        # Create long messages
        messages = [
            {"role": "user", "content": "A" * 4000},
        ]
        stats = self.manager.get_context_stats(messages)
        assert stats["needs_compression"] is True


class TestContextIntegration:
    """Integration tests for context management.
    上下文管理的集成测试。
    """

    def setup_method(self):
        """Setup test environment.
        设置测试环境。
        """
        self.config = ContextConfig(max_tokens=500)
        self.manager = ContextManager(config=self.config)

    def test_full_compression_workflow(self):
        """Test full compression workflow.
        测试完整压缩工作流。
        """
        # Create conversation that exceeds threshold
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"Question {i}" * 30})
            messages.append({"role": "assistant", "content": f"Answer {i}" * 30})

        # Add important message
        messages.insert(0, {"role": "assistant", "content": "IMPORTANT: Always save your work"})

        # Build optimized context
        result = self.manager.build_optimized_context(messages)

        # Verify important message is preserved
        assert any("IMPORTANT" in msg.get("content", "") for msg in result)

        # Verify context is compressed
        stats = self.manager.get_context_stats(result)
        assert stats["total_messages"] < len(messages)

    def test_tool_result_summarization(self):
        """Test tool result summarization in context.
        测试上下文中的工具结果摘要。
        """
        messages = [
            {"role": "user", "content": "List files"},
            {"role": "assistant", "content": "Called tool: file_tool"},
            {"role": "tool", "content": "file1.txt\nfile2.txt\nfile3.txt"},
            {"role": "user", "content": "Read file1.txt"},
            {"role": "assistant", "content": "Called tool: file_tool"},
            {"role": "tool", "content": "Contents of file1.txt: hello world"},
        ]

        # Turn should summarize tool results
        turn = messages[:3]
        result = self.manager._summarize_turn(turn)
        assert result is not None
        assert "Tool Results:" in result["content"]
