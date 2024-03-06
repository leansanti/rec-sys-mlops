# rec-sys-mlops project overview
We'll use Airbyte + dbt for the data pipeline, MLFlow for experimenting, track model metrics and parameters, and save models in it's Model Registry. Finally, we'll use Dagster to orchestrate the entire workflow where we'll train a recommendation system model and evaluate it's performance.

Dagster notes:
- The objects within Dagster that connect to external services are called `Resources`. In this project we'll need to create one to connect to `MLFlow`. The `I/O Managers` are a type of Resource.
- The Dagster feature `ops` are all the operations that don't generate an asset. They are also called `non-asset jobs`

# Creación de entorno
```bash

# Using conda
conda create -n dagster-env-rec-sys python=3.9.6
conda activate dagster-env-rec-sys

# Using venv
#python3.9 -m venv dagster-env-rec-sys
#source dagster-env-rec-sys/bin/activate

# Install packages
pip install dagster==1.5.7 pendulum==2.1.2

```

# Creo estructura de carpetas
```bash

dagster project scaffold --name recommender_system

```


# Instalación de dependencias y creación de paquete
Modificar el archivo setup.py para agregar las librerias correspondientes

Install the packages and create the dagster package based on `setup.py` file called `/recommender_system.egg-info`
```bash
cd recommender_system

pip install -e ".[dev]"
```

# Correr dagster en modo development
```bash
# Seteo de variables
set -o allexport && source environments/local && set +o allexport

# Corro dagster
dagster dev # con esto se sirve el modulo (code location) que creamos anteriormente en el puerto 3000 del localhost
```
Abrir browser en http://localhost:3000/

# Configurar archivos Dagster (init raiz y assets) e ir haciendo el Reload en la sección Deployment de la web UI de Dagster hasta que estemos conformes. Tener en cuenta que los assets que quieran interactuar con MLflow van a tirar error porque todavía no iniciamos ese servidor.


# Definición de variables de entorno
Como la terminal que estabamos usando la dedicamos a correr el server de dagster tenemos que crear otra y volver a pararnos en el venv correspondiente y volver a setear las vars de entorno
```bash
# Seteo de variables
set -o allexport && source environments/local && set +o allexport

# Verificarlo
echo $postgres_data_folder
echo $MLFLOW_ARTIFACTS_PATH
```

# PSQL DB

### Iniciar Docker en nuestro equipo

### Bajar imagen
```bash
docker pull postgres
```

### Instanciar imagen (cuando se instancia la imagen se crea el contenedor)
```bash
docker run -d \
    --name recsys-elt-postgres \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -v $postgres_data_folder:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres
```

### Si docker ya lo habíamos creado correr el siguiente comando unicamente
```bash
docker start recsys-elt-postgres
```

### Verificar funcionamiento, y manejo del contenedor
```bash
docker ps

docker ps -a

docker exec -it recsys-elt-postgres-v4 /bin/bash

root@08487b094f8a:/#  psql -U postgres

postgres=# exit

root@b9da8c0dc815:/# exit

psql -U postgres -h localhost -p 5432 # Esta alternativa es para saltearnos el paso de docker exec -it
```

### Create MLFLOW DB

Primero toca volver a ingresar al docker que contiene el postgres como vimos en la sección anterior.
```bash
docker exec -it recsys-elt-postgres /bin/bash

root@08487b094f8a:/#  psql -U postgres
```

```sql
CREATE DATABASE mlflow_db;
CREATE USER mlflow_user WITH ENCRYPTED PASSWORD 'mlflow';
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow_user;
```

```bash
postgres=# exit
root@b9da8c0dc815:/# exit
```

# Mlflow server

### Dado que vamos a usar postgres como backend store del mlflow server necesitamos instalar psycopg
```bash
pip install psycopg2-binary --no-cache-dir # ahora probamos instalarlo en el mismo env de dagster para no tener dos
```

