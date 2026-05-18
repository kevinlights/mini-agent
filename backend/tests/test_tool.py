# Tool Tests
# 工具测试

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.tool import BaseTool, ToolRegistry, ToolParameter, ToolDefinition


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


class TestToolParameter:
    """Tests for ToolParameter.
    ToolParameter 的测试。
    """

    def test_required_parameter(self):
        param = ToolParameter(name="test", type="string", description="Test param")
        assert param.required is True
        assert param.enum is None

    def test_optional_parameter(self):
        param = ToolParameter(
            name="test", type="string", description="Test param", required=False
        )
        assert param.required is False

    def test_enum_parameter(self):
        param = ToolParameter(
            name="test",
            type="string",
            description="Test param",
            enum=["a", "b", "c"],
        )
        assert param.enum == ["a", "b", "c"]


class TestToolDefinition:
    """Tests for ToolDefinition.
    ToolDefinition 的测试。
    """

    def test_to_openai_format(self):
        params = [
            ToolParameter(name="input", type="string", description="Input text"),
            ToolParameter(
                name="optional",
                type="string",
                description="Optional param",
                required=False,
            ),
        ]
        definition = ToolDefinition(
            name="test_tool", description="Test tool", parameters=params
        )

        result = definition.to_openai_format()

        assert result["type"] == "function"
        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "Test tool"
        assert "input" in result["function"]["parameters"]["properties"]
        assert "optional" in result["function"]["parameters"]["properties"]
        assert "input" in result["function"]["parameters"]["required"]
        assert "optional" not in result["function"]["parameters"]["required"]


class TestBaseTool:
    """Tests for BaseTool.
    BaseTool 的测试。
    """

    def setup_method(self):
        self.tool = MockTool()

    def test_name(self):
        assert self.tool.name == "mock_tool"

    def test_description(self):
        assert self.tool.description == "A mock tool for testing."

    def test_parameters(self):
        assert len(self.tool.parameters) == 1
        assert self.tool.parameters[0].name == "input"

    def test_get_definition(self):
        definition = self.tool.get_definition()
        assert definition.name == "mock_tool"
        assert len(definition.parameters) == 1

    def test_to_openai_format(self):
        result = self.tool.to_openai_format()
        assert result["type"] == "function"
        assert result["function"]["name"] == "mock_tool"

    @pytest.mark.asyncio
    async def test_execute(self):
        result = await self.tool.execute(input="test")
        assert result == "Mock result: test"


class TestToolRegistry:
    """Tests for ToolRegistry.
    ToolRegistry 的测试。
    """

    def setup_method(self):
        self.registry = ToolRegistry()
        self.tool = MockTool()

    def test_register_tool(self):
        self.registry.register(self.tool)
        assert self.registry.get("mock_tool") == self.tool

    def test_unregister_tool(self):
        self.registry.register(self.tool)
        self.registry.unregister("mock_tool")
        assert self.registry.get("mock_tool") is None

    def test_unregister_nonexistent_tool(self):
        self.registry.unregister("nonexistent")

    def test_list_tools(self):
        self.registry.register(self.tool)
        tools = self.registry.list_tools()
        assert len(tools) == 1
        assert tools[0] == self.tool

    def test_get_tool_definitions(self):
        self.registry.register(self.tool)
        definitions = self.registry.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["function"]["name"] == "mock_tool"

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        self.registry.register(self.tool)
        result = await self.registry.execute_tool("mock_tool", input="test")
        assert result == "Mock result: test"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        with pytest.raises(ValueError, match="Tool 'unknown' not found"):
            await self.registry.execute_tool("unknown", input="test")
