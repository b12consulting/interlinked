"""
Example that combine trainign and inference and reies on
`ml-flow-params.toml` to provide parameters.

Use log-model-xyz as target to trigger training and log model to mlflow:

    $ interlinked ml-flow run log-model-first --config ml-flow-params.toml
    Successfully registered model 'sk-learn-random-forest-first'.
    Created version '1' of model 'sk-learn-random-forest-first'.

    $ interlinked ml-flow run log-model-second --config ml-flow-params.toml
    Successfully registered model 'sk-learn-random-forest-second'.
    Created version '1' of model 'sk-learn-random-forest-second'.

    $ interlinked ml-flow run log-model-second --config ml-flow-params.toml
    Registered model 'sk-learn-random-forest-second' already exists. Creating a new version of this model...
    Created version '2' of model 'sk-learn-random-forest-second'.

Use infer-xyz as target to trigger inference:

    $ interlinked ml-flow run infer-first --config ml-flow-params.toml
    Use model sk-learn-random-forest-first at version 1
    $ interlinked ml-flow run infer-second --config ml-flow-params.toml
    Use model sk-learn-random-forest-second at version 2

You can pass an extra `-s` cli argument to display the output (if any) of the target function

    $ interlinked ml-flow run infer-second --config ml-flow-params.toml  -s
    Use model sk-learn-random-forest-second at version 2
    [ 81.32292293  38.42718558  38.27094583  11.8126125   75.89833742
      15.26967922  95.81896899 -79.19412999 -84.89151001  10.05561881
      ...
"""

from sklearn.datasets import make_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from mlflow.models import infer_signature
import mlflow
import mlflow.pyfunc
import mlflow.sklearn

from interlinked import provide, depend


@provide("dataset-{name}")
def dataset(n_features: int = 4, n_informative: int = 2, random_state: int = 0):
    X, y = make_regression(
        n_features=n_features,
        n_informative=n_informative,
        random_state=random_state,
        shuffle=False,
    )
    return X, y


@depend(dataset="dataset-{name}")
@provide("train-{name}")
def train_model(name, dataset):
    X, y = dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    params = {"max_depth": 2, "random_state": 42}
    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Infer the model signature
    signature = infer_signature(X_test, y_pred)

    # Log parameters and metrics using the MLflow APIs
    mlflow.log_params(params)
    mlflow.log_metrics({"mse": mean_squared_error(y_test, y_pred)})

    return model, signature


@depend(trainset="train-{name}")
@provide("log-model-{name}")
def log_model(name, trainset):
    model, signature = trainset

    # Log the sklearn model and register as version 1
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="sklearn-model",
        signature=signature,
        registered_model_name=f"sk-learn-random-forest-{name}",
    )




@depend(dataset="dataset-{name}")
@provide("infer-{name}")
def infer(name, dataset, version=1):
    X, y = dataset
    model_name = f"sk-learn-random-forest-{name}"
    print(f"Use model {model_name} at version {version}")
    model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{version}")
    res = model.predict(X)
    return res
