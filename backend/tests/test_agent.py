# Agent Tests
# Agent 测试

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.agent import Agent, AgentConfig, Message
from app.core.model import BaseModel as LLMModel
from app.tools.tool import ToolRegistry, BaseTool, ToolParameter


class MockTool(BaseTool):
    """Mock tool for testing.
    用于测试的模拟工具。
    """

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing."

    @property
    def parameters(self) -> list:
        return [
            ToolParameter(name="input", type="string", description="Input text"),
        ]

    async def execute(self, input: str) -> str:
        return f"Mock result: {input}"


class TestMessage:
    """Tests for the Message dataclass.
    Message 数据类的测试。
    """

    def test_message_creation(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp > 0
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        msg = Message(role="assistant", content="Hi", metadata={"token_count": 10})
        assert msg.metadata == {"token_count": 10}


class TestAgentConfig:
    """Tests for the AgentConfig dataclass.
    AgentConfig 数据类的测试。
    """

    def test_default_config(self):
        config = AgentConfig()
        assert config.name == "Assistant"
        assert config.system_prompt == "You are a helpful assistant."
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.max_history == 20
        assert config.enable_tools is True
        assert config.max_tool_calls == 5

    def test_custom_config(self):
        config = AgentConfig(
            name="TestBot",
            system_prompt="You are a test bot.",
            temperature=0.9,
            max_tokens=100,
            max_history=10,
            enable_tools=False,
        )
        assert config.name == "TestBot"
        assert config.system_prompt == "You are a test bot."
        assert config.temperature == 0.9
        assert config.max_tokens == 100
        assert config.max_history == 10
        assert config.enable_tools is False


class TestAgent:
    """Tests for the Agent class.
    Agent 类的测试。
    """

    def setup_method(self):
        self.mock_model = MagicMock(spec=LLMModel)
        self.mock_model.name = "test-model"
        self.mock_model.generate = AsyncMock(return_value="Test response")
        self.agent = Agent(model=self.mock_model)

    def test_initialization(self):
        assert self.agent.agent_id is not None
        assert self.agent.model == self.mock_model
        assert isinstance(self.agent.config, AgentConfig)
        assert self.agent.history == []
        assert self.agent.is_active is True
        assert isinstance(self.agent.tool_registry, ToolRegistry)

    def test_initialization_with_custom_config(self):
        config = AgentConfig(name="CustomBot", temperature=0.5)
        agent = Agent(model=self.mock_model, config=config)
        assert agent.config.name == "CustomBot"
        assert agent.config.temperature == 0.5

    def test_initialization_with_tool_registry(self):
        registry = ToolRegistry()
        agent = Agent(model=self.mock_model, tool_registry=registry)
        assert agent.tool_registry == registry

    def test_add_message(self):
        msg = self.agent.add_message("user", "Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert len(self.agent.history) == 1

    def test_add_message_with_metadata(self):
        msg = self.agent.add_message("user", "Hello", metadata={"source": "test"})
        assert msg.metadata == {"source": "test"}

    def test_history_trimming(self):
        config = AgentConfig(max_history=3)
        agent = Agent(model=self.mock_model, config=config)

        for i in range(5):
            agent.add_message("user", f"Message {i}")

        assert len(agent.history) == 3
        assert agent.history[0].content == "Message 2"
        assert agent.history[2].content == "Message 4"

    def test_get_context_messages(self):
        self.agent.add_message("user", "Hello")
        self.agent.add_message("assistant", "Hi there")

        context = self.agent.get_context_messages()

        assert len(context) == 3
        assert context[0]["role"] == "system"
        assert context[1]["role"] == "user"
        assert context[1]["content"] == "Hello"
        assert context[2]["role"] == "assistant"
        assert context[2]["content"] == "Hi there"

    @pytest.mark.asyncio
    async def test_respond(self):
        response = await self.agent.respond("Hello")

        assert response == "Test response"
        assert len(self.agent.history) == 2
        assert self.agent.history[0].role == "user"
        assert self.agent.history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_respond_calls_model_generate(self):
        await self.agent.respond("Hello")

        self.mock_model.generate.assert_called_once()
        call_kwargs = self.mock_model.generate.call_args[1]
        assert call_kwargs["prompt"] == "Hello"
        assert call_kwargs["system_prompt"] == self.agent.config.system_prompt
        assert call_kwargs["temperature"] == self.agent.config.temperature

    @pytest.mark.asyncio
    async def test_respond_when_inactive(self):
        self.agent.deactivate()
        response = await self.agent.respond("Hello")

        assert response == "Agent is not active."
        assert len(self.agent.history) == 0

    @pytest.mark.asyncio
    async def test_respond_maintains_conversation(self):
        response1 = await self.agent.respond("Hello")
        response2 = await self.agent.respond("How are you?")

        assert len(self.agent.history) == 4
        assert self.agent.history[0].content == "Hello"
        assert self.agent.history[2].content == "How are you?"

    def test_clear_history(self):
        self.agent.add_message("user", "Hello")
        self.agent.add_message("assistant", "Hi")
        assert len(self.agent.history) == 2

        self.agent.clear_history()
        assert len(self.agent.history) == 0

    def test_get_status(self):
        self.agent.add_message("user", "Hello")
        status = self.agent.get_status()

        assert status["agent_id"] == self.agent.agent_id
        assert status["name"] == self.agent.config.name
        assert status["is_active"] is True
        assert status["model"] == self.mock_model.name
        assert status["message_count"] == 1
        assert status["temperature"] == self.agent.config.temperature
        assert status["tools_enabled"] is True
        assert status["registered_tools"] == 0

    def test_activate(self):
        self.agent.deactivate()
        assert self.agent.is_active is False

        self.agent.activate()
        assert self.agent.is_active is True

    def test_deactivate(self):
        assert self.agent.is_active is True

        self.agent.deactivate()
        assert self.agent.is_active is False


class TestAgentToolCalling:
    """Tests for agent tool calling functionality.
    Agent 工具调用功能的测试。
    """

    def setup_method(self):
        self.mock_model = MagicMock(spec=LLMModel)
        self.mock_model.name = "test-model"
        self.registry = ToolRegistry()
        self.registry.register(MockTool())
        self.agent = Agent(model=self.mock_model, tool_registry=self.registry)

    def test_parse_tool_call_valid(self):
        response = 'TOOL_CALL:{"name": "mock_tool", "arguments": {"input": "test"}}'
        result = self.agent._parse_tool_call(response)

        assert result is not None
        assert result["name"] == "mock_tool"
        assert result["arguments"]["input"] == "test"

    def test_parse_tool_call_invalid_json(self):
        response = "TOOL_CALL:invalid json"
        result = self.agent._parse_tool_call(response)

        assert result is None

    def test_parse_tool_call_no_prefix(self):
        response = '{"name": "mock_tool", "arguments": {"input": "test"}}'
        result = self.agent._parse_tool_call(response)

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_tool_call(self):
        tool_call = {"name": "mock_tool", "arguments": {"input": "test"}}
        self.mock_model.generate.return_value = "Final response"

        result = await self.agent._handle_tool_call(tool_call, [])

        assert result == "Final response"
        assert len(self.agent.history) == 3
        assert self.agent.history[0].role == "assistant"
        assert "Called tool: mock_tool" in self.agent.history[0].content
        assert self.agent.history[1].role == "tool"
        assert self.agent.history[1].content == "Mock result: test"
        assert self.agent.history[2].role == "assistant"
        assert self.agent.history[2].content == "Final response"

    @pytest.mark.asyncio
    async def test_handle_tool_call_error(self):
        tool_call = {"name": "mock_tool", "arguments": {"input": "test"}}

        # Make execute_tool raise an exception
        self.registry.execute_tool = AsyncMock(
            side_effect=Exception("Tool execution failed")
        )
        self.mock_model.generate.return_value = "Error response"

        result = await self.agent._handle_tool_call(tool_call, [])

        assert result == "Error response"
        assert "Error executing tool" in self.agent.history[1].content

    @pytest.mark.asyncio
    async def test_respond_with_tool_call(self):
        # First call returns tool call, second call returns final response
        self.mock_model.generate.side_effect = [
            'TOOL_CALL:{"name": "mock_tool", "arguments": {"input": "test"}}',
            "Final response after tool use",
        ]

        response = await self.agent.respond("Use the tool")

        assert response == "Final response after tool use"
        assert len(self.agent.history) == 4

    @pytest.mark.asyncio
    async def test_respond_without_tool_call(self):
        self.mock_model.generate.return_value = "Normal response"

        response = await self.agent.respond("Hello")

        assert response == "Normal response"
        assert len(self.agent.history) == 2

    def test_build_prompt_with_tools(self):
        context = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        prompt = self.agent._build_prompt(context)

        assert "Available tools: mock_tool" in prompt
        assert "TOOL_CALL:" in prompt
        assert "Hello" in prompt

    def test_build_prompt_without_tools(self):
        agent = Agent(model=self.mock_model)
        config = AgentConfig(enable_tools=False)
        agent = Agent(model=self.mock_model, config=config)

        context = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        prompt = agent._build_prompt(context)

        assert prompt == "Hello"

    def test_get_status_with_tools(self):
        status = self.agent.get_status()

        assert status["tools_enabled"] is True
        assert status["registered_tools"] == 1
