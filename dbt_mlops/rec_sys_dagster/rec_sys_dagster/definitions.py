import os

from dagster import Definitions, define_asset_job
from dagster_dbt import DbtCliResource

#from .assets import dbt_mlops_dbt_assets, preprocessed_data, split_data, keras_dot_product_model, log_model#, evaluate_model
from .assets import *
from .constants import dbt_project_dir
from .airbyte import airbyte_assets

all_assets = [dbt_mlops_dbt_assets, preprocessed_data
            ,split_data, numpy_dot_product_model
            ,log_model, evaluate_model, airbyte_assets
            ]

mlflow_resources = {
    'mlflow': {
        'config': {
            'experiment_name': 'recommender_system',
        }            
    },
}

# training_config = {
#     'keras_dot_product_model': {
#         'config': {
#             'batch_size': 128,
#             'epochs': 10,
#             'learning_rate': 1e-3,
#             'embeddings_dim': 5
#         }
#     }
# }

training_config = {
    'numpy_dot_product_model': {
        'config': {
            'num_factors': 50,
            'epochs': 20,
            'learning_rate': 0.005
        }
    }
}

postgres_config = {
    'preprocessed_data': {
        'config': {
            'hostname': "localhost",
            'username': "postgres",
            'password': "mysecretpassword",
            'db_name': "mlops",
            'port': 5432
        }
    }
}

job_training_config = {
    'resources': {
        **mlflow_resources
    },
    'ops': {
        **training_config,
        **postgres_config
    }
}

full_process_job = define_asset_job(
    name="full_process",
    selection="*",
    config=job_training_config
    )

defs = Definitions(
    assets=all_assets,
    resources={
        "dbt": DbtCliResource(project_dir=os.fspath(dbt_project_dir)),
    },
    jobs=[full_process_job]
)