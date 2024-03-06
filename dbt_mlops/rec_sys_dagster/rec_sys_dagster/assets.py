from dagster import AssetExecutionContext, AssetIn, AssetOut, multi_asset, asset, Int, Float, String
from dagster_dbt import DbtCliResource, dbt_assets, get_asset_key_for_model
from dagster_mlflow import mlflow_tracking
import pandas as pd
from sklearn.model_selection import train_test_split
import psycopg2
import numpy as np

import mlflow
#from mlflow.pyfunc import PythonModel

from .constants import dbt_manifest_path


@dbt_assets(manifest=dbt_manifest_path)
def dbt_mlops_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
    
    
@multi_asset(
    compute_kind="python",
    deps=get_asset_key_for_model([dbt_mlops_dbt_assets], "scores_peliculas_usuarios"),
    outs={
        "preprocessed_training_data": AssetOut(),
        "user2Idx": AssetOut(),
        "movie2Idx": AssetOut(),
    },
    config_schema={
        'hostname': String,
        'username': String,
        'password': String,
        'db_name': String,
        'port': Int
    }
)
def preprocessed_data(context):
    
    ## Read data from postgres
    
    conn_params = {
        "host":context.op_config["hostname"],
        "user":context.op_config["username"],
        "password":context.op_config["password"],
        "dbname":context.op_config["db_name"],
        "port":context.op_config["port"]
    }
    
    # Establishing the connection
    connection = psycopg2.connect(**conn_params)
    
    # Your SQL query
    query = "SELECT * FROM target.scores_peliculas_usuarios;"
    
    # Execute query and save the result in a pandas DataFrame
    scores_peliculas_usuarios = pd.read_sql_query(query, connection)
    
    # Processing
    u_unique = scores_peliculas_usuarios.user_id.unique()
    #user2Idx = {o:i+1 for i,o in enumerate(u_unique)}
    user2Idx = {o:i for i,o in enumerate(u_unique)}
    m_unique = scores_peliculas_usuarios.movie_id.unique()
    #movie2Idx = {o:i+1 for i,o in enumerate(m_unique)}
    movie2Idx = {o:i for i,o in enumerate(m_unique)}
    scores_peliculas_usuarios['encoded_user_id'] = scores_peliculas_usuarios.user_id.apply(lambda x: user2Idx[x])
    scores_peliculas_usuarios['encoded_movie_id'] = scores_peliculas_usuarios.movie_id.apply(lambda x: movie2Idx[x])
    
    context.log.info(f'Check user2Idx first elements: {list(user2Idx.items())[:5]}')
    context.log.info(f'Check movie2Idx first elements: {list(movie2Idx.items())[:5]}')
    
    preprocessed_training_data = scores_peliculas_usuarios.copy()

    return preprocessed_training_data, user2Idx, movie2Idx


@multi_asset(
    ins={
        "preprocessed_training_data": AssetIn(
    )
    },
    outs={
        "X_train": AssetOut(),
        "X_test": AssetOut(),
        "y_train": AssetOut(),
        "y_test": AssetOut(),
    }
)
def split_data(context, preprocessed_training_data):
    test_size=0.10
    random_state=42
    X_train, X_test, y_train, y_test = train_test_split(
        preprocessed_training_data[['encoded_user_id', 'encoded_movie_id']],
        preprocessed_training_data[['rating']],
        test_size=test_size, random_state=random_state
    )
    return X_train, X_test, y_train, y_test


# @asset(
#     resource_defs={'mlflow': mlflow_tracking},
#     ins={
#         "X_train": AssetIn(),
#         "y_train": AssetIn(),
#         "user2Idx": AssetIn(),
#         "movie2Idx": AssetIn(),
#     },
#     config_schema={
#         'batch_size': Int,
#         'epochs': Int,
#         'learning_rate': Float,
#         'embeddings_dim': Int
#     }
# )
# def keras_dot_product_model(context, X_train, y_train, user2Idx, movie2Idx):
#     from .model_helper import get_model
#     from keras.optimizers import Adam
#     mlflow = context.resources.mlflow
#     mlflow.log_params(context.op_config)

    
#     batch_size = context.op_config["batch_size"]
#     epochs = context.op_config["epochs"]
#     learning_rate = context.op_config["learning_rate"]
#     embeddings_dim = context.op_config["embeddings_dim"]
    
#     print(f'HEY, batch_size {batch_size}')

#     model = get_model(len(movie2Idx), len(user2Idx), embeddings_dim)

