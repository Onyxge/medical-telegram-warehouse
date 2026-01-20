import subprocess
import sys
import os
import json
from dagster import asset, Output, AssetExecutionContext
from pathlib import Path

# 1. Define the Root Directory
ROOT_DIR = Path(__file__).parent.parent

# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------
# FIX: Change this to the exact name of the file your scraper produces!
SCRAPED_FILE_PATH = ROOT_DIR / "telegram_data.json"


# ---------------------------------------------------
# ASSET 1: SCRAPER
# ---------------------------------------------------
@asset(group_name="ingestion")
def raw_telegram_data(context: AssetExecutionContext):
    """
    Runs scripts/telegram_scraper.py
    """
    script_path = ROOT_DIR / "scripts" / "telegram_scraper.py"
    context.log.info(f"Running scraper at: {script_path}")

    if not script_path.exists():
        raise Exception(f"❌ Script not found at: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
    )

    if result.stdout:
        context.log.info(f"Scraper Output: {result.stdout}")
    if result.stderr:
        context.log.warning(f"Scraper Logs: {result.stderr}")

    if result.returncode != 0:
        raise Exception(f"Scraper failed with code {result.returncode}")

    return Output(
        value="Scraping Finished",
        metadata={"status": "Success"}
    )


# ---------------------------------------------------
# ASSET 2: LOADER (With "New Data" Check)
# ---------------------------------------------------
@asset(group_name="ingestion", deps=[raw_telegram_data])
def raw_database_tables(context: AssetExecutionContext):
    """
    Runs scripts/load_raw_telegram_messages.py ONLY if there is new data.
    """
    # 1. CHECK: Does the data file exist?
    if not SCRAPED_FILE_PATH.exists():
        context.log.warning(f"⚠️ Data file not found at {SCRAPED_FILE_PATH}. Skipping Load.")
        return Output("Skipped", metadata={"status": "No File"})

    # 2. CHECK: Is the data file empty?
    try:
        with open(SCRAPED_FILE_PATH, 'r') as f:
            data = json.load(f)

        if not data or len(data) == 0:
            context.log.info("ℹ️ Scraper returned 0 items. Skipping Loader to prevent duplicates.")
            return Output("Skipped", metadata={"status": "No New Data", "items": 0})

        context.log.info(f"✅ Found {len(data)} items. Proceeding to Load...")

    except json.JSONDecodeError:
        context.log.error("❌ Failed to parse JSON. File might be corrupted.")
        raise

    # 3. RUN: The Loader Script
    script_path = ROOT_DIR / "scripts" / "load_raw_telegram_messages.py"

    if not script_path.exists():
        raise Exception(f"❌ Loader script not found at: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
    )

    if result.stdout:
        context.log.info(f"Loader Output: {result.stdout}")
    if result.stderr:
        context.log.warning(f"Loader Logs: {result.stderr}")

    if result.returncode != 0:
        raise Exception("Loader script failed!")

    return Output("Data Loaded", metadata={"table": "raw.telegram_messages", "items_loaded": len(data)})


# ---------------------------------------------------
# ASSET 3: YOLO
# ---------------------------------------------------
@asset(group_name="ingestion", deps=[raw_telegram_data])
def object_detection_results(context: AssetExecutionContext):
    """
    Runs src/yolo_detect.py
    """
    script_path = ROOT_DIR / "src" / "yolo_detect.py"

    if not script_path.exists():
        raise Exception(f"❌ Script not found at: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR)
    )

    if result.stdout:
        context.log.info(f"YOLO Output: {result.stdout}")
    if result.stderr:
        context.log.warning(f"YOLO Logs: {result.stderr}")

    if result.returncode != 0:
        raise Exception("YOLO script failed!")

    return Output("YOLO Detections Completed", metadata={"table": "raw.yolo_detections"})