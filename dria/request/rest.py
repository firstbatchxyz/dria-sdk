from typing import List, Union

import httpx

from dria import constants
from dria.models.exceptions import RPCContentTopicError, RPCConnectionError, RPCAuthenticationError
from dria.utils.logging import logger


class RPCClient:
    """
    RPCClient for Libp2p RPC for Dria Network

    Args:
        auth_token (str): The authentication token for the RPC client.

    """

    def __init__(self, auth_token: str):
        if not auth_token:
            raise ValueError("RPC token is required for Dria RPC."
                             "Please set the DRIA_RPC_TOKEN environment variable.")
        self.base_url = constants.RPC_BASE_URL
        self.auth_token = auth_token

    async def health_check(self) -> bool:
        """
        Perform a health check on the node.

        :return: True if the node is healthy, False otherwise.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        try:
            async with httpx.AsyncClient(
                    headers={"x-api-key": self.auth_token, "Accept": "application/json"}) as client:
                response = await client.get(f"{self.base_url}/health")
                text = response.text
            return text == "Node is healthy"
        except httpx.RequestError as e:
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
            async with httpx.AsyncClient(
                    headers={"x-api-key": self.auth_token, "Accept": "application/json"}) as client:
                response = await client.get(f"{self.base_url}/rpc/{content_topic}")

                if response.status_code == 401:
                    raise RPCAuthenticationError()

                response.raise_for_status()
                res_json = response.json()
            return res_json["data"]["results"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RPCAuthenticationError()
            logger.error(f"Failed to get content topic {content_topic}: {e}")
            raise RPCContentTopicError(f"Failed to get content topic", content_topic)
        except httpx.RequestError as e:
            logger.error(f"Failed to get content topic {content_topic}: {e}")
            return []

    async def push_content_topic(self, data: Union[str, bytes], content_topic: str) -> bool:
        """
        Push content to a topic.

        :param data: The data to push.
        :param content_topic: The content topic to push to.
        :return: A success message.
        :raises RPCContentTopicError: If there is an error pushing content to the topic.
        :raises RPCAuthenticationError: If there is an authentication error.
        :raises RPCConnectionError: If there is a connection error with the RPC server.
        """
        try:
            logger.debug("Pushing content to topic: %s", content_topic)
            async with httpx.AsyncClient(
                    headers={"x-api-key": self.auth_token, "Accept": "application/json"}) as client:
                response = await client.post(
                    f"{self.base_url}/rpc/{content_topic}",
                    json={"value": {
                        "payload": data,
                    }},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 401:
                    raise RPCAuthenticationError()

                response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RPCAuthenticationError()
            logger.error(f"Failed to push content topic {content_topic}: {e}")
            raise RPCContentTopicError(f"Failed to push content topic", content_topic)
        except httpx.RequestError as e:
            raise RPCConnectionError(f"Connection error: {str(e)}")
