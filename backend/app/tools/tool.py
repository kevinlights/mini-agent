# Tool Base Class and Registry
# 工具基础类和注册表

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ToolParameter:
    """Definition of a tool parameter.
    工具参数的定义。
    """

    name: str
    type: str  # "string", "integer", "boolean", "number", "array", "object"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    """Definition of a tool for LLM function calling.
    工具的定义，用于 LLM 函数调用。
    """

    name: str
    description: str
    parameters: List[ToolParameter]

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format.
        转换为 OpenAI 函数调用格式。
        """
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class BaseTool(ABC):
    """Base class for all tools.
    所有工具的基础类。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool.
        工具的唯一名称。
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does.
        工具功能的描述。
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """List of tool parameters.
        工具参数列表。
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters.
        使用给定参数执行工具。

        Args:
            **kwargs: Parameter values.
                参数值。

        Returns:
            Result string.
            结果字符串。
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition.
        获取工具定义。
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format.
        转换为 OpenAI 函数调用格式。
        """
        return self.get_definition().to_openai_format()


class ToolRegistry:
    """Registry for managing available tools.
    管理可用工具的注册表。
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a tool.
        注册一个工具。

        Args:
            tool: The tool instance to register.
                要注册的工具实例。
        """
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str):
        """Unregister a tool by name.
        按名称注销一个工具。

        Args:
            tool_name: Name of the tool to unregister.
                要注销的工具名称。
        """
        self._tools.pop(tool_name, None)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        按名称获取工具。

        Args:
            tool_name: Name of the tool.
                工具名称。

        Returns:
            The tool instance, or None if not found.
            工具实例，如果未找到则返回 None。
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools.
        列出所有已注册的工具。

        Returns:
            List of tool instances.
            工具实例列表。
        """
        return list(self._tools.values())

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI format definitions for all tools.
        获取所有工具的 OpenAI 格式定义。

        Returns:
            List of tool definitions in OpenAI format.
            OpenAI 格式的工具定义列表。
        """
        return [tool.to_openai_format() for tool in self._tools.values()]

    async def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters.
        按名称执行工具并给定参数。

        Args:
            tool_name: Name of the tool to execute.
                要执行的工具名称。
            **kwargs: Parameter values.
                参数值。

        Returns:
            Result string.
            结果字符串。

        Raises:
            ValueError: If tool not found.
                如果未找到工具则抛出。
        """
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return await tool.execute(**kwargs)
