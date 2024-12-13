import pytest
import asyncio
import json
from dria.db.storage import Storage


@pytest.fixture
def storage():
    return Storage()


@pytest.mark.asyncio
async def test_set_value_no_expiry(storage: Storage):
    await storage.set_value("test_key", "test_value")
    assert await storage.get_value("test_key") == "test_value"


@pytest.mark.asyncio
async def test_set_value_with_expiry(storage: Storage):
    await storage.set_value("test_key", "test_value", ex=1)
    assert await storage.get_value("test_key") == "test_value"
    await asyncio.sleep(1.5)
    assert await storage.get_value("test_key") is None


@pytest.mark.asyncio
async def test_set_json(storage: Storage):
    test_data = {"name": "test", "value": 123}
    await storage.set_json("test_json_key", test_data)
    retrieved_value = await storage.get_value("test_json_key")
    assert json.loads(retrieved_value) == test_data


@pytest.mark.asyncio
async def test_get_value_key_not_found(storage: Storage):
    assert await storage.get_value("nonexistent_key") is None


@pytest.mark.asyncio
async def test_update_value_existing_key(storage: Storage):
    await storage.set_json("test_update_key", {"field1": "initial_value"})
    await storage.update_value("test_update_key", "field1", "updated_value")
    retrieved_value = await storage.get_value("test_update_key")
    assert json.loads(retrieved_value) == {"field1": "updated_value"}


@pytest.mark.asyncio
async def test_update_value_new_key(storage: Storage):
    await storage.update_value("test_new_key", "field2", "new_value")
    retrieved_value = await storage.get_value("test_new_key")
    assert json.loads(retrieved_value) == {"field2": "new_value"}


@pytest.mark.asyncio
async def test_append_value_existing_key(storage: Storage):
    await storage.set_json("test_append_key", {"field3": [1, 2]})
    await storage.append_value("test_append_key", "field3", 3)
    retrieved_value = await storage.get_value("test_append_key")
    assert json.loads(retrieved_value) == {"field3": [1, 2, 3]}


@pytest.mark.asyncio
async def test_append_value_new_key(storage: Storage):
    await storage.append_value("test_new_append_key", "field4", 1)
    retrieved_value = await storage.get_value("test_new_append_key")
    assert json.loads(retrieved_value) == {"field4": [1]}


@pytest.mark.asyncio
async def test_remove_from_list_existing_key_with_field(storage: Storage):
    await storage.set_json("test_remove_key", {"list_field": [1, 2, 3, 4]})
    await storage.remove_from_list("test_remove_key", "list_field", [2, 4])
    retrieved_value = await storage.get_value("test_remove_key")
    assert json.loads(retrieved_value) == {"list_field": [1, 3]}


@pytest.mark.asyncio
async def test_remove_from_list_existing_key_without_field(storage: Storage):
    await storage.set_json("test_remove_key_no_field", [1, 2, 3, 4])
    await storage.remove_from_list("test_remove_key_no_field", None, [2, 4])
    retrieved_value = await storage.get_value("test_remove_key_no_field")
    assert json.loads(retrieved_value) == [1, 3]


@pytest.mark.asyncio
async def test_remove_from_list_nonexistent_key(storage: Storage):
    with pytest.raises(
        ValueError,
        match="Key 'nonexistent_key' does not exist in the local dictionary.",
    ):
        await storage.remove_from_list("nonexistent_key", "some_field", [1, 2])


@pytest.mark.asyncio
async def test_delete_key(storage: Storage):
    await storage.set_value("key_to_delete", "value_to_delete")
    await storage.delete_key("key_to_delete")
    assert await storage.get_value("key_to_delete") is None


@pytest.mark.asyncio
async def test_get_w_scan(storage: Storage):
    await storage.set_value("test_key1", "value1")
    await storage.set_value("test_key2", "value2")
    await storage.set_value("another_key", "value3")
    matches = await storage.get_w_scan("test_key*")
    assert set(matches) == {"test_key1", "test_key2"}
    matches_all = await storage.get_w_scan("*")
    assert set(matches_all) == {"test_key1", "test_key2", "another_key"}
    matches_none = await storage.get_w_scan("none")
    assert len(matches_none) == 0
