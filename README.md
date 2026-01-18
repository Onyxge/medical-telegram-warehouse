# Medical Telegram Analytics Platform

## Overview

This project implements an end-to-end data engineering and analytics platform for analyzing Telegram channels in the medical, pharmaceutical, and cosmetics domain.

The system ingests unstructured Telegram messages and images, stores them in a scalable data lake, transforms them into a clean, tested analytical warehouse using dbt, and enriches visual content using YOLO-based object detection.

The architecture follows modern lakehouse and dimensional modeling best practices, ensuring reliability, auditability, and extensibility.

---

## High-Level Architecture

```
Telegram API
     |
     v
Data Ingestion (Python, Telethon)
     |
     v
Raw Data Lake (JSON + Images)
     |
     v
PostgreSQL (raw schema)
     |
     v
dbt Transformations
(staging → marts)
     |
     v
Analytics-Ready Warehouse
     |
     v
YOLO Image Enrichment
```

---

## Repository Structure

```
medical-telegram-warehouse/
├── data/
│   └── raw/
│       ├── telegram/
│       │   └── messages/
│       │       └── ingestion_date=YYYY-MM-DD/
│       │           ├── channel=channel_name/
│       │           └── _manifest.json
│       └── images/
│           ├── channel_name/
│           │   └── message_id.jpg
│
├── src/
│   ├── datalake.py              # Data lake utilities
│   ├── telegram.py              # Telegram scraping logic
│   ├── raw_loader.py            # Load raw JSON into PostgreSQL
│   └── yolo_detection.py        # YOLO object detection pipeline
│
├── medical_warehouse/
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_telegram_messages.sql
│   │   ├── marts/
│   │   │   ├── dim_channels.sql
│   │   │   ├── dim_dates.sql
│   │   │   ├── fct_messages.sql
│   │   │   └── fct_image_detections.sql
│   │   └── schema.yml
│   └── dbt_project.yml
│
├── tests/
│   ├── assert_no_future_messages.sql
│   └── assert_positive_views.sql
│
├── logs/
│   └── telegram_scraper.log
│
├── requirements.txt
├── .env
└── README.md
```

---

## Task 1 – Data Ingestion & Data Lake

### Key Features

* Telegram scraping using Telethon
* Rate-limit safe execution
* Handles messages with and without media
* Idempotent ingestion
* Partitioned raw data lake design

### Data Lake Design

* Messages stored as raw JSON
* Partitioned by `ingestion_date` and `channel`
* Images stored separately using deterministic paths
* No premature schema enforcement

This design ensures:

* Reproducibility
* Backfill capability
* Full audit trail

---

## Task 2 – Data Modeling & Transformation (dbt)

### Modeling Approach

The warehouse follows a star schema optimized for analytics.

#### Fact Tables

* `fct_messages`: one row per Telegram message
* `fct_image_detections`: one row per image detection event

#### Dimension Tables

* `dim_channels`
* `dim_dates`

### Staging Layer

Staging models:

* Cast data types
* Rename columns consistently
* Filter invalid records
* Add derived fields such as `message_length` and `has_image`

### Data Quality Enforcement

Implemented using dbt:

* `not_null`
* `unique`
* `relationships`

Custom data tests:

* No future-dated messages
* Non-negative view counts

All tests pass successfully.

---

## Task 3 – Image Enrichment with YOLO

### Objective

Use computer vision to extract analytical signals from Telegram images.

### Implementation

* YOLOv8 nano model for efficiency
* Detects general objects using COCO classes

### Classification Logic

* `promotional`: person + product
* `product_display`: product only
* `lifestyle`: person only
* `other`: neither detected

### Outputs

* Annotated images saved locally
* Detection results stored in `raw.yolo_detections`
* Enriched analytics table: `fct_image_detections`

---

## Running the Pipeline

### 1. Set Environment Variables

Create a `.env` file:

```
PG_HOST=localhost
PG_PORT=5432
PG_DB=medical_telegram_warehouse
PG_USER=postgres
PG_PASSWORD=your_password
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Run Telegram Scraper

```
python src/telegram.py
```

### 4. Load Raw Data to PostgreSQL

```
python src/raw_loader.py
```

### 5. Run dbt Transformations

From inside `medical_warehouse/`:

```
dbt run
dbt test
```

### 6. Generate dbt Documentation

```
dbt docs generate
dbt docs serve
```

### 7. Run YOLO Image Detection

```
python src/yolo_detection.py
```

---

## Key Learnings

* Raw data should remain raw until transformation
* dbt provides strong guarantees around data trust
* Pre-trained vision models add value even without domain-specific training
* Clear separation of ingestion, transformation, and enrichment simplifies debugging

---

## Limitations & Future Work

### Current Limitations

**Computer Vision Domain Gap**
The YOLOv8 model used is a general-purpose object detector trained on COCO classes. As a result, it cannot reliably distinguish between medically relevant product types such as specific drugs, supplements, or cosmetics. Product presence is inferred indirectly through container-like objects rather than domain-aware labels.

**Image-Only Enrichment**
The current enrichment pipeline focuses exclusively on visual signals. Images containing embedded text (e.g., dosage instructions, promotional claims, or price lists) are not processed using OCR, which limits semantic understanding of visual content.

**Batch-Oriented Ingestion**
Telegram data ingestion is implemented as a batch process. This introduces latency between message publication and analytical availability, making the system less suitable for near-real-time monitoring or alerting use cases.

**Limited Advanced NLP**
While messages are ingested and modeled, no advanced natural language processing is currently applied. Sentiment, topic evolution, misinformation detection, and entity extraction are not yet implemented.

**Single-Source Scope**
The platform currently focuses only on Telegram channels. Cross-platform analysis (e.g., Facebook, X, Instagram) is out of scope but would be required for broader market intelligence.

### Future Work and Next Tasks

**Task 4 – Advanced Text Analytics & Insights**
The next phase of the project focuses on extracting higher-level insights from Telegram message text, including:

* Sentiment analysis to track public perception of medical and pharmaceutical products
* Topic modeling to identify emerging health trends and promotional narratives
* Named Entity Recognition (NER) for drugs, brands, organizations, and medical conditions
* Time-series analysis to correlate content trends with engagement metrics

These features will transform raw message content into decision-ready analytical signals.

**Task 5 – Business Intelligence & Visualization Layer**
A dedicated analytics consumption layer will be added, including:

* BI dashboards (e.g., Power BI, Metabase, or Superset)
* Channel-level and product-level performance views
* Image vs. text engagement comparisons
* Trend monitoring and anomaly detection

This task bridges the gap between the analytical warehouse and non-technical stakeholders.

**Model Specialization & Fine-Tuning**
Future iterations may include fine-tuning vision models on domain-specific datasets or introducing custom classifiers for medical product recognition.

**Streaming & Automation**
Replacing batch ingestion with a streaming or scheduled incremental pipeline would improve freshness and enable real-time use cases such as compliance monitoring and early-warning systems.

**Scalability & Governance Enhancements**
Planned improvements include metadata management, data catalog integration, and role-based access controls to support enterprise-scale usage.

## Conclusion

This project demonstrates a production-level analytics pipeline, combining data engineering, analytics engineering, and AI-based enrichment. The system is modular, testable, and extensible, making it suitable for real-world analytical workloads.
