import asyncio
import json
from collections import defaultdict
from typing import List, Dict

from Crypto.Hash import keccak

from dria.constants import *
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
    Monitor class to handle the monitoring of the node network.
    """

    def __init__(self, storage: Storage, rpc: RPCClient, kv: KeyValueQueue):
        self.task_manager = TaskManager(storage, rpc, kv)
        self.rpc = rpc

    async def run(self):
        """
        Periodically sends a heartbeat to the node network and checks for responses.
        """
        while True:
            try:
                await self._check_heartbeat()
                await asyncio.sleep(MONITORING_INTERVAL)
            except Exception as e:
                logger.error(f"Error during heartbeat process: {e}")
                await asyncio.sleep(MONITORING_INTERVAL)
                raise Exception(e)

    async def _send_heartbeat(self, payload: str) -> bool:
        """
        Sends a heartbeat message to the network.

        Args:
            payload (str): The heartbeat payload.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.rpc:
            logger.warning("RPC client not initialized, skipping heartbeat sending.")
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
        Checks for a response to a previously sent heartbeat.


        Returns:
            bool: True if a response is received, False otherwise.
        """
        if not self.rpc or not self.task_manager:
            logger.warning(
                "RPC client or Task Manager not initialized, skipping heartbeat checking."
            )
            return False

        topic = await self.rpc.get_content_topic(HEARTBEAT_OUTPUT_TOPIC)
        if topic:
            try:
                nodes_as_address = self._decrypt_nodes(
                    [base64_to_json(t) for t in topic]
                )
                logger.debug(f"Current nodes: {nodes_as_address}")

                model_d = {}
                for model, addresses in nodes_as_address.items():
                    addresses = list(set(addresses))
                    self.task_manager.add_available_nodes(
                        NodeModel(uuid="", nodes=addresses), model
                    )
                    model_d[model] = model_d.get(model, 0) + len(addresses)

                return True
            except Exception as e:
                logger.error(f"Error processing heartbeat response: {e}", exc_info=True)

        return False

    @staticmethod
    def _decrypt_nodes(available_nodes: List[str]) -> Dict[str, List[str]]:
        """
        Decrypts the available nodes to get the address.

        Args:
            available_nodes (List[str]): Encrypted node identifiers.

        Returns:
            Dict[str, List[str]]: Mapping of models to lists of decrypted node addresses.
        """
        node_addresses = defaultdict(list)

        for node in available_nodes:
            try:
                signature, metadata_json = node[:130], node[130:]
                metadata = json.loads(metadata_json)

                public_key = recover_public_key(
                    bytes.fromhex(signature), metadata_json.encode()
                )
                public_key = uncompressed_public_key(public_key)
                address = (
                    keccak.new(digest_bits=256)
                    .update(public_key[1:])
                    .digest()[-20:]
                    .hex()
                )
                for model_id, model_name in metadata["models"]:
                    node_addresses[model_name].append(address)
                    node_addresses[model_id].append(address)

            except Exception as e:
                logger.error(f"Failed to decrypt node: {e}", exc_info=True)

        for i, v in node_addresses.items():
            node_addresses[i] = list(set(v))

        return dict(node_addresses)
