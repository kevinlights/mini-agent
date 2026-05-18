# Simple Agent Implementation
# 简单 Agent 实现

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
import uuid

from app.core.model import BaseModel as LLMModel


@dataclass
class Message:
    """Represents a single message in the conversation.
    表示对话中的单条消息。
    """

    role: str  # "system", "user", "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for the agent.
    Agent 的配置。
    """

    name: str = "Assistant"
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    max_history: int = 20  # Maximum number of messages to keep in history


class Agent:
    """Simple agent that uses an LLM model to respond to user input.
    简单 Agent，使用 LLM 模型响应用户输入。
    """

    def __init__(
        self,
        model: LLMModel,
        config: Optional[AgentConfig] = None,
        agent_id: Optional[str] = None,
    ):
        """Initialize the agent.
        初始化 Agent。

        Args:
            model: The LLM model to use for generating responses.
                用于生成响应的 LLM 模型。
            config: Agent configuration (optional).
                Agent 配置（可选）。
            agent_id: Unique identifier for the agent (optional).
                Agent 的唯一标识符（可选）。
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.model = model
        self.config = config or AgentConfig()
        self.history: List[Message] = []
        self.is_active = True

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to the conversation history.
        将消息添加到对话历史。

        Args:
            role: Message role ("system", "user", "assistant").
                消息角色。
            content: Message content.
                消息内容。
            metadata: Additional metadata (optional).
                附加元数据（可选）。

        Returns:
            The created Message object.
            创建的消息对象。
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.history.append(message)

        # Trim history if it exceeds max_history
        if len(self.history) > self.config.max_history:
            # Keep system messages and recent messages
            self.history = self.history[-self.config.max_history :]

        return message

    def get_context_messages(self) -> List[Dict[str, str]]:
        """Get messages formatted for the LLM context.
        获取为 LLM 上下文格式化的消息。

        Returns:
            List of message dictionaries for the LLM.
            用于 LLM 的消息字典列表。
        """
        messages = []

        # Add system prompt
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})

        # Add conversation history (excluding system messages from history)
        for msg in self.history:
            if msg.role != "system":
                messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def respond(self, user_input: str) -> str:
        """Generate a response to user input.
        为用户输入生成响应。

        Args:
            user_input: The user's input text.
                用户的输入文本。

        Returns:
            The agent's response text.
            Agent 的响应文本。
        """
        if not self.is_active:
            return "Agent is not active."

        # Add user message to history
        self.add_message("user", user_input)

        # Get context for the model
        context_messages = self.get_context_messages()

        # Build the prompt from context
        prompt = self._build_prompt(context_messages)

        # Generate response using the model
        response = await self.model.generate(
            prompt=prompt,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Add assistant response to history
        self.add_message("assistant", response)

        return response

    def _build_prompt(self, context_messages: List[Dict[str, str]]) -> str:
        """Build the prompt from context messages.
        从上下文消息构建提示。

        Args:
            context_messages: List of message dictionaries.
                消息字典列表。

        Returns:
            Formatted prompt string.
            格式化的提示字符串。
        """
        # If there are context messages, use the last user message as the prompt
        # The model will receive the full context including system prompt
        for msg in reversed(context_messages):
            if msg["role"] == "user":
                return msg["content"]

        # Fallback to empty prompt
        return ""

    def clear_history(self):
        """Clear the conversation history.
        清空对话历史。
        """
        self.history = []

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.
        获取 Agent 的当前状态。

        Returns:
            Dictionary with agent status information.
            包含 Agent 状态信息的字典。
        """
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "is_active": self.is_active,
            "model": self.model.name,
            "message_count": len(self.history),
            "temperature": self.config.temperature,
        }

    def activate(self):
        """Activate the agent.
        激活 Agent。
        """
        self.is_active = True

    def deactivate(self):
        """Deactivate the agent.
        停用 Agent。
        """
        self.is_active = False


if __name__ == "__main__":
    import asyncio
    from app.core.model import LMStudioModel

    model = LMStudioModel(
        base_url="http://127.0.0.1:1234", model_name="qwen/qwen3-1.7b"
    )
    agent = Agent(model=model)
    agent.activate()
    print(agent.get_status())
    response = asyncio.run(agent.respond("你好"))
    print(response)
    agent.deactivate()
    print(agent.get_status())
