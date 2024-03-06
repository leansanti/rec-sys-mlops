# from setuptools import find_packages, setup

# setup(
#     name="rec_sys_dagster",
#     version="0.0.1",
#     packages=find_packages(),
#     install_requires=[
#         "dagster>1.5.7",
#         "pendulum<3.0",
#         "dagster-cloud",
#         #"dagster-dbt==0.21.7",
#         "dagster-dbt",
#         "dbt-core>=1.4.0",
#         "dbt-postgres",
#     ],
#     extras_require={
#         "dev": [
#             "dagster-webserver",
#         ]
#     },
# )

from setuptools import find_packages, setup

import os
DAGSTER_VERSION=os.getenv('DAGSTER_VERSION', '1.5.7')
DAGSTER_LIBS_VERSION=os.getenv('DAGSTER_LIBS_VERSION', '0.21.7') # '0.21.6'
MLFLOW_VERSION=os.getenv('MLFLOW_VERSION', '2.8.0')

# Esto nos creara un packete editable con el nombre que pasemos en el arg `name` cuando corramos el comando `pip install -e ".[dev]"`
setup(
    name="recommender_system",
    packages=find_packages(exclude=["recommender_system_tests"]),
    install_requires=[
        f"dagster=={DAGSTER_VERSION}",
        f"dagster-mlflow=={DAGSTER_LIBS_VERSION}",
        f"mlflow=={MLFLOW_VERSION}",
        f"tensorflow==2.14.0",
    ],
    # Acá van los paquetes que no se necesitan en prod pero si en dev
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)