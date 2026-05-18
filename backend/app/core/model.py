# Model Interface and Implementations
# 模型接口和实现

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urljoin
from app.log import logger


class BaseModel(ABC):
    """Base model interface for LLM models.
    基础模型接口，用于大语言模型。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Model identifier/name.
        模型标识符/名称。
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Model description.
        模型描述。
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response for the given prompt.
        为给定的提示生成响应。

        Args:
            prompt: User input text.
                用户输入文本。
            system_prompt: System instructions (optional).
                系统指令（可选）。
            temperature: Sampling temperature (0.0-2.0).
                采样温度（0.0-2.0）。
            max_tokens: Maximum tokens to generate (optional).
                生成的最大 token 数（可选）。

        Returns:
            Generated response text.
            生成的响应文本。
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if the model service is healthy.
        检查模型服务是否健康。
        """
        pass


class LMStudioModel(BaseModel):
    """LM Studio local LLM interface implementation.
    LM Studio 本地大语言模型接口实现。

    This implements an OpenAI-compatible client for LM Studio's
    local server running on http://127.0.0.1:1234.
    这实现了 LM Studio 本地服务器的 OpenAI 兼容客户端，
    运行在 http://127.0.0.1:1234。
    """

    def __init__(
        self, base_url: str = "http://127.0.0.1:1234", model_name: Optional[str] = None, debug: bool = False
    ):
        """Initialize LM Studio client.
        初始化 LM Studio 客户端。

        Args:
            base_url: Base URL for LM Studio API.
                LM Studio API 的基础 URL。
            model_name: Specific model to use (optional).
                要使用的特定模型（可选）。
            debug: Enable debug logging.
                启用调试日志。
        """
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.debug = debug

    @property
    def name(self) -> str:
        """Model identifier.
        模型标识符。
        """
        return f"lmstudio:{self.model_name or 'default'}"

    @property
    def description(self) -> str:
        """Model description.
        模型描述。
        """
        return f"LM Studio local server at {self.base_url}"

    async def _make_request(
        self, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to LM Studio API.
        向 LM Studio API 发送 HTTP 请求。

        Args:
            endpoint: API endpoint path.
                API 端点路径。
            json_data: JSON payload (optional).
                JSON 负载（可选）。

        Returns:
            Response JSON data.
            响应 JSON 数据。
        """
        url = urljoin(self.base_url, endpoint)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=json_data)
            response.raise_for_status()
            return response.json()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate response using LM Studio API.
        使用 LM Studio API 生成响应。

        Args:
            prompt: User input text.
                用户输入文本。
            system_prompt: System instructions (optional).
                系统指令（可选）。
            temperature: Sampling temperature (0.0-2.0).
                采样温度（0.0-2.0）。
            max_tokens: Maximum tokens to generate.
                生成的最大 token 数。

        Returns:
            Generated response text.
            生成的响应文本。
        """
        # Build chat completion request
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        params = {"messages": messages, "temperature": temperature}
        if self.model_name:
            params["model"] = self.model_name
        if max_tokens:
            params["max_tokens"] = max_tokens

        if self.debug:
            logger.info(f"\n[MODEL DEBUG] generate() called:")
            logger.info(f"  - model: {self.model_name}")
            logger.info(f"  - temperature: {temperature}")
            logger.info(f"  - max_tokens: {max_tokens}")
            logger.info(f"  - messages count: {len(messages)}")
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown")
                content_preview = str(msg.get("content", ""))[:100]
                logger.info(f"  - message[{i}]: role={role}, content={content_preview}...")
            logger.info(f"  - tools: {params.get('tools', 'NOT SET')}")
            logger.info(f"  - tool_choice: {params.get('tool_choice', 'NOT SET')}")
            logger.info(f"  - full params keys: {list(params.keys())}")

        try:
            result = await self._make_request("/v1/chat/completions", json_data=params)
            choices = result.get("choices", [])
            if not choices:
                return ""
            return choices[0].get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "connect timed out" in error_msg:
                return "LM Studio server is not running. Please start LM Studio first."
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "connect timed out" in error_msg:
                return "LM Studio server is not running. Please start LM Studio first."
            return f"Error: {error_msg}"

    async def check_health(self) -> bool:
        """Check if LM Studio server is running.
        检查 LM Studio 服务器是否运行。

        Returns:
            True if server is healthy, False otherwise.
            如果服务器健康则返回 True，否则返回 False。
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    urljoin(self.base_url, "/v1/models"), follow_redirects=False
                )
                return response.status_code == 200
        except Exception:
            return False


if __name__ == "__main__":
    import asyncio

    model = LMStudioModel(
        base_url="http://127.0.0.1:1234", model_name="qwen/qwen3-1.7b"
    )
    health = asyncio.run(model.check_health())
    logger.info(health)
    response = asyncio.run(model.generate("你好"))
    logger.info(response)
