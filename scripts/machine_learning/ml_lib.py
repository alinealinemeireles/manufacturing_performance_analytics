"""
ml_lib.py

Helper functions used by the 4 Machine Learning notebooks (09-12) --
same idea as etl_lib.py, but for the modeling side: splitting data
correctly, evaluating the model, saving/loading it.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)

# ---------------------------------------------------------------------------
# 1. SPLITTING THE DATA (train/test)
# ---------------------------------------------------------------------------

def split_by_date(df: pd.DataFrame, date_column: str, test_fraction: float = 0.2):
    """Splits the data by date instead of randomly -- the oldest rows go
    to training, the most recent rows go to testing.

    I first thought about using a plain random train/test split, but
    that's wrong for this kind of data: if I shuffle the rows before
    splitting, the model could end up "seeing" information from the
    future during training (like a machine failure next week helping it
    guess a failure from last week), which makes it look far more
    accurate than it would actually be in practice. Splitting by date
    avoids that.
    """
    sorted_df = df.sort_values(date_column).reset_index(drop=True)
    cutoff = int(len(sorted_df) * (1 - test_fraction))
    train = sorted_df.iloc[:cutoff].copy()
    test = sorted_df.iloc[cutoff:].copy()
    return train, test


# ---------------------------------------------------------------------------
# 2. REGRESSION METRICS (when the target is a number, like a quantity)
# ---------------------------------------------------------------------------

def regression_metrics(y_true, y_pred) -> dict:
    """MAE/RMSE in the same unit as the target (easy to compare against
    the target's average to see if the error is big or small), MAPE as
    a percentage, and R2 to know how much better the model is than just
    guessing the average."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    nonzero = y_true != 0
    if nonzero.any():
        mape = np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
    else:
        mape = np.nan

    r2 = r2_score(y_true, y_pred)

    return {"MAE": mae, "RMSE": rmse, "MAPE_%": mape, "R2": r2}


# ---------------------------------------------------------------------------
# 3. CLASSIFICATION METRICS (when the target is yes/no)
# ---------------------------------------------------------------------------

def classification_metrics(y_true, y_pred, probability=None) -> dict:
    """Accuracy alone is misleading here, because the "yes" class is
    rare in every classifier in this project (lot rejections, machine
    failures etc. are around 5%-40% of the data, depending on the
    model) -- a model that always predicts "no" would score high on
    accuracy and be completely useless. So I always look at
    precision/recall/F1 too, and ROC-AUC when I have a probability."""
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
    }
    if probability is not None:
        try:
            metrics["ROC_AUC"] = roc_auc_score(y_true, probability)
        except ValueError:
            metrics["ROC_AUC"] = np.nan
    return metrics


def show_classification_report(y_true, y_pred, class_names=("Negative", "Positive")):
    print(classification_report(y_true, y_pred, target_names=list(class_names), zero_division=0))
    print("Confusion matrix (rows=actual, columns=predicted):")
    print(pd.DataFrame(
        confusion_matrix(y_true, y_pred),
        index=[f"Actual {n}" for n in class_names],
        columns=[f"Predicted {n}" for n in class_names],
    ))


# ---------------------------------------------------------------------------
# 4. SAVING / LOADING MODELS
# ---------------------------------------------------------------------------

def save_model(model, path: str, **metadata):
    """Saves the model along with some extra information (feature
    names, metrics) in the same file, so I can open it again later and
    remember what it was without digging through an old notebook."""
    joblib.dump({"model": model, "metadata": metadata}, path)


def load_model(path: str):
    bundle = joblib.load(path)
    return bundle["model"], bundle["metadata"]
