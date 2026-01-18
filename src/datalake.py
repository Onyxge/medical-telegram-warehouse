import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SOURCE = "telegram"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sanitize_channel(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def telegram_messages_partition_dir(base_path: str, date_str: str, channel_name: str) -> str:
    channel = sanitize_channel(channel_name)
    path = os.path.join(
        base_path,
        "raw",
        SOURCE,
        "messages",
        f"ingestion_date={date_str}",
        f"channel={channel}",
    )
    ensure_dir(path)
    return path


def telegram_images_dir(base_path: str, channel_name: str) -> str:
    channel = sanitize_channel(channel_name)
    path = os.path.join(
        base_path,
        "raw",
        SOURCE,
        "media",
        f"channel={channel}",
    )
    ensure_dir(path)
    return path


def channel_messages_json_path(base_path: str, date_str: str, channel_name: str) -> str:
    partition_dir = telegram_messages_partition_dir(base_path, date_str, channel_name)
    return os.path.join(partition_dir, "messages.json")


def write_channel_messages_json(
    *,
    base_path: str,
    date_str: str,
    channel_name: str,
    messages: List[Dict[str, Any]],
) -> str:
    """
    Write raw Telegram messages for a single (date, channel) partition.

    This function overwrites the partition file by design.
    Raw data is treated as append-only at the partition level.
    """
    out_path = channel_messages_json_path(base_path, date_str, channel_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    return out_path


def manifest_path(base_path: str, date_str: str) -> str:
    path = os.path.join(
        base_path,
        "raw",
        SOURCE,
        "messages",
        f"ingestion_date={date_str}",
        "_manifest.json",
    )
    ensure_dir(os.path.dirname(path))
    return path


def write_manifest(
    *,
    base_path: str,
    date_str: str,
    channel_message_counts: Dict[str, int],
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Write audit metadata for a Telegram scrape run."""

    payload: Dict[str, Any] = {
        "source": SOURCE,
        "ingestion_date": date_str,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "channels": channel_message_counts,
        "total_messages": sum(channel_message_counts.values()),
    }

    if extra:
        payload.update(extra)

    out_path = manifest_path(base_path, date_str)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
