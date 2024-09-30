import base64


def base64_to_json(data):
    """
    Decode base64 encoded data to a UTF-8 string.

    :param data: Base64 encoded string
    :return: Decoded UTF-8 string
    """
    return base64.b64decode(data).decode("utf-8")


def str_to_base64(data):
    """
    Encode a UTF-8 string to base64.

    :param data: UTF-8 encoded string
    :return: Base64 encoded string
    """
    return base64.b64encode(data.encode("utf-8")).decode("utf-8")
