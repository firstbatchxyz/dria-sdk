from typing import List, Union, Optional

import aiohttp
import asyncio

from dria import constants
from dria.models.exceptions import (
    RPCContentTopicError,
    RPCConnectionError,
    RPCAuthenticationError,
)
from dria.utils.logging import logger


class RPCClient:
    """
    RPCClient for Libp2p RPC for Dria Network

    Args:
        auth_token (str): The authentication token for the RPC client.
    """

    NETWORK_MAX_MESSAGE_SIZE = 256
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, auth_token: Optional[str] = None):
        if not auth_token:
            raise ValueError(
                "RPC token is required for Dria RPC. "
                "Please set the DRIA_RPC_TOKEN environment variable."
            )
        if auth_token.startswith("sk-dria-v1-"):
            self.base_url = constants.RPC_BASE_URL
        else:
            self.base_url = constants.RPC_BASE_URL_COMMUNITY
        self.auth_token = auth_token
        self.headers = {
            "x-api-key": self.auth_token,
            "Accept": "application/json",
        }

    async def health_check(self) -> bool:
        """
        Perform a health check on the node.

        :return: True if the node is healthy, False otherwise.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(f"{self.base_url}/health") as response:
                        status = response.status
                        return status == 200
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise RPCConnectionError(f"Health check failed: {str(e)}")
                await asyncio.sleep(self.RETRY_DELAY)

    async def get_content_topic(self, content_topic: str) -> List[str]:
        """
        Get content topic.

        :param content_topic: The content topic to get.
        :return: Messages from the content topic.
        :raises RPCContentTopicError: If there is an error fetching content from the topic.
        :raises RPCAuthenticationError: If there is an authentication error.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(
                        f"{self.base_url}/rpc/{content_topic}"
                    ) as response:
                        if response.status == 401:
                            raise RPCAuthenticationError()

                        res_json = await response.json()
                        return res_json["data"]["results"]
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    raise RPCAuthenticationError()
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Failed to get content topic {content_topic}: {e}")
                    raise RPCContentTopicError(str(e), content_topic)
                await asyncio.sleep(self.RETRY_DELAY)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise RPCConnectionError(f"{str(e)}")
                await asyncio.sleep(self.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to get content topic {content_topic}: {e}")
                raise

    async def push_content_topic(
        self, data: Union[str, bytes], content_topic: str
    ) -> bool:
        """
        Push content to a topic.

        :param data: The data to push.
        :param content_topic: The content topic to push to.
        :return: True if successful, False otherwise.
        :raises RPCContentTopicError: If there is an error pushing content to the topic.
        :raises RPCAuthenticationError: If there is an authentication error.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        data_size = len(data) if isinstance(data, bytes) else len(data.encode("utf-8"))
        if data_size > self.NETWORK_MAX_MESSAGE_SIZE * 1024:
            raise ValueError(
                f"Data size ({data_size} bytes) exceeds the maximum allowed size of {self.NETWORK_MAX_MESSAGE_SIZE} bytes"
            )
        for attempt in range(self.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.post(
                        f"{self.base_url}/rpc/{content_topic}",
                        json={"value": {"payload": data}},
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        if response.status == 401:
                            raise RPCAuthenticationError()
                        return True
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    raise RPCAuthenticationError()
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Failed to push content topic {content_topic}: {e}")
                    raise RPCContentTopicError(
                        "Failed to push content topic", content_topic
                    )
                await asyncio.sleep(self.RETRY_DELAY)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise RPCConnectionError(f"Connection error: {str(e)}")
                await asyncio.sleep(self.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to push content topic {content_topic}: {e}")
                raise e
