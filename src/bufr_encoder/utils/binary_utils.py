"""Binary data utilities."""


def to_bytes(data):
    if isinstance(data, str):
        return data.encode('utf-8')
    return bytes(data)
