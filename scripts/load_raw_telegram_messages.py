import os
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch

load_dotenv()

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

DATA_LAKE_BASE = Path("data/raw/telegram/messages")

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "dbname": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

INSERT_SQL = """
INSERT INTO raw.telegram_messages (
    message_id,
    channel_name,
    channel_title,
    message_date,
    message_text,
    has_media,
    image_path,
    views,
    forwards
)
VALUES (
    %(message_id)s,
    %(channel_name)s,
    %(channel_title)s,
    %(message_date)s,
    %(message_text)s,
    %(has_media)s,
    %(image_path)s,
    %(views)s,
    %(forwards)s
)
ON CONFLICT (message_id, channel_name) DO NOTHING;
"""

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def get_all_json_files(base_path: Path) -> List[Path]:
    """Recursively find all JSON files under channel folders."""
    return list(base_path.glob("**/channel=*/**/*.json"))


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON messages from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_messages(messages: List[Dict]) -> List[Dict]:
    """Normalize messages and skip incomplete ones."""
    records = []

    for msg in messages:
        if not msg.get("message_id") or not msg.get("message_date"):
            continue

        records.append({
            "message_id": msg["message_id"],
            "channel_name": msg["channel_name"],
            "channel_title": msg.get("channel_title"),
            "message_date": msg["message_date"],
            "message_text": msg.get("message_text", ""),
            "has_media": msg.get("has_media", False),
            "image_path": msg.get("image_path"),
            "views": msg.get("views", 0),
            "forwards": msg.get("forwards", 0),
        })

    return records


def filter_existing_records(records: List[Dict], conn) -> List[Dict]:
    """Remove messages that already exist in the database."""
    if not records:
        return []

    message_ids = [r["message_id"] for r in records]
    channel_names = [r["channel_name"] for r in records]

    with conn.cursor() as cur:
        # Use WHERE (message_id, channel_name) IN (...) to filter existing messages
        cur.execute(
            """
            SELECT message_id, channel_name
            FROM raw.telegram_messages
            WHERE (message_id, channel_name) IN %s
            """,
            (tuple(zip(message_ids, channel_names)),)
        )
        existing = {(row[0], row[1]) for row in cur.fetchall()}

    # Return only records that are not in existing
    new_records = [
        r for r in records if (r["message_id"], r["channel_name"]) not in existing
    ]
    return new_records


# -----------------------------------------------------------------------------
# MAIN LOAD
# -----------------------------------------------------------------------------

def load_to_postgres(records: List[Dict]) -> None:
    if not records:
        print("No new records to load.")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        new_records = filter_existing_records(records, conn)
        if not new_records:
            print("All messages already loaded, skipping insert.")
            return

        with conn:
            with conn.cursor() as cur:
                execute_batch(cur, INSERT_SQL, new_records, page_size=500)
        print(f"Loaded {len(new_records)} new records into raw.telegram_messages")
    finally:
        conn.close()


def main() -> None:
    all_files = get_all_json_files(DATA_LAKE_BASE)
    print(f"Found {len(all_files)} JSON files")

    all_records: List[Dict] = []

    for file in all_files:
        messages = load_json(file)
        records = flatten_messages(messages)
        all_records.extend(records)

    load_to_postgres(all_records)


if __name__ == "__main__":
    main()
