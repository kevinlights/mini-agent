# API Routes for Mini-Agent
# Mini-Agent 的 API 路由

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
import asyncio

from app.api.schemas import (
    ChatRequest, 
    ChatResponse, 
    ErrorResponse, 
    AgentConfigRequest,
    AgentStatusResponse
)
from app.core.agent import Agent, AgentConfig
from app.core.model import LMStudioModel
from app.core.memory import MemorySystem
from app.core.context import ContextConfig
from app.skills.skill import SkillRegistry
from app.tools.tool import ToolRegistry
from app.tools.builtins.file_tool import FileTool
from app.config import config
from app.log import logger


router = APIRouter(prefix="/api/v1")


# Global agent instance (in production, you'd want to use dependency injection)
# 全局代理实例（在生产环境中，您需要使用依赖注入）
_agents: Dict[str, Agent] = {}
_memory_system = MemorySystem(storage_path=config.memory_path)
_skill_registry = SkillRegistry()
_tool_registry = ToolRegistry()

# Register built-in tools
# 注册内置工具
_tool_registry.register(FileTool())

# Load skills
# 加载技能
try:
    skills_path = Path(config.skills_path)
    if skills_path.exists():
        if skills_path.is_dir():
            for md_file in skills_path.glob("**/*.md"):
                if not md_file.name.startswith("_"):
                    _skill_registry.load_from_markdown(str(md_file))
        else:
            _skill_registry.load_from_markdown(config.skills_path)
except Exception as e:
    logger.warning("Failed to load skills: %s", str(e))


def get_agent(agent_id: str) -> Agent:
    """Get agent by ID.
    按 ID 获取代理。

    Args:
        agent_id: Agent ID.
            代理 ID。

    Returns:
        Agent instance.
            代理实例。
    """
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return _agents[agent_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat request.
    处理聊天请求。

    Args:
        request: Chat request body.
            聊天请求体。

    Returns:
        Chat response.
            聊天响应。
    """
    try:
        # Check if conversation_id is provided, otherwise create new conversation
        # 检查是否提供了 conversation_id，否则创建新对话
        is_new_conversation = not request.conversation_id
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Try to get existing agent, or create new one
        # 尝试获取已有代理，或创建新代理
        agent_id = f"agent_{conversation_id[:8]}"
        
        if agent_id not in _agents:
            # If conversation_id was provided but agent doesn't exist, return 404
            # 如果提供了 conversation_id 但代理不存在，返回 404
            if not is_new_conversation:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Conversation {conversation_id} not found"
                )
            
            # Create new agent
            # 创建新代理
            model = LMStudioModel(base_url=config.model_base_url, model_name=config.model_name)
            
            agent_config = AgentConfig(
                name=request.agent_config.name if request.agent_config else "Assistant",
                system_prompt=request.agent_config.system_prompt if request.agent_config else "You are a helpful assistant.",
                temperature=request.agent_config.temperature if request.agent_config else 0.7,
                max_tokens=request.agent_config.max_tokens if request.agent_config else None,
                max_history=request.agent_config.max_history if request.agent_config else 20,
                enable_tools=request.agent_config.enable_tools if request.agent_config else True,
                max_tool_calls=request.agent_config.max_tool_calls if request.agent_config else 5,
                debug=request.agent_config.debug if request.agent_config else False,
                context_config=ContextConfig(
                    max_tokens=config.context_max_tokens,
                    compression_threshold=0.8,
                    keep_recent_count=5
                )
            )
            
            agent = Agent(
                model=model,
                config=agent_config,
                agent_id=agent_id,
                memory_system=_memory_system,
                skill_registry=_skill_registry,
                tool_registry=_tool_registry
            )
            
            _agents[agent_id] = agent
        
        agent = _agents[agent_id]
        
        # Add history to agent if provided
        # 如果提供了历史记录，则将其添加到代理
        for msg in request.history:
            agent.add_message(role=msg.role, content=msg.content)
        
        # Get response from agent
        # 从代理获取响应
        response = await agent.respond(request.message)
        
        # Return response
        # 返回响应
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            agent_status={
                "active": agent.is_active,
                "history_length": len(agent.history),
                "agent_id": agent.agent_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str) -> AgentStatusResponse:
    """Get agent status.
    获取代理状态。

    Args:
        agent_id: Agent ID.
            代理 ID。

    Returns:
        Agent status.
            代理状态。
    """
    try:
        agent = get_agent(agent_id)
        return AgentStatusResponse(
            status={
                "active": agent.is_active,
                "history_length": len(agent.history),
                "agent_id": agent.agent_id,
                "config": {
                    "name": agent.config.name,
                    "temperature": agent.config.temperature,
                    "enable_tools": agent.config.enable_tools,
                    "debug": agent.config.debug
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/{agent_id}")
async def reset_agent(agent_id: str) -> Dict[str, str]:
    """Reset agent conversation history.
    重置代理对话历史。

    Args:
        agent_id: Agent ID.
            代理 ID。

    Returns:
        Success message.
            成功消息。
    """
    try:
        agent = get_agent(agent_id)
        agent.history.clear()
        return {"message": f"Agent {agent_id} history cleared"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    健康检查端点。

    Returns:
        Health status.
            健康状态。
    """
    return {"status": "healthy", "service": "mini-agent-api"}


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List all agents.
    列出所有代理。

    Returns:
        Dictionary of agent IDs and basic info.
            代理 ID 和基本信息的字典。
    """
    agents_info = {}
    for agent_id, agent in _agents.items():
        agents_info[agent_id] = {
            "active": agent.is_active,
            "history_length": len(agent.history),
            "last_updated": agent.history[-1].timestamp if agent.history else None
        }
    
    return {"agents": agents_info}