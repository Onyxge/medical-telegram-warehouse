import os
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets
from pathlib import Path

# FIX: Point to the 'medical_warehouse' subfolder where dbt_project.yml lives
# Path(__file__) = orchestration/dbt_assets.py
# .parent        = orchestration/
# .parent        = medical-telegram-warehouse/ (Root)
# / "medical_warehouse" = The actual dbt project folder
DBT_PROJECT_DIR = Path(__file__).parent.parent / "medical_warehouse"

# Define the dbt resource
dbt_resource = DbtCliResource(project_dir=os.fspath(DBT_PROJECT_DIR))

# Create assets automatically from your dbt project
# Note: We look for manifest.json inside that specific folder's target directory
@dbt_assets(manifest=DBT_PROJECT_DIR / "target" / "manifest.json")
def medical_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()