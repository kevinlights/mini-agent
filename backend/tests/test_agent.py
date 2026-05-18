# Agent Tests
# Agent 测试

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.agent import Agent, AgentConfig, Message
from app.core.model import BaseModel as LLMModel


class TestMessage:
    """Tests for the Message dataclass.
    Message 数据类的测试。
    """

    def test_message_creation(self):
        """Test creating a message with required fields.
        测试使用必填字段创建消息。
        """
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp > 0
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test creating a message with metadata.
        测试使用元数据创建消息。
        """
        msg = Message(role="assistant", content="Hi", metadata={"token_count": 10})
        assert msg.metadata == {"token_count": 10}


class TestAgentConfig:
    """Tests for the AgentConfig dataclass.
    AgentConfig 数据类的测试。
    """

    def test_default_config(self):
        """Test default configuration values.
        测试默认配置值。
        """
        config = AgentConfig()
        assert config.name == "Assistant"
        assert config.system_prompt == "You are a helpful assistant."
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.max_history == 20

    def test_custom_config(self):
        """Test custom configuration values.
        测试自定义配置值。
        """
        config = AgentConfig(
            name="TestBot",
            system_prompt="You are a test bot.",
            temperature=0.9,
            max_tokens=100,
            max_history=10,
        )
        assert config.name == "TestBot"
        assert config.system_prompt == "You are a test bot."
        assert config.temperature == 0.9
        assert config.max_tokens == 100
        assert config.max_history == 10


class TestAgent:
    """Tests for the Agent class.
    Agent 类的测试。
    """

    def setup_method(self):
        """Set up test fixtures.
        设置测试夹具。
        """
        self.mock_model = MagicMock(spec=LLMModel)
        self.mock_model.name = "test-model"
        self.mock_model.generate = AsyncMock(return_value="Test response")
        self.agent = Agent(model=self.mock_model)

    def test_initialization(self):
        """Test agent initialization.
        测试 Agent 初始化。
        """
        assert self.agent.agent_id is not None
        assert self.agent.model == self.mock_model
        assert isinstance(self.agent.config, AgentConfig)
        assert self.agent.history == []
        assert self.agent.is_active is True

    def test_initialization_with_custom_config(self):
        """Test agent initialization with custom config.
        测试使用自定义配置初始化 Agent。
        """
        config = AgentConfig(name="CustomBot", temperature=0.5)
        agent = Agent(model=self.mock_model, config=config)
        assert agent.config.name == "CustomBot"
        assert agent.config.temperature == 0.5

    def test_initialization_with_agent_id(self):
        """Test agent initialization with custom agent_id.
        测试使用自定义 agent_id 初始化 Agent。
        """
        agent = Agent(model=self.mock_model, agent_id="test-id-123")
        assert agent.agent_id == "test-id-123"

    def test_add_message(self):
        """Test adding a message to history.
        测试向历史添加消息。
        """
        msg = self.agent.add_message("user", "Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert len(self.agent.history) == 1

    def test_add_message_with_metadata(self):
        """Test adding a message with metadata.
        测试向历史添加带元数据的消息。
        """
        msg = self.agent.add_message("user", "Hello", metadata={"source": "test"})
        assert msg.metadata == {"source": "test"}

    def test_history_trimming(self):
        """Test that history is trimmed when exceeding max_history.
        测试当超过 max_history 时历史会被修剪。
        """
        config = AgentConfig(max_history=3)
        agent = Agent(model=self.mock_model, config=config)

        # Add 5 messages
        for i in range(5):
            agent.add_message("user", f"Message {i}")

        # Should only keep the last 3 messages
        assert len(agent.history) == 3
        assert agent.history[0].content == "Message 2"
        assert agent.history[2].content == "Message 4"

    def test_get_context_messages(self):
        """Test getting context messages for LLM.
        测试获取 LLM 的上下文消息。
        """
        self.agent.add_message("user", "Hello")
        self.agent.add_message("assistant", "Hi there")

        context = self.agent.get_context_messages()

        # Should include system prompt and conversation history
        assert len(context) == 3  # system + user + assistant
        assert context[0]["role"] == "system"
        assert context[1]["role"] == "user"
        assert context[1]["content"] == "Hello"
        assert context[2]["role"] == "assistant"
        assert context[2]["content"] == "Hi there"

    def test_get_context_messages_excludes_system_from_history(self):
        """Test that system messages from history are excluded.
        测试历史中的系统消息被排除。
        """
        self.agent.add_message("system", "Custom system")
        self.agent.add_message("user", "Hello")

        context = self.agent.get_context_messages()

        # Should have system prompt from config, but not from history
        system_messages = [m for m in context if m["role"] == "system"]
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == self.agent.config.system_prompt

    @pytest.mark.asyncio
    async def test_respond(self):
        """Test generating a response.
        测试生成响应。
        """
        response = await self.agent.respond("Hello")

        assert response == "Test response"
        assert len(self.agent.history) == 2  # user message + assistant response
        assert self.agent.history[0].role == "user"
        assert self.agent.history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_respond_calls_model_generate(self):
        """Test that respond calls model.generate with correct parameters.
        测试 respond 使用正确参数调用 model.generate。
        """
        await self.agent.respond("Hello")

        self.mock_model.generate.assert_called_once()
        call_kwargs = self.mock_model.generate.call_args[1]
        assert call_kwargs["prompt"] == "Hello"
        assert call_kwargs["system_prompt"] == self.agent.config.system_prompt
        assert call_kwargs["temperature"] == self.agent.config.temperature

    @pytest.mark.asyncio
    async def test_respond_when_inactive(self):
        """Test respond when agent is inactive.
        测试 Agent 不活跃时的 respond。
        """
        self.agent.deactivate()
        response = await self.agent.respond("Hello")

        assert response == "Agent is not active."
        assert len(self.agent.history) == 0  # No messages added

    @pytest.mark.asyncio
    async def test_respond_with_custom_temperature(self):
        """Test respond with custom temperature setting.
        测试使用自定义温度设置的 respond。
        """
        config = AgentConfig(temperature=0.9)
        agent = Agent(model=self.mock_model, config=config)

        await agent.respond("Hello")

        call_kwargs = self.mock_model.generate.call_args[1]
        assert call_kwargs["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_respond_with_max_tokens(self):
        """Test respond with max_tokens setting.
        测试使用 max_tokens 设置的 respond。
        """
        config = AgentConfig(max_tokens=100)
        agent = Agent(model=self.mock_model, config=config)

        await agent.respond("Hello")

        call_kwargs = self.mock_model.generate.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_respond_maintains_conversation(self):
        """Test that respond maintains conversation history.
        测试 respond 维护对话历史。
        """
        response1 = await self.agent.respond("Hello")
        response2 = await self.agent.respond("How are you?")

        assert len(self.agent.history) == 4  # 2 user + 2 assistant messages
        assert self.agent.history[0].content == "Hello"
        assert self.agent.history[2].content == "How are you?"

    def test_clear_history(self):
        """Test clearing conversation history.
        测试清空对话历史。
        """
        self.agent.add_message("user", "Hello")
        self.agent.add_message("assistant", "Hi")
        assert len(self.agent.history) == 2

        self.agent.clear_history()
        assert len(self.agent.history) == 0

    def test_get_status(self):
        """Test getting agent status.
        测试获取 Agent 状态。
        """
        self.agent.add_message("user", "Hello")
        status = self.agent.get_status()

        assert status["agent_id"] == self.agent.agent_id
        assert status["name"] == self.agent.config.name
        assert status["is_active"] is True
        assert status["model"] == self.mock_model.name
        assert status["message_count"] == 1
        assert status["temperature"] == self.agent.config.temperature

    def test_activate(self):
        """Test activating the agent.
        测试激活 Agent。
        """
        self.agent.deactivate()
        assert self.agent.is_active is False

        self.agent.activate()
        assert self.agent.is_active is True

    def test_deactivate(self):
        """Test deactivating the agent.
        测试停用 Agent。
        """
        assert self.agent.is_active is True

        self.agent.deactivate()
        assert self.agent.is_active is False

    def test_build_prompt(self):
        """Test building prompt from context messages.
        测试从上下文消息构建提示。
        """
        context = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        prompt = self.agent._build_prompt(context)
        assert prompt == "Hello"

    def test_build_prompt_empty_context(self):
        """Test building prompt with empty context.
        测试使用空上下文构建提示。
        """
        prompt = self.agent._build_prompt([])
        assert prompt == ""

    def test_build_prompt_no_user_message(self):
        """Test building prompt when no user message exists.
        测试当没有用户消息时构建提示。
        """
        context = [
            {"role": "system", "content": "You are helpful"},
            {"role": "assistant", "content": "Hi"},
        ]
        prompt = self.agent._build_prompt(context)
        assert prompt == ""