#     model.compile(Adam(learning_rate=learning_rate), 'mean_squared_error')
    
#     context.log.info(f'batch_size: {batch_size} - epochs: {epochs}')
#     history = model.fit(
#         [
#             X_train.encoded_user_id,
#             X_train.encoded_movie_id
#         ], 
#         y_train.rating, 
#         batch_size=batch_size,
#         # validation_data=([ratings_val.userId, ratings_val.movieId], ratings_val.rating), 
#         epochs=epochs, 
#         verbose=1
#     )
#     for i, l in enumerate(history.history['loss']):
#         mlflow.log_metric('mse', l, i)
#     from matplotlib import pyplot as plt
#     fig, axs = plt.subplots(1)
#     axs.plot(history.history['loss'], label='mse')
#     plt.legend()
#     mlflow.log_figure(fig, 'plots/loss.png')
#     return model

# # version simple
# @asset(
#     resource_defs={'mlflow': mlflow_tracking},
#     ins={
#         "X_train": AssetIn(),
#         "y_train": AssetIn(),
#         "user2Idx": AssetIn(),
#         "movie2Idx": AssetIn(),
#     },
#     config_schema={
#         'batch_size': int,
#         'epochs': int,
#         'learning_rate': float,
#         'embeddings_dim': int
#     }
# )
# def keras_dot_product_model(context, X_train, y_train, user2Idx, movie2Idx):
    
#     context.log.info('Start of keras_dot_product_model asset')
    
#     #from .model_helper import get_model
    
#     context.log.info('get_model func imported successfully from model_helper module')
    
#     #from tensorflow.keras.optimizers import Adam
    
#     context.log.info('Adam class imported successfully')

    
#     print('Check debuggin santito - post imports')
#     context.log.info('Imports successful')
    
#     # Config parameters
#     batch_size = context.op_config["batch_size"]
#     epochs = context.op_config["epochs"]
#     learning_rate = context.op_config["learning_rate"]
#     embeddings_dim = context.op_config["embeddings_dim"]
    
#     context.log.info(f"Configuration - batch_size: {batch_size}, epochs: {epochs}, learning_rate: {learning_rate}, embeddings_dim: {embeddings_dim}")
    
#     print("batch_size",batch_size)
    
#     from tensorflow.keras.optimizers import Adam
    
#     context.log.info('Adam class imported successfully')

#     try:
#         # Initialize model
#         #from .model_helper import get_model
#         model = get_model(len(movie2Idx), len(user2Idx), embeddings_dim)
#         context.log.info('Model initialized successfully')

#         # Compile model
#         model.compile(optimizer=Adam(learning_rate=learning_rate), loss='mean_squared_error')
#         context.log.info('Model compiled successfully')

#         # Train model
#         context.log.info('Starting model training')
#         history = model.fit(
#             [X_train.encoded_user_id, X_train.encoded_movie_id],
#             y_train.rating,
#             batch_size=batch_size,
#             epochs=epochs,
#             verbose=1
#         )
#         context.log.info('Model training completed successfully')
#     except Exception as e:
#         context.log.error(f"Error during model training: {str(e)}")
#         raise e
    
#     context.log.info('keras_dot_product_model asset completed successfully')
    
#     # Simplified return without logging or plotting for debugging
#     return model


# @asset(
#     resource_defs={'mlflow': mlflow_tracking},
#     ins={
#         "X_train": AssetIn(),
#         "y_train": AssetIn(),
#         "user2Idx": AssetIn(),
#         "movie2Idx": AssetIn(),
#     },
#     config_schema={
#         'num_factors': Int, # Embedding dimension
#         'epochs': Int,
#         'learning_rate': Float,
#     }
# )
# def numpy_dot_product_model(context, X_train, y_train, user2Idx, movie2Idx):
    
#     context.log.info('Start numpy_dot_product_model asset run')
    
#     num_users = len(user2Idx)
#     num_movies = len(movie2Idx)
    
#     context.log.info(f'num_users: {num_users}, num_movies: {num_movies}')
    
    
#     num_factors = context.op_config['num_factors']
#     epochs = context.op_config['epochs']
#     learning_rate = context.op_config['learning_rate']
    
#     context.log.info('Hyperparams loaded successfully!')
    
    
#     # Initialize user and item embeddings
#     user_embeddings = np.random.normal(scale=1./num_factors, size=(num_users, num_factors))
#     movie_embeddings = np.random.normal(scale=1./num_factors, size=(num_movies, num_factors))