### Inicializamos el mlflow server seteando como backend store el postgres que montamos en el docker y para los artifacts le indicamos la ruta (la cual esta linkeada como volumen al docker)
Before you run any Dagster jobs that will materialize assets that will interact with MLFlow you need to have this sections ready.
```bash
mlflow server --backend-store-uri postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$MLFLOW_POSTGRES_DB --default-artifact-root $MLFLOW_ARTIFACTS_PATH -h 0.0.0.0 -p 8002
```
Abrir browser en http://localhost:8002/

# Hacemos Reload en la sección Deployment de Dagster y probamos Materializar los assets que interactúan con MLFlow

# Configuramos Airbyte
```bash
cd recommender_system/ELT
# clone Airbyte from GitHub
git clone --depth=1 https://github.com/airbytehq/airbyte.git
# switch into Airbyte directory
cd airbyte
```

# start Airbyte
```bash
./run-ab-platform.sh
```
Abrir browser en http://localhost:8000/

username: `airbyte`
password: `password`

## Creación de source (csvs)
https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/peliculas_0.csv
https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/usuarios_0.csv
https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/scores_0.csv

## Creación de destination (psql)

```bash
psql -U postgres -h localhost -p 5432 # si ingresamos de esta forma al container nos pide la password
```

```sql
CREATE DATABASE mlops;
CREATE USER airbyte WITH ENCRYPTED PASSWORD 'airbyte';
GRANT ALL PRIVILEGES ON DATABASE mlops TO airbyte;
GRANT ALL ON SCHEMA public TO airbyte;
GRANT USAGE ON SCHEMA public TO airbyte;
ALTER DATABASE mlops OWNER TO airbyte;
```
```bash
postgres=# exit
```

Ahora que ya tenemos creada la database que usaremos para configurar como destino en Airbyte, volvemos a la UI de Airbyte y hacemos dicha configuración tanto del destino como de las conexiones entre sources y destino.

# dbt
```bash
pip install dbt-postgres

cd recommender_system/ELT

dbt init dbt_mlops # al ejecutarlo nos pediran las especificaciones del postgres (valores a ingresar: localhost, 5432, postgres, mysecretpassword, mlops, target) - Esto nos va a crear una carpeta llamada dbt_mlops con todo lo necesario para el proyecto

open ~/.dbt/profiles.yml # el dbt init nos crea este file si es la primera vez que hacemos un dbt init y sino, simplemente agrega el profile del este project a dicho archivo (lo appendea abajo de los otros projects dbt que tengamos)

cd dbt_mlops

dbt debug # testeamos la conexión
```

### Creamos `schema.yml` dentro de la carpeta `dbt_mlops/models`
### Creamos los .sql para las transformaciones que querramos hacer dentro de la carpeta `dbt_mlops/models`
Aclaración: el nombre de las tablas resultantes con la data transformada será el nombre del file .sql que contiene las transformaciones correspondientes.

### Ejecutamos las transformaciones. Esto nos creará las tablas con la data transformada en el schema `target` de la postgres db `mlops`.
Si es la primera vez que lo corremos, se creará el schema target automaticamente.
```bash
dbt run # asegurarse estar parados en ELT/dbt_mlops
```

# Integración Dagster con Airbyte & dbt
```bash
pip install dagster-dbt==0.21.7 #(tiene que ser una version que no entre en conflicto con dagster==1.5.7)
# Como mejora, podríamos agregarlo al setup.py para instalarlo al momento del pip install -e .[dev]
```

creamos constants.py - DONE
creamos dbt.py - DONE

empezando de arriba (luego modificar el Readme)

conda activate dagster-env-rec-sys # este es el env que anda

dagster-dbt project scaffold --project-name rec_sys_dagster

cd rec_sys_dagster

configurar el setup.py con todo lo que necesitamos

pip install -e ".[dev]"

dagster dev

```bash
pip install dagster-airbyte==0.21.7

pip install dagster-postgres==0.21.7
```
Configuramos dagster_config.yml para el resource de lectura de postgres en el asset de preprocessing()


Materializar los assets desde el full_process job desde Dagster UI