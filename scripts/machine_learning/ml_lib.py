"""
ml_lib.py

Shared helper functions for the 4 ML notebooks (09-12) -- same idea as
etl_lib.py, just for the modeling side: splitting data properly,
evaluating models, saving/loading them.
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
# 1. SPLITTING DATA
# ---------------------------------------------------------------------------

def time_based_split(df: pd.DataFrame, date_col: str, test_frac: float = 0.2):
    """Splits by date instead of randomly -- oldest rows go to train, most
    recent rows go to test.

    I almost used a normal random train_test_split at first, but that's
    wrong for this kind of data: if you shuffle rows before splitting,
    the model can accidentally "see" things from the future while
    training (like a machine failure next week helping it guess a
    failure last week), which makes it look way more accurate than it
    would actually be once deployed. Splitting by date avoids that.
    """
    df_sorted = df.sort_values(date_col).reset_index(drop=True)
    cutoff = int(len(df_sorted) * (1 - test_frac))
    return df_sorted.iloc[:cutoff].copy(), df_sorted.iloc[cutoff:].copy()


# ---------------------------------------------------------------------------
# 2. REGRESSION METRICS
# ---------------------------------------------------------------------------

def regression_metrics(y_true, y_pred) -> dict:
    """MAE/RMSE in the same units as the target (easy to compare against
    the target's average to see if the error is big or small), MAPE as a
    percentage, and R2 for how much better than just guessing the mean."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    nonzero = y_true != 0
    mape = np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100 if nonzero.any() else np.nan
    r2 = r2_score(y_true, y_pred)
    return {"MAE": mae, "RMSE": rmse, "MAPE_%": mape, "R2": r2}


# ---------------------------------------------------------------------------
# 3. CLASSIFICATION METRICS
# ---------------------------------------------------------------------------

def classification_metrics(y_true, y_pred, y_proba=None) -> dict:
    """Accuracy alone is misleading here since the "yes" class is rare in
    all 3 classifiers I built (lot rejections, failures etc. are like
    5-40% of the data depending on the model) -- a model that just
    predicts "no" every time would score high on accuracy and be
    completely useless. So I always look at precision/recall/F1 too, and
    ROC-AUC if I have probabilities."""
    metrics = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
    }
    if y_proba is not None:
        try:
            metrics["ROC_AUC"] = roc_auc_score(y_true, y_proba)
        except ValueError:
            metrics["ROC_AUC"] = np.nan
    return metrics


def print_classification_report(y_true, y_pred, target_names=("Negative", "Positive")):
    print(classification_report(y_true, y_pred, target_names=list(target_names), zero_division=0))
    print("Confusion matrix (rows=actual, cols=predicted):")
    print(pd.DataFrame(confusion_matrix(y_true, y_pred),
                        index=[f"Actual {n}" for n in target_names],
                        columns=[f"Predicted {n}" for n in target_names]))


# ---------------------------------------------------------------------------
# 4. SAVING/LOADING MODELS
# ---------------------------------------------------------------------------

def save_model(model, path: str, **metadata):
    """Saves the model plus some extra info (feature names, metrics) in
    the same pickle, so I can open it again later and remember what it
    actually was without digging through old notebook output."""
    joblib.dump({"model": model, "metadata": metadata}, path)


def load_model(path: str):
    bundle = joblib.load(path)
    return bundle["model"], bundle["metadata"]
