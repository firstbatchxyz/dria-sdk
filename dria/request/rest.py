from typing import List, Union

import aiohttp

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

    NETWORK_MAX_MESSAGE_SIZE = 128

    def __init__(self, auth_token: str):
        if not auth_token:
            raise ValueError(
                "RPC token is required for Dria RPC. "
                "Please set the DRIA_RPC_TOKEN environment variable."
            )
        self.base_url = constants.RPC_BASE_URL
        self.auth_token = auth_token
        self.headers = {
            "x-api-key": self.auth_token,
            "Accept": "application/json",
        }
        self.session = None
        self.connector = None

    async def initialize(self):
        if self.session is None:
            self.connector = aiohttp.TCPConnector(force_close=True)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                connector=self.connector,
            )
        return self

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
        if self.connector:
            await self.connector.close()
            self.connector = None

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def health_check(self) -> bool:
        """
        Perform a health check on the node.

        :return: True if the node is healthy, False otherwise.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                text = await response.text()
                return text == "Node is healthy"
        except aiohttp.ClientError as e:
            raise RPCConnectionError(f"Health check failed: {str(e)}")

    async def get_content_topic(self, content_topic: str) -> List[str]:
        """
        Get content topic.

        :param content_topic: The content topic to get.
        :return: Messages from the content topic.
        :raises RPCContentTopicError: If there is an error fetching content from the topic.
        :raises RPCAuthenticationError: If there is an authentication error.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        try:
            async with self.session.get(
                f"{self.base_url}/rpc/{content_topic}"
            ) as response:
                if response.status == 401:
                    raise RPCAuthenticationError()

                res_json = await response.json()
                return res_json["data"]["results"]
        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise RPCAuthenticationError()
            logger.error(f"Failed to get content topic {content_topic}: {e}")
            raise RPCContentTopicError("Failed to get content topic", content_topic)
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get content topic {content_topic}: {e}")
            raise RPCConnectionError(f"Connection error: {str(e)}")
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
        try:
            logger.debug("Pushing content to topic: %s", content_topic)
            async with self.session.post(
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
            logger.error(f"Failed to push content topic {content_topic}: {e}")
            raise RPCContentTopicError("Failed to push content topic", content_topic)
        except aiohttp.ClientError as e:
            raise RPCConnectionError(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to push content topic {content_topic}: {e}")
            raise e
