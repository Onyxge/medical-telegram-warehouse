from dagster import Definitions, load_assets_from_modules
from . import assets, dbt_assets

# Load all assets from our python files
all_assets = load_assets_from_modules([assets, dbt_assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "dbt": dbt_assets.dbt_resource,
    },
)