# Pydantic Schemas for FastAPI
# FastAPI 的 Pydantic 模式

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Message(BaseModel):
    """Schema for conversation message.
    对话消息的模式。
    """

    role: str  # "user", "assistant", "tool"
    content: str


class AgentConfigRequest(BaseModel):
    """Schema for agent configuration request.
    代理配置请求的模式。
    """

    name: str = "Assistant"
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    max_history: int = 20
    enable_tools: bool = True
    max_tool_calls: int = 5
    debug: bool = False


class ChatRequest(BaseModel):
    """Schema for chat request.
    聊天请求的模式。
    """

    message: str
    conversation_id: Optional[str] = None  # For continuing conversations
    agent_config: Optional[AgentConfigRequest] = None
    history: List[Message] = []


class ChatResponse(BaseModel):
    """Schema for chat response.
    聊天响应的模式。
    """

    response: str
    conversation_id: str
    agent_status: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Schema for error response.
    错误响应的模式。
    """

    error: str
    detail: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Schema for agent status response.
    代理状态响应的模式。
    """

    status: Dict[str, Any]