#     context.log.info('User and Item embedings initilized!')

#     # Example training loop (very simplified)
#     for epoch in range(epochs):
#         for user_id, movie_id, rating in zip(X_train.encoded_user_id, X_train.encoded_movie_id, y_train.rating):
            
#             # Predicted rating
#             user_embedding = user_embeddings[user_id]
            
#             #context.log.info('user_embedding processed successfully!')
            
#             # el bug lo tenemos en esta linea
#             movie_embedding = movie_embeddings[movie_id]
            
#             prediction = np.dot(user_embedding, movie_embedding)
            
#             # Error
#             error = rating - prediction
            
#             # Update embeddings
#             user_embeddings[user_id] += learning_rate * error * movie_embedding
#             movie_embeddings[movie_id] += learning_rate * error * user_embedding


#     # Logging, plotting, etc., similar to your existing code
#     # Note: The actual model to return/evaluate would need to be structured differently
#     # since we're not using a Keras model anymore.
    
#     # Placeholder for what might represent the "model" in this simplified context
#     model = {
#         'user_embeddings': user_embeddings,
#         'movie_embeddings': movie_embeddings,
#     }

#     return model


# @asset(
#     resource_defs={'mlflow': mlflow_tracking},
#     ins={
#         "numpy_dot_product_model": AssetIn(),
#     },
#     name="model_data"
# )
# def log_model(context, numpy_dot_product_model):

#     mlflow = context.resources.mlflow
    
#     logged_model = mlflow.log_model(
#         numpy_dot_product_model,
#         "numpy_dot_product_model",
#         registered_model_name='numpy_dot_product_model',
#         input_example=[np.array([1, 2]), np.array([2, 3])],
#     )
#     # logged_model.flavors
#     model_data = {
#         'model_uri': logged_model.model_uri,
#         'run_id': logged_model.run_id
#     }
#     return model_data



# Custom wrapper class for the numpy dot product model
class NumpyDotProductModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model):
        self.user_embeddings = model['user_embeddings']
        self.movie_embeddings = model['movie_embeddings']

    def predict(self, context, model_input):
        # Ensure model_input is a DataFrame
        if not isinstance(model_input, pd.DataFrame):
            raise ValueError("model_input must be a pandas DataFrame")
        
        predictions = np.zeros(len(model_input))
        
        for idx, row in model_input.iterrows():
            user_id = row['user_id']
            movie_id = row['movie_id']
            user_embedding = self.user_embeddings[user_id]
            movie_embedding = self.movie_embeddings[movie_id]
            predictions[idx] = np.dot(user_embedding, movie_embedding)
        
        return predictions

# class NumpyDotProductModelWrapper(mlflow.pyfunc.PythonModel):

#     def load_context(self, context):
#         import numpy as np
#         self.user_embeddings = context.artifacts["user_embeddings"]
#         self.movie_embeddings = context.artifacts["movie_embeddings"]
#         # Load median_rating from the model artifacts
#         self.median_rating = context.artifacts['median_rating']
    
#     def predict(self, context, model_input):
#         # Assuming model_input is a DataFrame with 'user_id' and 'movie_id' columns
#         predictions = np.zeros(len(model_input))
        
#         for idx, (user_id, movie_id) in enumerate(zip(model_input['user_id'], model_input['movie_id'])):
#             try:
#                 user_embedding = self.user_embeddings[user_id]
#                 movie_embedding = self.movie_embeddings[movie_id]
#                 predictions[idx] = np.dot(user_embedding, movie_embedding)
#             except IndexError:
#                 # Fallback to median rating if user or movie is not seen
#                 predictions[idx] = self.median_rating
#         return predictions



