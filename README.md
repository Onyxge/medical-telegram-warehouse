# Ethiopian Medical Business Insights Platform (EMBIP)

## 📖 Executive Summary

The **Ethiopian Medical Business Insights Platform (EMBIP)** is a comprehensive data engineering solution designed to centralize, standardize, and analyze the fragmented digital footprint of the Ethiopian medical sector on Telegram.

By transitioning from ad hoc manual monitoring to an automated **ELT (Extract, Load, Transform)** architecture, this platform enables data-driven decision-making related to pharmaceutical availability, pricing trends, and marketing strategies. The system ingests unstructured data streams, enriches them using Computer Vision via **YOLOv5**, and delivers structured business intelligence through a high-performance **REST API**.

---

## 🏗 System Architecture

The platform adheres to **Modern Data Stack** principles, prioritizing modularity, scalability, and data resilience.

> [Insert Architecture Diagram Here]

### Architectural Decisions (ADR)

| Component     | Choice                    | Rationale                                                                                                                                                                                          |
| ------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ingestion     | ELT over ETL              | Raw data is loaded immediately into a Data Lake or Warehouse using a raw schema before transformation. This preserves data lineage and allows historical reprocessing when business logic changes. |
| Orchestration | Asset-Based (Dagster)     | Unlike task-based orchestrators such as Airflow, Dagster understands data assets and their dependencies, preventing downstream jobs from running on stale data.                                    |
| Modeling      | Dimensional (Star Schema) | The warehouse uses Fact and Dimension tables following the Kimball methodology, optimizing query performance for BI and aggregation workloads.                                                     |
| Enrichment    | Hybrid AI                 | Combines NLP for text and Computer Vision using YOLOv5 for images to capture the full context of visual commerce common in Telegram channels.                                                      |

---

## 🛠 Technology Stack

* **Ingestion:** Python, Telethon (MTProto API)
* **Storage (Data Lake):** Local JSON or Object Storage
* **Data Warehouse:** PostgreSQL 15+
* **Transformation:** dbt Core
* **Orchestration:** Dagster
* **Computer Vision:** PyTorch, YOLOv5
* **API / Serving:** FastAPI, Uvicorn, Pydantic
* **Containerization:** Docker (Optional, Roadmap)

---

## 📂 Repository Structure

The project is organized to clearly separate concerns between extraction, transformation, orchestration, and serving.

```bash
medical-telegram-warehouse/
├── api/                       # [Task 4] REST API and Serving Layer
│   ├── main.py                # Application entrypoint
│   ├── crud.py                # Database transaction logic
│   └── schemas.py             # Pydantic data contracts
│
├── medical_warehouse/         # [Task 2] dbt transformation layer
│   ├── models/
│   │   ├── raw/               # Source configurations
│   │   ├── staging/           # Cleaning and casting views
│   │   └── marts/             # Final dimensional models (facts and dims)
│   └── tests/                 # Data quality tests
│
├── orchestration/             # [Task 5] Dagster automation
│   ├── assets/                # Asset definitions (scrapers, dbt, YOLO)
│   └── jobs/                  # Schedule definitions
│
├── scripts/                   # [Task 1] Extraction and load scripts
│   ├── telegram_scraper.py    # Telethon scraper implementation
│   └── load_raw.py            # JSON to Postgres loader
│
├── src/                       # [Task 3] Machine learning modules
│   └── yolo_detect.py         # Object detection inference engine
│
├── data/                      # Local data lake (gitignored)
└── requirements.txt           # Dependency management
```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* PostgreSQL 14 or higher
* Telegram API credentials (`api_id`, `api_hash`) from `my.telegram.org`

### 1. Environment Configuration

Clone the repository and create a `.env` file in the project root.

```bash
git clone https://github.com/YourOrg/medical-telegram-warehouse.git
cd medical-telegram-warehouse
cp .env.example .env
```

#### Required `.env` Variables

```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your db name
DB_USER=postgres
DB_PASSWORD=your password

# Telegram API Configuration
TG_API_ID=123456
TG_API_HASH=your_api_hash
TG_SESSION_NAME=medical_scraper
```

### 2. Installation

Install Python dependencies using a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Database Initialization

Ensure PostgreSQL is running. Table creation is handled by the scraper and dbt, but the database must exist.

```sql
CREATE DATABASE medical_dw;
```

---

## ⚙️ Usage and Orchestration

The entire pipeline is managed using **Dagster**, providing a single pane of glass for operations.

### Running the Pipeline (UI Method)

1. Launch the Dagster development server:

   ```bash
   dagster dev -m orchestration
   ```
2. Navigate to `http://127.0.0.1:3000`.
3. Select `ingestion_job` and click **Materialize All**.

This executes the full pipeline: Scrape → Load → Enrich (YOLO) → Transform (dbt).

### Manual Execution (CLI Method)

Individual components can be run independently for debugging.

**Scraping**

```bash
python scripts/telegram_scraper.py
```

**Transformation**

```bash
cd medical_warehouse
dbt build
```

**Serving (API)**

```bash
uvicorn api.main:app --reload
```

---

## 📊 Data Model (Star Schema)

The warehouse converts raw JSON data into a structured schema optimized for BI tools such as Tableau, Power BI, and Metabase.

* **fct_messages:** Central fact table containing `view_count`, `share_count`, and text metadata.
* **fct_image_detections:** Fact table containing YOLO inference confidence scores and detected object counts per message.
* **dim_channels:** Slowly Changing Dimension (Type 1) for channel metadata including name and subscriber count.
* **dim_dates:** Standard date dimension for temporal aggregation.

---

## 🔌 API Reference

The platform exposes a fully documented REST API. After starting the server, access Swagger UI at:

`http://localhost:8000/docs`

### Key Endpoints

| Method | Endpoint                  | Description                                                       |
| ------ | ------------------------- | ----------------------------------------------------------------- |
| GET    | `/reports/top-products`   | Returns trending medical products based on NLP frequency analysis |
| GET    | `/reports/visual-content` | Analyzes image-heavy channels and detection ratios                |
| GET    | `/channels/{id}/activity` | Returns time-series data for channel posting activity             |
| GET    | `/search/messages`        | Full-text search across the historical message archive            |

---

## 🛣 Roadmap

* **Phase 1 (Current):** Single-node deployment with local data lake
* **Phase 2:** Containerization using Docker Compose and cloud deployment with AWS RDS and S3
* **Phase 3:** Advanced NLP using Named Entity Recognition for extracting drug prices and currencies
* **Phase 4:** Real-time alerting via Telegram bots for keyword-based triggers

---

**Developed by:** Yonatan
