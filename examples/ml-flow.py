

TODO BASE EXAMPLE ON https://mlflow.org/docs/latest/model-registry.html#api-workflow
MAYBE USE CLICK LIB TO HANDLE EXTRA PARAMS (https://click.palletsprojects.com/en/8.1.x/api/#commands) ?
USE ROUTER TO LOAD CONFIG VALUES (FLATTEN SUB_DICTS?)


# Adaptation of https://github.com/mlflow/mlflow-example/blob/master/train.py

# Usage:
# with interlinked cli: `interlinked examples.ml-flow run train`
# or with python interpreter `python examples/ml-flow.py`

from pathlib import Path
import warnings

from pandas import read_csv
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn
from numpy import sqrt, random

from interlinked import depend, provide, run


HERE = Path(__file__).parent


def eval_metrics(actual, pred):
    rmse = sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


@provide("wine-quality")
def ingest():
    wine_path = HERE / "wine-quality.csv"
    return read_csv(wine_path)

    
@depend(df="wine-quality")
@provide("train")
def train(df, alpha=0.5, l1_ratio=0.5):
    warnings.filterwarnings("ignore")
    random.seed(40)

    # Split the data into training and test sets. (0.75, 0.25) split.
    train, test = train_test_split(df)

    # The predicted column is "quality" which is a scalar from [3, 9]
    train_x = train.drop(["quality"], axis=1)
    test_x = test.drop(["quality"], axis=1)
    train_y = train[["quality"]]
    test_y = test[["quality"]]

    lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
    lr.fit(train_x, train_y)

    predicted_qualities = lr.predict(test_x)

    (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

    print("Elasticnet model (alpha=%f, l1_ratio=%f):" % (alpha, l1_ratio))
    print("  RMSE: %s" % rmse)
    print("  MAE: %s" % mae)
    print("  R2: %s" % r2)

    with mlflow.start_run():
        mlflow.log_param("alpha", alpha)
        mlflow.log_param("l1_ratio", l1_ratio)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)
        mlflow.sklearn.log_model(lr, "model")



if __name__ == "__main__":
    run("train")
