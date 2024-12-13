import pytest
from dria.db.mq import KeyValueQueue
import asyncio


@pytest.fixture
async def queue():
    return KeyValueQueue()


@pytest.mark.asyncio
async def test_push_and_pop(queue):
    await queue.push("key1", "value1")
    await queue.push("key1", "value2")
    await queue.push("key2", "value3")

    assert await queue.pop("key1") == "value1"
    assert await queue.pop("key1") == "value2"
    assert await queue.pop("key2") == "value3"
    assert await queue.pop("key1") is None
    assert await queue.pop("nonexistent") is None


@pytest.mark.asyncio
async def test_peek(queue):
    await queue.push("key1", "value1")
    await queue.push("key1", "value2")

    assert await queue.peek("key1") == "value1"
    assert await queue.peek("key1") == "value1"  # Peek doesn't remove the value
    assert await queue.peek("nonexistent") is None


@pytest.mark.asyncio
async def test_is_empty(queue):
    assert await queue.is_empty("key1") is True
    await queue.push("key1", "value1")
    assert await queue.is_empty("key1") is False
    await queue.pop("key1")
    assert await queue.is_empty("key1") is True


@pytest.mark.asyncio
async def test_size(queue):
    assert await queue.size("key1") == 0
    await queue.push("key1", "value1")
    await queue.push("key1", "value2")
    assert await queue.size("key1") == 2
    assert await queue.size("nonexistent") == 0


@pytest.mark.asyncio
async def test_clear(queue):
    await queue.push("key1", "value1")
    await queue.push("key1", "value2")
    await queue.clear("key1")
    assert await queue.is_empty("key1") is True
    assert await queue.size("key1") == 0


@pytest.mark.asyncio
async def test_keys(queue):
    assert await queue.keys() == []
    await queue.push("key1", "value1")
    await queue.push("key2", "value2")
    keys = await queue.keys()
    assert len(keys) == 2
    assert "key1" in keys
    assert "key2" in keys


@pytest.mark.asyncio
async def test_concurrent_operations(queue):
    await queue.push("key1", "value1")
    await queue.push("key2", "value2")

    results = await asyncio.gather(
        queue.push("key1", "value3"),
        queue.pop("key1"),
        queue.peek("key2"),
        queue.size("key1"),
    )

    assert results[1] == "value1"  # pop result
    assert results[2] == "value2"  # peek result
    assert results[3] == 1  # size result after push and pop
