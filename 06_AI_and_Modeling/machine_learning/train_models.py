"""
CoralTwin-DT: Machine Learning Training Pipeline
================================================
Trains and cross-validates supervised predictive models (Random Forest,
XGBoost, Deep MLP, Regularized Linear/Logistic) for coral bleaching
risk classification and continuous cover loss regression.

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LogisticRegression, Ridge
import xgboost as xgb

SEED = 42
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "processed_data", "coral_environmental_harmonized.csv")
MODELS_DIR = os.path.join(BASE_DIR, "machine_learning", "saved_models")
EVAL_DIR = os.path.join(BASE_DIR, "model_evaluation")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EVAL_DIR, exist_ok=True)


def train_and_cross_validate():
    print("Loading data for model training...")
    df = pd.read_csv(DATA_PATH)

    features = [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
        "pH_total", "Aragonite_Saturation_Omega", "Turbidity_NTU",
        "PAR_umol_m2_s", "Structural_Rugosity", "Live_Coral_Cover_Pct"
    ]

    X = df[features].values
    y_class = df["Bleaching_Risk"].values
    y_reg = df["Coral_Cover_Loss_Pct"].values

    le = LabelEncoder()
    # Ensure consistent class ordering: Low=0, Medium=1, High=2
    le.fit(["Low", "Medium", "High"])
    y_class_enc = le.transform(y_class)

    # 5-Fold Spatially-Stratified / Cluster Split by Station
    stations = df["Station_Name"].unique()
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)

    classifiers = {
        "Random_Forest": RandomForestClassifier(n_estimators=250, max_depth=15, random_state=SEED, n_jobs=-1),
        "XGBoost": xgb.XGBClassifier(n_estimators=250, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=SEED, eval_metric="mlogloss"),
        "Deep_MLP": MLPClassifier(hidden_layer_sizes=(128, 64, 32), activation="relu", max_iter=200, random_state=SEED, early_stopping=True),
        "Logistic_Baseline": LogisticRegression(max_iter=500, random_state=SEED),
    }

    regressors = {
        "Random_Forest": RandomForestRegressor(n_estimators=250, max_depth=15, random_state=SEED, n_jobs=-1),
        "XGBoost": xgb.XGBRegressor(n_estimators=250, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=SEED),
        "Deep_MLP": MLPRegressor(hidden_layer_sizes=(128, 64, 32), activation="relu", max_iter=200, random_state=SEED, early_stopping=True),
        "Ridge_Baseline": Ridge(alpha=1.0, random_state=SEED),
    }

    cv_results = []
    oof_predictions = {name: np.zeros(len(df)) for name in classifiers}
    oof_probabilities = {name: np.zeros((len(df), 3)) for name in classifiers}
    oof_reg_predictions = {name: np.zeros(len(df)) for name in regressors}

    print("Executing 5-Fold Cross-Validation...")
    for fold, (train_st_idx, val_st_idx) in enumerate(kf.split(stations)):
        train_stations = stations[train_st_idx]
        val_stations = stations[val_st_idx]

        train_mask = df["Station_Name"].isin(train_stations).values
        val_mask = df["Station_Name"].isin(val_stations).values

        X_train, X_val = X[train_mask], X[val_mask]
        y_train_c, y_val_c = y_class_enc[train_mask], y_class_enc[val_mask]
        y_train_r, y_val_r = y_reg[train_mask], y_reg[val_mask]

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        for name, clf in classifiers.items():
            if name in ["Deep_MLP", "Logistic_Baseline"]:
                clf.fit(X_train_scaled, y_train_c)
                preds = clf.predict(X_val_scaled)
                probs = clf.predict_proba(X_val_scaled)
            else:
                clf.fit(X_train, y_train_c)
                preds = clf.predict(X_val)
                probs = clf.predict_proba(X_val)

            oof_predictions[name][val_mask] = preds
            oof_probabilities[name][val_mask] = probs

        for name, reg in regressors.items():
            if name in ["Deep_MLP", "Ridge_Baseline"]:
                reg.fit(X_train_scaled, y_train_r)
                preds_r = reg.predict(X_val_scaled)
            else:
                reg.fit(X_train, y_train_r)
                preds_r = reg.predict(X_val)

            oof_reg_predictions[name][val_mask] = preds_r

    # Train Final Production Models on full dataset
    scaler_full = StandardScaler()
    X_scaled_full = scaler_full.fit_transform(X)

    best_xgb_clf = classifiers["XGBoost"].fit(X, y_class_enc)
    best_xgb_reg = regressors["XGBoost"].fit(X, y_reg)
    best_rf_clf = classifiers["Random_Forest"].fit(X, y_class_enc)
    best_rf_reg = regressors["Random_Forest"].fit(X, y_reg)

    # Save artifacts
    joblib.dump(best_xgb_clf, os.path.join(MODELS_DIR, "xgboost_classifier.joblib"))
    joblib.dump(best_xgb_reg, os.path.join(MODELS_DIR, "xgboost_regressor.joblib"))
    joblib.dump(best_rf_clf, os.path.join(MODELS_DIR, "random_forest_classifier.joblib"))
    joblib.dump(best_rf_reg, os.path.join(MODELS_DIR, "random_forest_regressor.joblib"))
    joblib.dump(scaler_full, os.path.join(MODELS_DIR, "feature_scaler.joblib"))
    joblib.dump(le, os.path.join(MODELS_DIR, "label_encoder.joblib"))

    # Save out-of-fold predictions
    oof_df = pd.DataFrame({
        "Record_ID": df["Record_ID"],
        "True_Class": y_class_enc,
        "True_Loss_Pct": y_reg,
        "XGB_Class_Pred": oof_predictions["XGBoost"],
        "RF_Class_Pred": oof_predictions["Random_Forest"],
        "MLP_Class_Pred": oof_predictions["Deep_MLP"],
        "Baseline_Class_Pred": oof_predictions["Logistic_Baseline"],
        "XGB_Loss_Pred": oof_reg_predictions["XGBoost"],
        "RF_Loss_Pred": oof_reg_predictions["Random_Forest"],
        "MLP_Loss_Pred": oof_reg_predictions["Deep_MLP"],
        "Baseline_Loss_Pred": oof_reg_predictions["Ridge_Baseline"],
    })
    oof_df.to_csv(os.path.join(EVAL_DIR, "cross_validation_oof_predictions.csv"), index=False)
    print("Models trained and out-of-fold validation saved successfully.")


if __name__ == "__main__":
    train_and_cross_validate()
