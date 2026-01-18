import os
import glob
import cv2
import pandas as pd
from ultralytics import YOLO
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine

# -----------------------------------------------------------------------------
# ENVIRONMENT
# -----------------------------------------------------------------------------

load_dotenv()

IMAGE_DIR = "data/raw/images"
OUTPUT_DIR = "data/processed/annotated_images"  # <--- NEW: Folder for results

DB_STR = (
    f"postgresql://{os.getenv('PG_USER')}:"
    f"{os.getenv('PG_PASSWORD')}@"
    f"{os.getenv('PG_HOST')}:"
    f"{os.getenv('PG_PORT')}/"
    f"{os.getenv('PG_DB')}"
)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# MODEL
# -----------------------------------------------------------------------------

# YOLOv8 nano for lightweight local inference
model = YOLO("yolov8n.pt")

# COCO classes loosely representing physical products
PRODUCT_CLASSES = [
    "bottle",
    "cup",
    "bowl",
    "vase",
    "other"
]

# -----------------------------------------------------------------------------
# BUSINESS LOGIC
# -----------------------------------------------------------------------------

def classify_image(detections: list[dict]) -> str:
    """
    Classify image based on detected objects.
    """
    labels = [d["label"] for d in detections]

    has_person = "person" in labels
    has_product = any(label in PRODUCT_CLASSES for label in labels)

    if has_person and has_product:
        return "promotional"
    if has_product and not has_person:
        return "product_display"
    if has_person and not has_product:
        return "lifestyle"
    return "other"


# -----------------------------------------------------------------------------
# IMAGE PROCESSING
# -----------------------------------------------------------------------------

def process_images() -> pd.DataFrame:
    """
    Scan directory, run YOLO, SAVE IMAGES, and return DataFrame.
    """
    image_paths = glob.glob(
        os.path.join(IMAGE_DIR, "**", "*.jpg"),
        recursive=True
    )

    logger.info(f"Found {len(image_paths)} images to process")

    rows = []

    for img_path in image_paths:
        try:
            filename = os.path.basename(img_path)
            message_id = filename.replace(".jpg", "")
            channel_name = os.path.basename(os.path.dirname(img_path))

            # Run Inference
            results = model(img_path, verbose=False)[0]

            # --- NEW: VISUALIZATION STEP ---
            # Plot the results (draws boxes on the image)
            annotated_frame = results.plot()

            # Save the image to the new folder
            # Structure: data/processed/annotated_images/channel_name_message_id.jpg
            output_filename = f"{channel_name}_{filename}"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            cv2.imwrite(output_path, annotated_frame)
            # -------------------------------

            detections = []
            confidences = []

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                conf = float(box.conf[0])

                detections.append({
                    "label": label,
                    "confidence": conf,
                })
                confidences.append(conf)

            image_category = classify_image(detections)
            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )

            rows.append({
                "message_id": int(message_id) if message_id.isdigit() else None,
                "channel_name": channel_name,
                "image_path": img_path,
                "detected_objects": [d["label"] for d in detections],
                "image_category": image_category,
                "confidence_score": round(avg_confidence, 3),
            })

        except Exception as exc:
            logger.error(f"Failed processing {img_path}: {exc}")

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting YOLO object detection")

    df = process_images()

    if df.empty:
        logger.warning("No images processed. Exiting.")
        exit(0)

    # Backup CSV
    csv_path = "data/yolo_detections.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"CSV backup written to {csv_path}")

    # Load to PostgreSQL raw schema
    engine = create_engine(DB_STR)
    df.to_sql(
        name="yolo_detections",
        con=engine,
        schema="raw",
        if_exists="append",  # Changed to replace to avoid duplicates during testing
        index=False,
    )

    logger.success(
        f"Loaded {len(df)} rows into raw.yolo_detections"
    )
    logger.success(f"Visual results saved to {OUTPUT_DIR}")