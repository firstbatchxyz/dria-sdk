from typing import Tuple, List, Dict

import coincurve
from Crypto.Hash import keccak
from ecies import decrypt
from ecies.utils import generate_eth_key

from dria.models import Task
from dria.utils.logging import logger


def uncompressed_public_key(public_key: str) -> bytes:
    """
    Convert a compressed public key to an uncompressed public key.

    :param public_key: The compressed public key as a hexadecimal string.
    :return: The uncompressed public key as bytes.

    Raises:
        ValueError: If the provided public key is invalid.
    """
    try:
        public_key_bytes = bytes.fromhex(public_key)
        public_key = coincurve.PublicKey(public_key_bytes)
        return public_key.format(compressed=False)
    except Exception as e:
        logger.error(f"Error converting public key: {e}", exc_info=True)
        raise ValueError(f"Failed to convert public key: {e}") from e


def generate_task_keys() -> Tuple[str, str]:
    """
    Generate an elliptic curve key pair.

    Returns:
        Tuple[str, str]: The private and public keys as hexadecimal strings.
    """
    try:
        eth_k = generate_eth_key()
        return eth_k.to_hex(), eth_k.public_key.to_hex()
    except Exception as e:
        logger.error(f"Error generating task keys: {e}", exc_info=True)
        raise e


def recover_public_key(signature: bytes, message_digest: bytes) -> str:
    """
    Recovers the public key from a signature and message.

    Args:
        signature (bytes): The signature from which to recover the public key. Must be exactly 65 bytes long.
        message_digest (bytes): Hash of the message that was signed.

    Returns:
        str: The recovered public key as a hexadecimal string, compressed.

    Raises:
        ValueError: If the signature is not 65 bytes long or other cryptographic errors occur.
    """
    try:
        if len(signature) != 65:
            raise ValueError("Signature must be exactly 65 bytes long")
        pk = coincurve.PublicKey.from_signature_and_message(signature, message_digest)
        return pk.format(compressed=True).hex()
    except Exception as e:
        logger.error(f"Error recovering public key: {e}", exc_info=True)
        raise ValueError(f"Failed to recover public key: {e}") from e


def decrypt_message(private_key: str, encrypted_message: bytes) -> str:
    """
    Decrypt an encrypted message using the provided private key.

    Args:
        private_key (str): The private key to use for decryption.
        encrypted_message (bytes): The encrypted message to decrypt.

    Returns:
        str: The decrypted message.

    Raises:
        ValueError: If the private key is invalid or other cryptographic errors occur.
    """
    try:
        private_key_bytes = bytes.fromhex(private_key)
        decrypted_message = decrypt(private_key_bytes, encrypted_message)
        return decrypted_message.decode("utf-8")
    except Exception as e:
        logger.error(f"Error decrypting message: {e}", exc_info=True)
        raise ValueError(f"Failed to decrypt message: {e}") from e


def publickey_to_address(public_key: bytes) -> str:
    """
    Convert a public key to an Ethereum address.

    Args:
        public_key (bytes): The public key to convert.

    Returns:
        str: The Ethereum address.

    Raises:
        ValueError: If the public key is invalid.
    """
    try:
        k = keccak.new(digest_bits=256)
        k.update(public_key[1:])
        return k.digest()[-20:].hex()  # Can be 40
    except Exception as e:
        logger.error(f"Error converting public key to address: {e}", exc_info=True)
        raise ValueError(f"Failed to convert public key to address: {e}") from e


def get_truthful_nodes(task: Task, topic_result: Dict) -> tuple[str, str]:
    """
    Get truthful nodes from topic results.

    Args:
        task (Task): Task data
        topic_result (Dict): Topic result

    Returns:
        Tuple[List[Dict], List[str]]: List of truthful nodes and results
    """
    if isinstance(topic_result["ciphertext"], str):
        topic_result["ciphertext"] = bytes.fromhex(topic_result["ciphertext"])
    result = decrypt_message(task.private_key[2:], topic_result["ciphertext"])
    public_key = recover_public_key(bytes.fromhex(topic_result["signature"]), (task.id + result).encode())
    public_key = uncompressed_public_key(public_key)
    address = publickey_to_address(public_key)
    return result, address
