from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_instance

from .constants import AIRBYTE_CONNECTION_ID, AIRBYTE_CONFIG

airbyte_instance = airbyte_resource.configured(AIRBYTE_CONFIG)

airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance, key_prefix=["recommmender_system_raw"]) # sale del nombre que le hayamos dado a nuestro source en schema.yml