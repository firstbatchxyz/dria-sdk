import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from dria.executor import Ping
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.request import RPCClient


# Fixture to create test Monitor instance
@pytest.fixture
def monitor():
    storage = Mock(spec=Storage)
    rpc = Mock(spec=RPCClient)
    kv = Mock(spec=KeyValueQueue)
    return Ping(storage=storage, rpc=rpc, kv=kv)


# Test Monitor initialization
def test_monitor_init(monitor):
    assert monitor.rpc is not None
    assert monitor.task_manager is not None


# Test checking heartbeat responses
@pytest.mark.asyncio
async def test_check_heartbeat_success(monitor):
    # Mock response data
    mock_response = (
        "ZjMyZGQ0MWZjNmUyZmUwNjcwNDFhY2Y5MjU0MTQyNjM4ZTk2YWFmZDljZDM3MzgyNjdkOWI1MjM0MzA0ZDY0NDAyYzc5YTFkYmV"
        "iMTU5ZGY4YWI1Y2MzMTA3OGFmYzY5MGE5MzVlNDJlYmQyMDFkZTc2NThkMzNkOGQ2ZmU5NjUwMXsibW9kZWxzIjpbWyJvbGx"
        "hbWEiLCJmaW5hbGVuZC9oZXJtZXMtMy1sbGFtYS0zLjE6OGItcThfMCJdLFsib2xsYW1hIiwicGhpMy41OjMuOGIiXSxbIm"
        "9sbGFtYSIsInBoaTMuNTozLjhiLW1pbmktaW5zdHJ1Y3QtZnAxNiJdLFsib2xsYW1hIiwiZ2VtbWEyOjliLWluc3RydWN0L"
        "XE4XzAiXSxbIm9sbGFtYSIsImxsYW1hMy4xOmxhdGVzdCJdLFsib2xsYW1hIiwibGxhbWEzLjE6OGItaW5zdHJ1Y3QtcThf"
        "MCJdLFsib2xsYW1hIiwibGxhbWEzLjE6OGItdGV4dC1xNF9LX00iXSxbIm9sbGFtYSIsImxsYW1hMy4xOjhiLXRleHQtcThf"
        "MCJdLFsib2xsYW1hIiwibGxhbWEzLjI6MWIiXSxbIm9sbGFtYSIsImxsYW1hMy4yOjFiLXRleHQtcTRfS19NIl0sWyJvbGxh"
        "bWEiLCJsbGFtYTMuMjozYiJdLFsib2xsYW1hIiwicXdlbjIuNTo3Yi1pbnN0cnVjdC1xNV8wIl0sWyJvbGxhbWEiLCJxd2Vu"
        "Mi41LWNvZGVyOjEuNWIiXSxbIm9sbGFtYSIsInF3ZW4yLjUtY29kZXI6N2ItaW5zdHJ1Y3QiXSxbIm9sbGFtYSIsInF3ZW4yL"
        "jUtY29kZXI6N2ItaW5zdHJ1Y3QtcThfMCJdLFsib2xsYW1hIiwiZGVlcHNlZWstY29kZXI6Ni43YiJdXSwicGVuZGluZ190YX"
        "NrcyI6WzAsMF0sInV1aWQiOiI0MmFDWkNnby0tcDEifQ=="
    )
    mock_nodes = {
        "finalend/hermes-3-llama-3.1:8b-q8_0": [
            "283cb35ea7b95891df841ccb772ad4104e646aa3"
        ]
    }

    # Setup mocks
    monitor.rpc.get_content_topic = AsyncMock(return_value=[mock_response])
    monitor.task_manager.add_available_nodes = AsyncMock()

    with patch.object(Ping, "_decrypt_nodes", return_value=mock_nodes):
        result = await monitor._check_heartbeat()
        assert result is True
        monitor.task_manager.add_available_nodes.assert_called_once()


@pytest.mark.asyncio
async def test_check_heartbeat_no_responses(monitor):
    monitor.rpc.get_content_topic = AsyncMock(return_value=[])
    result = await monitor._check_heartbeat()
    assert result is False


@pytest.mark.asyncio
async def test_check_heartbeat_no_rpc(monitor):
    monitor.rpc = None
    result = await monitor._check_heartbeat()
    assert result is False


# Test node decryption
def test_decrypt_nodes_success():
    # Mock node response data
    mock_signature = "6eb1267708b79fc492ce5a11665a5fb02c1ac8425f04d9b3137d9efadaa04b2e752efd14c4993cc193c125e8d853c869df144d359cb75fc45df872600000000000"
    mock_metadata = {
        "models": [["ollama", "finalend/hermes-3-llama-3.1:8b-q8_0"]],
        "pending_tasks": [0, 0],
        "uuid": "--p1",
    }
    mock_response = mock_signature + json.dumps(mock_metadata)

    with patch("dria.utilities.recover_public_key", return_value=b"test_key"), patch(
        "dria.utilities.uncompressed_public_key", return_value=b"uncompressed_key"
    ):
        result = Ping._decrypt_nodes([mock_response])
        assert isinstance(result, dict)
        assert all(isinstance(v, list) for v in result.values())


def test_decrypt_nodes_invalid_response():
    result = Ping._decrypt_nodes(["invalid_response"])
    assert result == {}


# Test monitor run
@pytest.mark.asyncio
async def test_run_success(monitor):
    monitor._check_heartbeat = AsyncMock(return_value=True)
    await monitor.run()
    monitor._check_heartbeat.assert_called_once()


@pytest.mark.asyncio
async def test_run_failure(monitor):
    monitor._check_heartbeat = AsyncMock(side_effect=Exception("Test error"))
    with pytest.raises(Exception):
        await monitor.run()