@asset(
    resource_defs={'mlflow': mlflow_tracking},
    ins={
        "X_train": AssetIn(),
        "y_train": AssetIn(),
        "user2Idx": AssetIn(),
        "movie2Idx": AssetIn(),
    },
    config_schema={
        'num_factors': Int,  # Embedding dimension
        'epochs': Int,
        'learning_rate': Float,
    }
)
def numpy_dot_product_model(context, X_train, y_train, user2Idx, movie2Idx):
    
    context.log.info('Start numpy_dot_product_model asset run')
    
    num_users = len(user2Idx)
    num_movies = len(movie2Idx)
    
    context.log.info(f'num_users: {num_users}, num_movies: {num_movies}')
    
    
    num_factors = context.op_config['num_factors']
    epochs = context.op_config['epochs']
    learning_rate = context.op_config['learning_rate']
    
    context.log.info('Hyperparams loaded successfully!')
    
    # # Calculate the median rating based on y_train
    # median_rating = np.median(y_train.rating.values)
    # context.log.info(f'Median rating calculated: {median_rating}')
    
    
    # Initialize user and item embeddings
    user_embeddings = np.random.normal(scale=1./num_factors, size=(num_users, num_factors))
    movie_embeddings = np.random.normal(scale=1./num_factors, size=(num_movies, num_factors))

    context.log.info('User and Item embeddings initialized!')

    # Simplified training loop
    for epoch in range(epochs):
        for user_id, movie_id, rating in zip(X_train.encoded_user_id, X_train.encoded_movie_id, y_train.rating):
            
            # Predicted rating
            user_embedding = user_embeddings[user_id]
            movie_embedding = movie_embeddings[movie_id]
            
            prediction = np.dot(user_embedding, movie_embedding)
            
            # Error
            error = rating - prediction
            
            # Update embeddings
            user_embeddings[user_id] += learning_rate * error * movie_embedding
            movie_embeddings[movie_id] += learning_rate * error * user_embedding


    model = {
        'user_embeddings': user_embeddings,
        'movie_embeddings': movie_embeddings,
        #'median_rating': median_rating
    }

    return model

@asset(
    resource_defs={'mlflow': mlflow_tracking},
    ins={
        "numpy_dot_product_model": AssetIn(),
    },
    name="model_data"
)
def log_model(context, numpy_dot_product_model):
    mlflow = context.resources.mlflow
    
    # Wrap the numpy model in the custom class
    model_wrapper = NumpyDotProductModelWrapper(numpy_dot_product_model)

    # Log the model with MLflow, specifying the environment and model wrapper
    logged_model = mlflow.pyfunc.log_model(
        artifact_path="numpy_dot_product_model",
        python_model=model_wrapper,
        registered_model_name="NumpyDotProductModel",
        conda_env="/Users/santiagolean/repos/courses/itba/mlops/rec-sys-mlops/dbt_mlops/rec_sys_dagster/rec_sys_dagster/conda.yaml",  # Adjust the path to where your conda.yaml is located
    )

    model_data = {
        'model_uri': logged_model.model_uri,
        'run_id': mlflow.active_run().info.run_id
    }

    return model_data



# @asset(
#     resource_defs={'mlflow': mlflow_tracking},
#     ins={
#         "model_data": AssetIn(),
#         "X_test": AssetIn(),
#         "y_test": AssetIn(),
#     }
# )
# def evaluate_model(context, model_data, X_test, y_test):
    
#     mlflow = context.resources.mlflow
#     logged_model = model_data['model_uri']

#     loaded_model = mlflow.pyfunc.load_model(logged_model)
    
#     y_pred = loaded_model.predict([
#             X_test.encoded_user_id,
#             X_test.encoded_movie_id
#     ])
#     from sklearn.metrics import mean_squared_error

#     mse = mean_squared_error(y_pred.reshape(-1), y_test.rating.values)
#     mlflow.log_metrics({
#         'test_mse': mse,
#         'test_rmse': mse**(0.5)
#     })

    
@asset(
    resource_defs={'mlflow': mlflow_tracking},
    ins={
        "model_data": AssetIn(),
        "X_test": AssetIn(),
        "y_test": AssetIn(),
        #"X_train": AssetIn(),
        #"y_train": AssetIn(),
    }
)
def evaluate_model(context, model_data, X_test, y_test
                   #, X_train, y_train
                   ):
    mlflow = context.resources.mlflow
    logged_model = model_data['model_uri']

    # Load the model
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    # Create a DataFrame from X_test's encoded user and movie IDs
    df_test = pd.DataFrame({
        'user_id': X_test.encoded_user_id,
        'movie_id': X_test.encoded_movie_id
    })
    # df_test = pd.DataFrame({
    #     'user_id': X_train.encoded_user_id,
    #     'movie_id': X_train.encoded_movie_id
    # })

    # Use the DataFrame to predict
    y_pred = loaded_model.predict(df_test)
    
    from sklearn.metrics import mean_squared_error

    mse = mean_squared_error(y_pred.reshape(-1), y_test.rating.values)
    #mse = mean_squared_error(y_pred.reshape(-1), y_train.rating.values)
    mlflow.log_metrics({
        'test_mse': mse,
        'test_rmse': mse**(0.5),
        # 'train_mse': mse,
        # 'train_rmse': mse**(0.5)
    })