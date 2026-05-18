# Simple Agent Implementation with Tool Calling
# 简单 Agent 实现（支持工具调用）

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
import uuid
import json

from app.core.model import BaseModel as LLMModel
from app.tools.tool import ToolRegistry


@dataclass
class Message:
    """Represents a single message in the conversation.
    表示对话中的单条消息。
    """

    role: str  # "system", "user", "assistant", "tool"
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
    enable_tools: bool = True  # Whether to enable tool calling
    max_tool_calls: int = 5  # Maximum tool calls per response
    debug: bool = False  # Enable debug logging


class Agent:
    """Simple agent that uses an LLM model to respond to user input.
    简单 Agent，使用 LLM 模型响应用户输入。
    """

    def __init__(
        self,
        model: LLMModel,
        config: Optional[AgentConfig] = None,
        agent_id: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None,
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
            tool_registry: Tool registry for tool calling (optional).
                工具调用注册表（可选）。
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.model = model
        self.config = config or AgentConfig()
        self.history: List[Message] = []
        self.is_active = True
        self.tool_registry = tool_registry or ToolRegistry()

        # Pass debug flag to model if it supports it
        if hasattr(self.model, "debug"):
            self.model.debug = self.config.debug

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to the conversation history.
        将消息添加到对话历史。

        Args:
            role: Message role ("system", "user", "assistant", "tool").
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

        # ReAct loop: Reason -> Act -> Observe -> Reason...
        tool_call_count = 0
        max_tool_calls = self.config.max_tool_calls
        consecutive_errors = 0
        max_consecutive_errors = 3
        recent_tool_calls: List[Dict[str, Any]] = []
        max_same_tool_calls = 2

        while tool_call_count < max_tool_calls:
            if self.config.debug:
                print(f"\n[DEBUG] ReAct loop iteration {tool_call_count + 1}/{max_tool_calls}")

            # Get context for the model
            context_messages = self.get_context_messages()

            # Build the prompt from context
            prompt = self._build_prompt(context_messages)
            if self.config.debug:
                print(f"[DEBUG] Prompt: {prompt[:200]}...")

            # Generate response using the model
            response = await self.model.generate(
                prompt=prompt,
                system_prompt=self.config.system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            if self.config.debug:
                print(f"[DEBUG] Model response: {response[:200]}...")

            # Check if response contains tool call
            if self.config.enable_tools:
                tool_call = self._parse_tool_call(response)
                if tool_call:
                    if self.config.debug:
                        print(f"[DEBUG] Parsed tool call: {tool_call}")

                    # Check for duplicate tool call
                    is_duplicate, dup_msg = self._check_duplicate_tool_call(tool_call, recent_tool_calls)
                    if is_duplicate:
                        if self.config.debug:
                            print(f"[DEBUG] Duplicate tool call detected: {dup_msg}")
                        result = dup_msg
                        is_error = True
                        # Add duplicate warning to history
                        self.add_message(
                            "assistant",
                            f"Called tool: {tool_call.get('name', 'unknown')}",
                            metadata={"tool_call": tool_call},
                        )
                        self.add_message(
                            "tool",
                            result,
                            metadata={"tool_name": tool_call.get("name")},
                        )
                    else:
                        # Execute the tool and add results to history
                        result, is_error = await self._execute_tool_call(tool_call)
                        recent_tool_calls.append(tool_call)

                    if self.config.debug:
                        print(f"[DEBUG] Tool execution result: {result[:200]}...")

                    if is_error:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            if self.config.debug:
                                print(f"[DEBUG] Max consecutive errors ({max_consecutive_errors}) reached")
                            return f"Tool execution failed after {max_consecutive_errors} attempts: {result}"
                        # Error feedback - don't increment tool_call_count, let model retry
                        continue
                    else:
                        consecutive_errors = 0
                        tool_call_count += 1
                        continue  # Continue the loop for next reasoning step
                else:
                    if self.config.debug:
                        print(f"[DEBUG] No tool call detected in response")

            # No tool call - this is the final response
            consecutive_errors = 0
            self.add_message("assistant", response)
            return response

        # Max tool calls reached
        if self.config.debug:
            print(f"[DEBUG] Max tool calls ({max_tool_calls}) reached")
        return "Maximum tool calls reached. Please refine your request."

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from model response.
        从模型响应中解析工具调用。

        Args:
            response: Model response text.
                模型响应文本。

        Returns:
            Tool call dict or None if no tool call found.
            工具调用字典，如果未找到则返回 None。
        """
        prefix = "TOOL_CALL:"
        stripped = response.strip()

        # Only treat as tool call if response starts with TOOL_CALL:
        if stripped.startswith(prefix):
            try:
                tool_data = json.loads(stripped[len(prefix):])
                return tool_data
            except json.JSONDecodeError:
                return None

        return None

    def _check_duplicate_tool_call(
        self, tool_call: Dict[str, Any], recent_calls: List[Dict[str, Any]]
    ) -> tuple[bool, str]:
        """Check if tool call is a duplicate of recent calls.
        检查工具调用是否与近期调用重复。

        Args:
            tool_call: Current tool call data.
                当前工具调用数据。
            recent_calls: List of recent tool calls.
                近期工具调用列表。

        Returns:
            Tuple of (is_duplicate, error_message).
            是否重复和错误消息的元组。
        """
        tool_name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", {})

        # Check if same tool with same arguments was called recently
        for prev in recent_calls:
            if prev.get("name") == tool_name and prev.get("arguments") == arguments:
                msg = (
                    f"Duplicate tool call detected: {tool_name} with same arguments. "
                    f"You have already called this tool. Use the previous result or try a different approach."
                )
                return True, msg

        return False, ""

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> tuple[str, bool]:
        """Execute a tool call and add results to history.
        执行工具调用并将结果添加到历史中。

        Args:
            tool_call: Tool call data.
                工具调用数据。

        Returns:
            Tuple of (result string, is_error flag).
            结果字符串和错误标志的元组。
        """
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        if not tool_name:
            result = "Invalid tool call: missing tool name."
            is_error = True
        else:
            # Execute the tool
            try:
                result = await self.tool_registry.execute_tool(tool_name, **arguments)
                is_error = result.startswith("Error")
            except Exception as e:
                result = f"Error executing tool '{tool_name}': {str(e)}"
                is_error = True

        # Add tool call and result to history
        self.add_message(
            "assistant",
            f"Called tool: {tool_name}",
            metadata={"tool_call": tool_call},
        )
        self.add_message(
            "tool",
            result,
            metadata={"tool_name": tool_name},
        )

        return result, is_error

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
        prompt_parts = []

        # Add tool instructions if tools are enabled
        if self.config.enable_tools and self.tool_registry.list_tools():
            tool_defs = self.tool_registry.get_tool_definitions()
            tool_names = [t["function"]["name"] for t in tool_defs]
            prompt_parts.append(
                f"Available tools: {', '.join(tool_names)}. "
                f"If you need to use a tool, respond with ONLY: "
                f'TOOL_CALL:{{"name": "tool_name", "arguments": {{"arg name(e.g., action)": "arg value"}}, {{"arg name": "arg value"}}}}'
                f"\nIMPORTANT: After receiving tool results, analyze if the task is complete. "
                f"If complete, respond with a final answer WITHOUT TOOL_CALL. "
                f"Only use TOOL_CALL when you still need more information."
            )

            # Add detailed tool parameter definitions
            for tool_def in tool_defs:
                func = tool_def["function"]
                params = func["parameters"]["properties"]
                required = func["parameters"].get("required", [])
                param_desc = []
                for pname, pinfo in params.items():
                    ptype = pinfo.get("type", "string")
                    pdesc = pinfo.get("description", "")
                    preq = "(required)" if pname in required else "(optional)"
                    penum = f" Options: {', '.join(pinfo.get('enum', []))}" if "enum" in pinfo else ""
                    param_desc.append(f"  - {pname} ({ptype}) {preq}: {pdesc}{penum}")
                prompt_parts.append(
                    f"Tool '{func['name']}' parameters:\n"
                    + "\n".join(param_desc)
                )

        # Include full conversation history (excluding system prompt)
        for msg in context_messages:
            if msg["role"] != "system":
                if msg["role"] == "user":
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    prompt_parts.append(f"Assistant: {msg['content']}")
                elif msg["role"] == "tool":
                    prompt_parts.append(f"Tool result: {msg['content']}")

        return "\n".join(prompt_parts) if prompt_parts else ""

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
            "tools_enabled": self.config.enable_tools,
            "registered_tools": len(self.tool_registry.list_tools()),
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
    from app.tools.builtins.file_tool import FileTool

    model = LMStudioModel(
        base_url="http://127.0.0.1:1234", model_name="qwen/qwen3-4b-2507"
    )

    registry = ToolRegistry()
    registry.register(FileTool())

    config = AgentConfig(
        name="test_agent",
        temperature=0.7,
        enable_tools=True,
        debug=True,
    )

    agent = Agent(model=model, tool_registry=registry, config=config)
    agent.activate()
    print(agent.get_status())
    response = asyncio.run(agent.respond("List the files in the /tmp directory"))
    print(response)
    agent.deactivate()
    print(agent.get_status())
