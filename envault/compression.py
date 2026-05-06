"""Optional compression for vault payloads to reduce storage size."""

import zlib
import base64
import json
from typing import Dict, Any

COMPRESSION_MARKER = "__compressed__"


def compress_payload(data: Dict[str, Any]) -> str:
    """Serialize and compress a dict payload to a base64-encoded string."""
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw, level=zlib.Z_BEST_COMPRESSION)
    return base64.b64encode(compressed).decode("ascii")


def decompress_payload(blob: str) -> Dict[str, Any]:
    """Decompress a base64-encoded compressed payload back to a dict."""
    compressed = base64.b64decode(blob.encode("ascii"))
    raw = zlib.decompress(compressed)
    return json.loads(raw.decode("utf-8"))


def is_compressed(value: Any) -> bool:
    """Return True if the value looks like a compressed blob marker dict."""
    return (
        isinstance(value, dict)
        and value.get("type") == COMPRESSION_MARKER
    )


def wrap_compressed(blob: str) -> Dict[str, str]:
    """Wrap a compressed blob in a marker dict for storage in vault secrets."""
    return {"type": COMPRESSION_MARKER, "data": blob}


def unwrap_compressed(value: Dict[str, str]) -> str:
    """Extract the raw compressed blob from a marker dict."""
    if not is_compressed(value):
        raise ValueError("Value is not a compressed payload marker.")
    return value["data"]


def compress_secrets(secrets: Dict[str, Any]) -> Dict[str, Any]:
    """Compress each secret value that is a non-trivial dict payload.

    Plain string values are left as-is; dict values (e.g. tagged or
    expiry-annotated secrets) are compressed to reduce vault file size.
    """
    result: Dict[str, Any] = {}
    for key, value in secrets.items():
        if isinstance(value, dict) and not is_compressed(value):
            blob = compress_payload(value)
            result[key] = wrap_compressed(blob)
        else:
            result[key] = value
    return result


def decompress_secrets(secrets: Dict[str, Any]) -> Dict[str, Any]:
    """Decompress any compressed secret values back to their original dicts."""
    result: Dict[str, Any] = {}
    for key, value in secrets.items():
        if is_compressed(value):
            blob = unwrap_compressed(value)
            result[key] = decompress_payload(blob)
        else:
            result[key] = value
    return result
