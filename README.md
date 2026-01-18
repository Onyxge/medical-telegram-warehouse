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

- **Domain-Specific Vision Accuracy**  
  The YOLOv8 model used for image enrichment is trained on general-purpose object classes (COCO). As a result, it cannot reliably distinguish between specific medical or pharmaceutical packaging types or identify brand-level details.

- **No Advanced Text Analytics Yet**  
  Telegram message text is currently stored and modeled structurally, but no higher-level analytics such as topic modeling, sentiment analysis, or entity extraction have been implemented.

- **Batch-Oriented Processing**  
  The pipeline operates in batch mode. Data is scraped, loaded, transformed, and enriched manually or sequentially rather than in near real-time.

- **No External Data Consumption Layer**  
  While the warehouse is analytics-ready, there is currently no programmatic interface for downstream applications, dashboards, or services to query curated business metrics.

- **Manual Pipeline Execution**  
  All pipeline stages (scraping, loading, dbt runs, enrichment) are triggered manually, increasing the risk of missed steps and reducing operational reliability.

---

### Future Work

#### Task 4 – Build an Analytical API

**Objective:** Expose the analytics warehouse through a REST API that answers real business questions.

Planned enhancements include:

- Develop a REST API using **FastAPI** or **Flask**
- Expose curated endpoints such as:
  - Top active medical channels by posting volume
  - Image-based promotional content trends over time
  - Product vs lifestyle image ratios per channel
  - Daily or weekly engagement metrics
- Query only **dbt mart models** (not raw or staging tables) to preserve data contracts
- Implement request validation, pagination, and basic authentication
- Enable downstream consumers such as:
  - BI tools
  - Dashboards
  - External analytical services

This API will serve as the **official consumption layer** of the data platform.

---

#### Task 5 – Pipeline Orchestration

**Objective:** Automate and operationalize the entire data pipeline using an orchestration tool.

Planned orchestration improvements:

- Introduce an orchestration framework such as:
  - **Apache Airflow**
  - **Prefect**
  - **Dagster**
- Define a DAG with clear task dependencies:
  1. Telegram data ingestion
  2. Raw data loading into PostgreSQL
  3. dbt transformations and tests
  4. YOLO image enrichment
  5. Analytical API refresh or cache invalidation
- Add:
  - Task-level retries
  - Failure notifications
  - Execution logging
- Support:
  - Scheduled daily runs
  - Backfills for historical dates
  - Environment-specific configurations (dev vs prod)

This step transitions the project from a **development pipeline** to a **production-grade data system**.

---

### Long-Term Enhancements

- Integrate **OCR** for extracting text from product packaging images
- Add **sentiment analysis and topic modeling** for Telegram message content
- Introduce **data freshness and SLA monitoring**
- Support **incremental dbt models** for performance optimization
- Enable **streaming ingestion** to reduce data latency

---

### Final Note

With Tasks 4 and 5 implemented, the platform evolves into a **fully automated, API-driven analytics system**, capable of serving both internal stakeholders and external applications with trustworthy, enriched insights.

## Conclusion

This project demonstrates a production-level analytics pipeline, combining data engineering, analytics engineering, and AI-based enrichment. The system is modular, testable, and extensible, making it suitable for real-world analytical workloads.
