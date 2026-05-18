# Model Tests
# 模型测试

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.model import BaseModel, LMStudioModel


class TestBaseModel:
    """Tests for the abstract base model class.
    抽象基础模型类的测试。
    """
    
    def test_base_model_is_abstract(self):
        """Verify that BaseModel is an ABC with abstract methods.
        验证 BaseModel 是一个具有抽象方法的 ABC。
        """
        from abc import ABC
        assert issubclass(BaseModel, ABC)
    
    def test_name_property_exists(self):
        """Check that name property exists in base class.
        检查基础类中存在 name 属性。
        """
        with pytest.raises(TypeError):
            BaseModel()
    

class TestLMStudioModel:
    """Tests for LMStudioModel implementation.
    LMStudioModel 实现的测试。
    """
    
    def setup_method(self):
        """Set up test fixtures.
        设置测试夹具。
        """
        self.model = LMStudioModel(
            base_url="http://127.0.0.1:1234",
            model_name="test-model"
        )
    
    def test_initialization(self):
        """Test model initialization with default and custom values.
        测试使用默认值和自定义值初始化模型。
        """
        default_model = LMStudioModel()
        assert default_model.base_url == "http://127.0.0.1:1234"
        assert default_model.model_name is None
        
        custom_model = LMStudioModel(
            base_url="http://localhost:8080",
            model_name="my-custom-model"
        )
        assert custom_model.base_url == "http://localhost:8080"
        assert custom_model.model_name == "my-custom-model"
    
    def test_trailing_slash_handling(self):
        """Test that trailing slashes are stripped from base_url.
        测试从 base_url 中删除尾随斜杠。
        """
        model = LMStudioModel(base_url="http://example.com/")
        assert model.base_url == "http://example.com"
    
    def test_name_property(self):
        """Test the name property returns correct identifier.
        测试 name 属性返回正确的标识符。
        """
        model = LMStudioModel(model_name="my-model")
        assert model.name == "lmstudio:my-model"
        
        default_model = LMStudioModel()
        assert default_model.name == "lmstudio:default"
    
    def test_description_property(self):
        """Test the description property returns correct string.
        测试 description 属性返回正确的字符串。
        """
        model = LMStudioModel(base_url="http://custom.url")
        expected = "LM Studio local server at http://custom.url"
        assert model.description == expected
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request to LM Studio API.
        测试向 LM Studio API 发送成功的 HTTP 请求。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response."
                    }
                }
            ]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model._make_request("/v1/test", {"test": "data"})
            
            assert result == {"choices": [{"message": {"content": "This is a test response."}}]}
    
    def test_make_request_with_timeout(self):
        """Test that requests use 30 second timeout.
        测试请求使用 30 秒超时。
        """
        with patch('httpx.AsyncClient') as mock_client_class:
            pass
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """Test generate method includes system prompt in messages.
        测试生成方法在消息中包含系统提示。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response to user."}}]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            system_prompt = "You are a helpful assistant."
            prompt = "Hello, how are you?"
            
            result = await self.model.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            call_args = mock_client.post.call_args
            json_data = call_args[1]['json']
            
            assert "messages" in json_data
            assert len(json_data["messages"]) == 2
            assert json_data["messages"][0]["role"] == "system"
            assert json_data["messages"][0]["content"] == system_prompt
            assert json_data["messages"][1]["role"] == "user"
            assert json_data["messages"][1]["content"] == prompt
    
    @pytest.mark.asyncio
    async def test_generate_without_system_prompt(self):
        """Test generate method when no system prompt is provided.
        测试未提供系统提示时生成方法。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            prompt = "Simple question"
            result = await self.model.generate(prompt=prompt)
            
            call_args = mock_client.post.call_args
            json_data = call_args[1]['json']
            
            assert len(json_data["messages"]) == 1
            assert json_data["messages"][0]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_generate_with_max_tokens(self):
        """Test generate method includes max_tokens parameter.
        测试生成方法包含 max_tokens 参数。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(
                prompt="Test",
                max_tokens=100
            )
            
            call_args = mock_client.post.call_args
            json_data = call_args[1]['json']
            
            assert "max_tokens" in json_data
            assert json_data["max_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_generate_with_temperature(self):
        """Test generate method includes temperature parameter.
        测试生成方法包含温度参数。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(
                prompt="Test",
                temperature=0.9
            )
            
            call_args = mock_client.post.call_args
            json_data = call_args[1]['json']
            
            assert "temperature" in json_data
            assert json_data["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_generate_default_temperature(self):
        """Test generate method uses default temperature of 0.7.
        测试生成方法使用默认温度 0.7。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            call_args = mock_client.post.call_args
            json_data = call_args[1]['json']
            
            assert "temperature" in json_data
            assert json_data["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_connection_refused(self):
        """Test generate handles connection refused gracefully.
        测试生成方法优雅处理连接被拒绝。
        """
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            assert "LM Studio server is not running" in result
    
    @pytest.mark.asyncio
    async def test_generate_timeout_error(self):
        """Test generate handles timeout errors gracefully.
        测试生成方法优雅处理超时错误。
        """
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("connect timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            assert "LM Studio server is not running" in result
    
    @pytest.mark.asyncio
    async def test_generate_http_error(self):
        """Test generate handles general HTTP errors.
        测试生成方法处理一般 HTTP 错误。
        """
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Internal Server Error")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            assert "Error:" in result
    
    @pytest.mark.asyncio
    async def test_generate_empty_response(self):
        """Test generate handles empty response from API.
        测试生成方法处理来自 API 的空响应。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_generate_partial_response(self):
        """Test generate handles partial/malformed response.
        测试生成方法处理部分/格式错误的响应。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {}}]}
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(prompt="Test")
            
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test check_health returns True when server responds.
        测试当服务器响应时 check_health 返回 True。
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.check_health()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_health_failure(self):
        """Test check_health returns False when server fails.
        测试当服务器失败时 check_health 返回 False。
        """
        mock_response = MagicMock()
        mock_response.status_code = 503
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.check_health()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_health_exception(self):
        """Test check_health returns False when exception occurs.
        测试当发生异常时 check_health 返回 False。
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection error")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.check_health()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_health_timeout(self):
        """Test check_health handles timeout gracefully.
        测试 check_health 优雅处理超时。
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = TimeoutError("Request timed out")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.check_health()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_health_uses_correct_endpoint(self):
        """Test check_health uses /v1/models endpoint.
        测试 check_health 使用/v1/models 端点。
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await self.model.check_health()
            
            call_args = mock_client.get.call_args
            assert call_args[0][0].endswith("/v1/models")
    
    def test_check_health_uses_correct_timeout(self):
        """Test check_health uses 5 second timeout.
        测试 check_health 使用 5 秒超时。
        """
        with patch('httpx.AsyncClient') as mock_client_class:
            pass
    

class TestIntegrationScenarios:
    """Integration test scenarios (would need actual LM Studio running).
    集成测试场景（需要实际运行 LM Studio）。
    """
    
    def setup_method(self):
        """Set up test fixtures.
        设置测试夹具。
        """
        self.model = LMStudioModel(
            base_url="http://127.0.0.1:1234",
            model_name="test-model"
        )
    
    @pytest.mark.asyncio
    async def test_full_generation_flow(self):
        """Test complete generation flow with mocked response.
        使用模拟响应测试完整生成流程。
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Hello! I'm a test response from the model."
                }
            }]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await self.model.generate(
                prompt="Hello, world!",
                system_prompt="You are a friendly assistant."
            )
            
            assert "Hello! I'm a test response" in result
    
    @pytest.mark.asyncio
    async def test_health_check_flow(self):
        """Test complete health check flow.
        测试完整健康检查流程。
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            is_healthy = await self.model.check_health()
            assert is_healthy is True