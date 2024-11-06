import json
from collections import defaultdict
from typing import Dict, List

from Crypto.Hash import keccak

from dria.constants import (
    HEARTBEAT_OUTPUT_TOPIC,
    HEARTBEAT_TOPIC,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import NodeModel
from dria.request import RPCClient
from dria.utils import (
    recover_public_key,
    base64_to_json,
    uncompressed_public_key,
    str_to_base64,
)
from dria.utils.logging import logger
from dria.utils.task_utils import TaskManager


class Monitor:
    """
    Monitor class that handles node network monitoring and heartbeat functionality.

    Responsible for:
    - Sending periodic heartbeats to check node availability
    - Processing heartbeat responses to track active nodes
    - Maintaining node address mappings by model type
    - Updating task manager with available nodes
    """

    def __init__(self, storage: Storage, rpc: RPCClient, kv: KeyValueQueue):
        """
        Initialize Monitor.

        Args:
            storage: Storage instance for persisting data
            rpc: RPCClient for network communication
            kv: KeyValueQueue for message queuing
        """
        self.task_manager = TaskManager(storage, rpc, kv)
        self.rpc = rpc

    async def run(self) -> None:
        """
        Run the monitor process continuously.

        Sends heartbeats and processes responses at regular intervals.
        Handles errors gracefully and maintains monitoring loop.
        """
        try:
            await self._check_heartbeat()
        except Exception as e:
            logger.error(f"Error during heartbeat process: {e}", exc_info=True)
            raise

    async def _send_heartbeat(self, payload: str) -> bool:
        """
        Send a heartbeat message to the network.

        Args:
            payload: Heartbeat message payload

        Returns:
            bool: True if heartbeat sent successfully, False otherwise
        """
        if not self.rpc:
            logger.warning("RPC client not initialized, skipping heartbeat")
            return False

        status = await self.rpc.push_content_topic(
            str_to_base64(payload), HEARTBEAT_TOPIC
        )
        if not status:
            logger.error(f"Failed to send heartbeat: {payload}")
            return False

        return True

    async def _check_heartbeat(self) -> bool:
        """
        Check for and process heartbeat responses.

        Retrieves responses from heartbeat topic, decrypts node information,
        and updates task manager with available nodes.

        Returns:
            bool: True if responses processed successfully, False otherwise
        """
        if not self.rpc or not self.task_manager:
            logger.warning("Required components not initialized")
            return False

        topic_responses = await self.rpc.get_content_topic(HEARTBEAT_OUTPUT_TOPIC)
        if not topic_responses:
            return False

        try:
            nodes_by_model = self._decrypt_nodes(
                [base64_to_json(response) for response in topic_responses]
            )

            model_counts: Dict[str, int] = {}
            for model, addresses in nodes_by_model.items():
                unique_addresses = list(set(addresses))
                await self.task_manager.add_available_nodes(
                    NodeModel(uuid="", nodes=unique_addresses), model
                )
                model_counts[model] = len(unique_addresses)

            return True

        except Exception as e:
            logger.error(f"Failed to process heartbeat responses: {e}", exc_info=True)
            return False

    @staticmethod
    def _decrypt_nodes(node_responses: List[str]) -> Dict[str, List[str]]:
        """
        Decrypt node responses to extract addresses.

        Args:
            node_responses: List of encrypted node response strings

        Returns:
            Dict mapping model names/IDs to lists of node addresses
        """
        node_addresses: Dict[str, List[str]] = defaultdict(list)

        for response in node_responses:
            try:
                signature, metadata_json = response[:130], response[130:]
                metadata = json.loads(metadata_json)

                public_key = recover_public_key(
                    bytes.fromhex(signature), metadata_json.encode()
                )
                public_key = uncompressed_public_key(public_key)

                # Generate Keccak hash of public key to get address
                address = (
                    keccak.new(digest_bits=256)
                    .update(public_key[1:])
                    .digest()[-20:]
                    .hex()
                )

                # Map address to both model ID and name
                for model_id, model_name in metadata["models"]:
                    node_addresses[model_name].append(address)
                    node_addresses[model_id].append(address)

            except Exception as e:
                logger.error(f"Failed to decrypt node response: {e}", exc_info=True)
                continue

        return {
            model: list(set(addresses)) for model, addresses in node_addresses.items()
        }
