# File Tool - Simple File Operations
# 文件工具 - 简单文件操作

import os
from typing import List
from pathlib import Path

from app.tools.tool import BaseTool, ToolParameter


class FileTool(BaseTool):
    """Tool for basic file operations.
    用于基本文件操作的工具。
    """

    @property
    def name(self) -> str:
        return "file_tool"

    @property
    def description(self) -> str:
        return "Read, write, and list files in the filesystem."

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform: 'read', 'write', or 'list'.",
                enum=["read", "write", "list"],
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File or directory path.",
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write (required for 'write' action).",
                required=False,
            ),
        ]

    async def execute(self, action: str, path: str, content: str = None) -> str:
        """Execute file operation.
        执行文件操作。

        Args:
            action: Operation type ('read', 'write', 'list').
                操作类型。
            path: File or directory path.
                文件或目录路径。
            content: Content to write (for 'write' action).
                要写入的内容（用于 'write' 操作）。

        Returns:
            Result string.
            结果字符串。
        """
        if action == "read":
            return self._read_file(path)
        elif action == "write":
            return self._write_file(path, content)
        elif action == "list":
            return self._list_directory(path)
        else:
            return f"Unknown action: {action}"

    def _read_file(self, path: str) -> str:
        """Read file content.
        读取文件内容。
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                return f"Error: File not found: {path}"
            if not file_path.is_file():
                return f"Error: Not a file: {path}"
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _write_file(self, path: str, content: str) -> str:
        """Write content to file.
        将内容写入文件。
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def _list_directory(self, path: str) -> str:
        """List directory contents.
        列出目录内容。
        """
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return f"Error: Directory not found: {path}"
            if not dir_path.is_dir():
                return f"Error: Not a directory: {path}"

            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "📁 " if item.is_dir() else "📄 "
                items.append(f"{prefix}{item.name}")

            if not items:
                return f"Directory is empty: {path}"

            return f"Contents of {path}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
