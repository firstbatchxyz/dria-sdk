import json
from collections import defaultdict
from typing import Dict, List, Tuple

from Crypto.Hash import keccak

from dria.constants import (
    HEARTBEAT_OUTPUT_TOPIC,
    MAX_OLLAMA_QUEUE,
    MAX_API_QUEUE,
)
from dria.db.mq import KeyValueQueue
from dria.db.storage import Storage
from dria.models import NodeModel
from dria.request import RPCClient
from dria.utils import (
    recover_public_key,
    base64_to_json,
    uncompressed_public_key,
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
            raise e

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
            nodes_by_model, peer_id_map = self._decrypt_nodes(topic_responses)

            model_counts: Dict[str, int] = {}
            for model, addresses in nodes_by_model.items():
                unique_addresses = list(set(addresses))
                await self.task_manager.add_available_nodes(
                    NodeModel(uuid="", nodes=unique_addresses), model
                )
                model_counts[model] = len(unique_addresses)

            await self.task_manager.add_peer_ids(peer_id_map)

            return True

        except Exception as e:
            raise e

    @staticmethod
    def _decrypt_nodes(
        node_responses: List[str],
    ) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """
        Decrypt node responses to extract addresses.

        Args:
            node_responses: List of encrypted node response strings

        Returns:
            A tuple containing:
              - A dictionary mapping model names/IDs to lists of node addresses.
              - A dictionary mapping addresses to peer IDs.
        """
        node_addresses: Dict[str, List[str]] = defaultdict(list)
        peer_id_map: Dict[str, str] = {}

        for response in node_responses:
            try:
                metadata = json.loads(response)
                signature = metadata.get("signature")
                peer_id = metadata.get("peer_id")
                payload_str = metadata.get("message")
                recovery_id = metadata.get("recovery_id")
                if None in (signature, peer_id, payload_str, recovery_id):
                    logger.error("Incomplete metadata in node response: %s", metadata)
                    continue

                # Construct full signature bytes
                byte_sig = bytes.fromhex(signature)
                try:
                    recovery_bytes = int(recovery_id).to_bytes(1, byteorder="big")
                except Exception as ex:
                    logger.error(
                        "Invalid recovery_id format: %s", recovery_id, exc_info=True
                    )
                    continue
                full_signature = byte_sig + recovery_bytes

                public_key = recover_public_key(full_signature, payload_str.encode())
                public_key = uncompressed_public_key(public_key)

                # Generate Keccak hash to obtain node address
                address_hasher = keccak.new(digest_bits=256)
                address_hasher.update(public_key[1:])
                address = address_hasher.digest()[-20:].hex()
                peer_id_map[address] = peer_id

                # Decode payload and extract models and pending_tasks
                decoded_payload = base64_to_json(payload_str)
                payload = json.loads(decoded_payload)
                models = payload.get("models")
                if not models or "pending_tasks" not in payload:
                    continue

                for model_id, model_name in models:
                    max_queue = (
                        MAX_OLLAMA_QUEUE if model_id == "ollama" else MAX_API_QUEUE
                    )
                    if payload["pending_tasks"][0] > max_queue:
                        continue
                    node_addresses[model_name].append(address)
                    node_addresses[model_id].append(address)

            except Exception as exc:
                logger.error("Failed to decrypt node response: %s", exc, exc_info=True)
                continue

        deduped_addresses = {
            model: list(set(addresses)) for model, addresses in node_addresses.items()
        }
        return deduped_addresses, peer_id_map
