import os
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch

from dria.request import RPCClient
from dria.models.exceptions import (
    RPCConnectionError,
    RPCAuthenticationError,
)
from dria import constants


@pytest.fixture
def rpc_client():
    return RPCClient(auth_token=os.environ["RPC_TOKEN"])


@pytest.mark.asyncio
async def test_health_check_success(rpc_client):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await rpc_client.health_check() is True
        mock_get.assert_called_once_with(f"{constants.RPC_BASE_URL_COMMUNITY}/health")


@pytest.mark.asyncio
async def test_health_check_failure(rpc_client):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await rpc_client.health_check() is False
        mock_get.assert_called_once_with(f"{constants.RPC_BASE_URL_COMMUNITY}/health")


@pytest.mark.asyncio
async def test_health_check_connection_error(rpc_client):
    with patch(
        "aiohttp.ClientSession.get",
        side_effect=aiohttp.ClientError("Test connection error"),
    ):
        with pytest.raises(
            RPCConnectionError, match="Health check failed: Test connection error"
        ):
            await rpc_client.health_check()


@pytest.mark.asyncio
async def test_get_content_topic_success(rpc_client):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"data": {"results": ["result1", "result2"]}}
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        results = await rpc_client.get_content_topic("test_topic")
        assert results == ["result1", "result2"]
        mock_get.assert_called_once_with(
            f"{constants.RPC_BASE_URL_COMMUNITY}/rpc/test_topic"
        )


@pytest.mark.asyncio
async def test_get_content_topic_authentication_error(rpc_client):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(RPCAuthenticationError):
            await rpc_client.get_content_topic("test_topic")


@pytest.mark.asyncio
async def test_get_content_topic_connection_error(rpc_client):
    with patch(
        "aiohttp.ClientSession.get",
        side_effect=aiohttp.ClientError("Test connection error"),
    ):
        with pytest.raises(RPCConnectionError, match="Test connection error"):
            await rpc_client.get_content_topic("test_topic")


@pytest.mark.asyncio
async def test_push_content_topic_success(rpc_client):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response

        assert await rpc_client.push_content_topic("test_data", "test_topic") is True
        mock_post.assert_called_once_with(
            f"{constants.RPC_BASE_URL_COMMUNITY}/rpc/test_topic",
            json={"value": {"payload": "test_data"}},
            headers={"Content-Type": "application/json"},
        )


@pytest.mark.asyncio
async def test_push_content_topic_authentication_error(rpc_client):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(RPCAuthenticationError):
            await rpc_client.push_content_topic("test_data", "test_topic")


@pytest.mark.asyncio
async def test_push_content_topic_connection_error(rpc_client):
    with patch(
        "aiohttp.ClientSession.post",
        side_effect=aiohttp.ClientError("Test connection error"),
    ):
        with pytest.raises(
            RPCConnectionError, match="Connection error: Test connection error"
        ):
            await rpc_client.push_content_topic("test_data", "test_topic")


@pytest.mark.asyncio
async def test_push_content_topic_too_large(rpc_client):
    long_data = "a" * (rpc_client.NETWORK_MAX_MESSAGE_SIZE * 1024 + 1)
    with pytest.raises(
        ValueError,
        match=f"Data size \\({rpc_client.NETWORK_MAX_MESSAGE_SIZE*1024+1} bytes\\) exceeds the maximum allowed size of {rpc_client.NETWORK_MAX_MESSAGE_SIZE} bytes",
    ):
        await rpc_client.push_content_topic(long_data, "test_topic")


@pytest.mark.asyncio
async def test_rpc_token_missing():
    with pytest.raises(ValueError, match="RPC token is required for Dria RPC."):
        RPCClient(auth_token=None)
