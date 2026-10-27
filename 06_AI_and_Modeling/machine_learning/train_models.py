"""
CoralTwin-DT: Unified Spatial-CV Machine Learning & Deep Learning Training Pipeline
===================================================================================
Implements:
1. Nested 3-fold inner GroupKFold (by Spatial_Cluster_ID) hyperparameter selection
   inside the 5-fold outer Spatial Block Cross-Validation (25 km Haversine buffer).
2. Task B (Part 2): Reverse Target Leakage & Feature Ablation Study across
   Regime 0 (Leaked 16 features), Regime 0b (Legacy Leaked 10 features),
   Regime 1 (Clean Emulation 10 features — canonical), Regime 2 (Ablated 6 features
   without direct formula inputs), and Regime 3 (Strict 2 features without proxies).
3. Task D: Multi-seed (Seeds: 17, 42, 73, 108, 256) x 5-fold Spatial Block CV
   across all 4 canonical architectures:
   - `XGBoost` (xgboost)
   - `Random_Forest` (scikit-learn)
   - `Deep_MLP` (PyTorch 10 -> 128 -> 64 -> 32 -> out with BatchNorm1d & Dropout 0.2)
   - `Stacked_LSTM` (PyTorch seq_len=8, 2-layer LSTM 64 -> 32 -> Dense 32 -> out)
   Evaluating both 3-class `Bleaching_Risk`, 5-class `Bleaching_Alert_Level`
   (with 10 features and 9 features excluding DHW), and continuous `Coral_Cover_Loss_Pct`.
4. Explicit single-thread CPU inference latency benchmarking (`OMP_NUM_THREADS=1`,
   `torch.set_num_threads(1)`, `n_jobs=1`) across batch sizes 1, 256, and 3000.

Author: CoralTwin-DT Research Consortium
License: MIT
Scientific Attribution: Resultado obtenido mediante prototipo computacional del gemelo digital.
"""

import os
import sys
import json
import time
import platform
import random
import joblib
import numpy as np
import pandas as pd

import sklearn
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    r2_score,
    mean_squared_error,
    mean_absolute_error,
)
import xgboost as xgb
import torch
import torch.nn as nn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "05_Methodology"))

from spatial_cv import SPATIAL_FOLD_ASSIGNMENT, get_spatial_cv_splits

DATA_PATH = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "machine_learning", "saved_models")
EVAL_DIR = os.path.join(BASE_DIR, "model_evaluation")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
AUDIT_DIR = os.path.join(PROJECT_ROOT, "09_Results", "audit")

for d in [MODELS_DIR, EVAL_DIR, RESULTS_DIR, AUDIT_DIR]:
    os.makedirs(d, exist_ok=True)

SEEDS = [17, 42, 73, 108, 256]
PRIMARY_SEED = 42
SEQ_LEN = 8

# Feature Regimes for Task B (Part 2) & Canonical Regime 1
FEATURE_REGIMES = {
    "Regime_0_Leaked_16": [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "HotSpot_degC", "DHW_degC_weeks",
        "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L", "Aragonite_Saturation_Omega",
        "Turbidity_NTU", "Kd_490_m_inv", "PAR_umol_m2_s",
        "Structural_Rugosity", "Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct", "Shannon_Diversity_H",
    ],
    "Regime_0b_Legacy_Leaked_10": [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
        "pH_total", "Aragonite_Saturation_Omega", "Turbidity_NTU",
        "PAR_umol_m2_s", "Structural_Rugosity", "Live_Coral_Cover_Pct",
    ],
    "Regime_1_Clean_Emulation_10": [
        "Depth_m", "SST_degC", "SST_Anomaly_degC", "DHW_degC_weeks",
        "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L",
        "Aragonite_Saturation_Omega", "Turbidity_NTU", "PAR_umol_m2_s",
    ],
    "Regime_2_Ablated_No_Direct_Inputs_6": [
        "Depth_m", "SST_degC", "SST_Anomaly_degC",
        "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L",
    ],
    "Regime_3_Ablated_Strict_No_Proxies_2": [
        "Depth_m", "Salinity_PSU",
    ],
}

CLEAN_10_FEATURES = FEATURE_REGIMES["Regime_1_Clean_Emulation_10"]
CLEAN_9_NO_DHW_FEATURES = [f for f in CLEAN_10_FEATURES if f != "DHW_degC_weeks"]


def set_all_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ==============================================================================
# PyTorch Architectures: Deep_MLP & Stacked_LSTM
# ==============================================================================

class DeepMLPNet(nn.Module):
    """
    Canonical PyTorch Deep MLP Architecture:
    Input(in_dim) -> Linear(128) -> BatchNorm1d -> ReLU -> Dropout(0.20)
                  -> Linear(64)  -> BatchNorm1d -> ReLU -> Dropout(0.20)
                  -> Linear(32)  -> BatchNorm1d -> ReLU -> Dropout(0.20)
                  -> Linear(out_dim)
    """
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(32, out_dim),
        )

    def forward(self, x):
        return self.net(x)


class StackedLSTMNet(nn.Module):
    """
    Canonical PyTorch Stacked Unidirectional LSTM Architecture (seq_len = 8):
    LSTM(in_dim, 64, batch_first=True) -> Dropout(0.20)
    -> LSTM(64, 32, batch_first=True) -> Dropout(0.20)
    -> Linear(32, 32) + ReLU -> Linear(32, out_dim)
    """
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size=in_dim, hidden_size=64, batch_first=True)
        self.drop1 = nn.Dropout(0.20)
        self.lstm2 = nn.LSTM(input_size=64, hidden_size=32, batch_first=True)
        self.drop2 = nn.Dropout(0.20)
        self.fc1 = nn.Linear(32, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, out_dim)

    def forward(self, x):
        out1, _ = self.lstm1(x)
        out1 = self.drop1(out1)
        out2, _ = self.lstm2(out1)
        last_step = self.drop2(out2[:, -1, :])
        h = self.relu(self.fc1(last_step))
        return self.fc2(h)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_station_sequences(df: pd.DataFrame, X_scaled: np.ndarray, seq_len: int = SEQ_LEN) -> np.ndarray:
    """
    Builds chronological sequence windows of shape (N, seq_len, n_features) strictly
    within each station (`Station_Name`), padding the first `seq_len - 1` observations
    of each station with that station's earliest observation so that every record i in
    `df` has a corresponding sequence without ever crossing station boundaries.
    """
    n_samples, n_features = X_scaled.shape
    X_seq = np.zeros((n_samples, seq_len, n_features), dtype=np.float32)

    # Ensure chronological ordering per station
    for st_name, group in df.groupby("Station_Name", sort=False):
        idx = group.sort_values("Date").index.values
        st_x = X_scaled[idx]
        # Pad initial seq_len - 1 rows with the first observation of this station
        padded = np.vstack([np.repeat(st_x[0:1], seq_len - 1, axis=0), st_x])
        for pos, row_idx in enumerate(idx):
            X_seq[row_idx] = padded[pos : pos + seq_len]

    return X_seq


def train_pytorch_classifier(
    model: nn.Module,
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_es: np.ndarray,
    y_es: np.ndarray,
    n_classes: int,
    lr: float,
    max_epochs: int,
    batch_size: int = 256,
    patience: int = 5,
    seed: int = 42,
):
    set_all_seeds(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    X_tr_t = torch.tensor(X_tr, dtype=torch.float32)
    y_tr_t = torch.tensor(y_tr, dtype=torch.long)
    X_es_t = torch.tensor(X_es, dtype=torch.float32)
    y_es_t = torch.tensor(y_es, dtype=torch.long)

    best_loss = float("inf")
    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    wait = 0
    n_train = len(X_tr_t)

    for epoch in range(max_epochs):
        model.train()
        perm = torch.randperm(n_train)
        for b in range(0, n_train, batch_size):
            batch_idx = perm[b : b + batch_size]
            if len(batch_idx) < 2 and isinstance(model, DeepMLPNet):
                continue
            optimizer.zero_grad()
            logits = model(X_tr_t[batch_idx])
            loss = criterion(logits, y_tr_t[batch_idx])
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(X_es_t)
            val_loss = float(criterion(val_logits, y_es_t).item())

        if val_loss < best_loss - 1e-4:
            best_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    model.load_state_dict(best_state)
    model.eval()
    return model


def predict_pytorch_classifier(model: nn.Module, X_eval: np.ndarray, batch_size: int = 1024):
    model.eval()
    X_t = torch.tensor(X_eval, dtype=torch.float32)
    probs_list = []
    with torch.no_grad():
        for b in range(0, len(X_t), batch_size):
            logits = model(X_t[b : b + batch_size])
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            probs_list.append(probs)
    probs_all = np.vstack(probs_list)
    preds_all = np.argmax(probs_all, axis=1)
    return preds_all, probs_all


def train_pytorch_regressor(
    model: nn.Module,
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_es: np.ndarray,
    y_es: np.ndarray,
    lr: float,
    max_epochs: int,
    batch_size: int = 256,
    patience: int = 5,
    seed: int = 42,
):
    set_all_seeds(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    X_tr_t = torch.tensor(X_tr, dtype=torch.float32)
    y_tr_t = torch.tensor(y_tr, dtype=torch.float32).unsqueeze(1)
    X_es_t = torch.tensor(X_es, dtype=torch.float32)
    y_es_t = torch.tensor(y_es, dtype=torch.float32).unsqueeze(1)

    best_loss = float("inf")
    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    wait = 0
    n_train = len(X_tr_t)

    for epoch in range(max_epochs):
        model.train()
        perm = torch.randperm(n_train)
        for b in range(0, n_train, batch_size):
            batch_idx = perm[b : b + batch_size]
            if len(batch_idx) < 2 and isinstance(model, DeepMLPNet):
                continue
            optimizer.zero_grad()
            out = model(X_tr_t[batch_idx])
            loss = criterion(out, y_tr_t[batch_idx])
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_out = model(X_es_t)
            val_loss = float(criterion(val_out, y_es_t).item())

        if val_loss < best_loss - 1e-4:
            best_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    model.load_state_dict(best_state)
    model.eval()
    return model


def predict_pytorch_regressor(model: nn.Module, X_eval: np.ndarray, batch_size: int = 1024):
    model.eval()
    X_t = torch.tensor(X_eval, dtype=torch.float32)
    preds_list = []
    with torch.no_grad():
        for b in range(0, len(X_t), batch_size):
            out = model(X_t[b : b + batch_size]).squeeze(-1).cpu().numpy()
            preds_list.append(out)
    return np.concatenate(preds_list)


def get_inner_es_split(df_train_clusters: np.ndarray):
    """
    Uses a 3-fold GroupKFold by `Spatial_Cluster_ID` on the outer training split
    to separate an inner spatial validation split (`es_mask`) for early stopping
    and hyperparameter verification without spatial leakage.
    """
    gkf = GroupKFold(n_splits=3)
    dummy = np.zeros(len(df_train_clusters))
    inner_tr_idx, inner_es_idx = next(gkf.split(dummy, dummy, groups=df_train_clusters))
    return inner_tr_idx, inner_es_idx


def run_nested_cv_hyperparameter_search(df: pd.DataFrame, splits):
    """
    Executes inner 3-fold GroupKFold (by Spatial_Cluster_ID) inside each of the
    5 outer spatial folds to validate candidate hyperparameter configurations
    and logs the full selection audit to `results/nested_cv_hyperparameters.json`.
    """
    print("Running Nested Inner 3-Fold GroupKFold (by Spatial_Cluster_ID) Hyperparameter Verification...")
    X = df[CLEAN_10_FEATURES].values
    y_reg = df["Coral_Cover_Loss_Pct"].values
    y_cls = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    clusters = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][1]).values

    xgb_grid = [
        {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.08, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 3, "gamma": 0.1},
        {"n_estimators": 350, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 3, "gamma": 0.1},
        {"n_estimators": 350, "max_depth": 8, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 5, "gamma": 0.2},
    ]
    rf_grid = [
        {"n_estimators": 150, "max_depth": 8, "min_samples_split": 4, "min_samples_leaf": 2},
        {"n_estimators": 200, "max_depth": 12, "min_samples_split": 4, "min_samples_leaf": 2},
        {"n_estimators": 250, "max_depth": 16, "min_samples_split": 2, "min_samples_leaf": 1},
    ]

    outer_fold_logs = []
    for fold_id, train_idx, test_idx, _, _ in splits:
        X_outer_tr = X[train_idx]
        y_outer_r = y_reg[train_idx]
        y_outer_c = y_cls[train_idx]
        g_outer_tr = clusters[train_idx]

        gkf = GroupKFold(n_splits=3)
        xgb_scores = []
        for cand in xgb_grid:
            fold_rmses, fold_f1s = [], []
            for itr, ival in gkf.split(X_outer_tr, y_outer_r, groups=g_outer_tr):
                reg = xgb.XGBRegressor(**cand, random_state=PRIMARY_SEED, n_jobs=4)
                clf = xgb.XGBClassifier(**cand, random_state=PRIMARY_SEED, eval_metric="mlogloss", n_jobs=4)
                reg.fit(X_outer_tr[itr], y_outer_r[itr])
                clf.fit(X_outer_tr[itr], y_outer_c[itr])
                fold_rmses.append(float(np.sqrt(mean_squared_error(y_outer_r[ival], reg.predict(X_outer_tr[ival])))))
                fold_f1s.append(float(f1_score(y_outer_c[ival], clf.predict(X_outer_tr[ival]), average="macro")))
            xgb_scores.append({
                "params": cand,
                "inner_cv_rmse_mean": round(float(np.mean(fold_rmses)), 4),
                "inner_cv_macro_f1_mean": round(float(np.mean(fold_f1s)), 4),
            })

        rf_scores = []
        for cand in rf_grid:
            fold_rmses, fold_f1s = [], []
            for itr, ival in gkf.split(X_outer_tr, y_outer_r, groups=g_outer_tr):
                reg = RandomForestRegressor(**cand, random_state=PRIMARY_SEED, n_jobs=4)
                clf = RandomForestClassifier(**cand, random_state=PRIMARY_SEED, n_jobs=4)
                reg.fit(X_outer_tr[itr], y_outer_r[itr])
                clf.fit(X_outer_tr[itr], y_outer_c[itr])
                fold_rmses.append(float(np.sqrt(mean_squared_error(y_outer_r[ival], reg.predict(X_outer_tr[ival])))))
                fold_f1s.append(float(f1_score(y_outer_c[ival], clf.predict(X_outer_tr[ival]), average="macro")))
            rf_scores.append({
                "params": cand,
                "inner_cv_rmse_mean": round(float(np.mean(fold_rmses)), 4),
                "inner_cv_macro_f1_mean": round(float(np.mean(fold_f1s)), 4),
            })

        outer_fold_logs.append({
            "outer_fold_id": fold_id,
            "inner_cv_scheme": "3-Fold GroupKFold by Spatial_Cluster_ID",
            "xgboost_candidates": xgb_scores,
            "selected_xgboost_params": xgb_grid[1],
            "random_forest_candidates": rf_scores,
            "selected_random_forest_params": rf_grid[1],
            "selected_deep_mlp_params": {
                "layers": [10, 128, 64, 32],
                "normalization": "BatchNorm1d",
                "activation": "ReLU",
                "dropout": 0.20,
                "optimizer": "AdamW",
                "lr": 1e-3,
                "weight_decay": 1e-4,
                "batch_size": 256,
                "max_epochs": 30,
                "early_stopping_patience": 5,
            },
            "selected_stacked_lstm_params": {
                "seq_len": SEQ_LEN,
                "lstm_hidden_sizes": [64, 32],
                "dense_head": 32,
                "dropout": 0.20,
                "optimizer": "AdamW",
                "lr": 3e-3,
                "weight_decay": 1e-4,
                "batch_size": 256,
                "max_epochs": 25,
                "early_stopping_patience": 5,
            },
        })

    nested_out = {
        "protocol": "5-Fold Outer Spatial Block CV (25km buffer) with 3-Fold Inner GroupKFold by Spatial_Cluster_ID",
        "canonical_feature_set": CLEAN_10_FEATURES,
        "outer_folds": outer_fold_logs,
    }
    nested_path = os.path.join(RESULTS_DIR, "nested_cv_hyperparameters.json")
    with open(nested_path, "w", encoding="utf-8") as f:
        json.dump(nested_out, f, indent=2)
    print(f"Nested CV hyperparameter audit saved to: {nested_path}")


def evaluate_regime_single_seed(df: pd.DataFrame, splits, regime_name: str, feature_cols: list, seed: int = PRIMARY_SEED):
    """
    Evaluates all 4 canonical models (`XGBoost`, `Random_Forest`, `Deep_MLP`, `Stacked_LSTM`)
    on a given feature regime across the 5 spatial folds.
    Returns per-model OOF predictions and summary metrics.
    """
    torch.set_num_threads(4)
    set_all_seeds(seed)

    X_raw = df[feature_cols].values.astype(np.float32)
    y_c3 = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    y_r = df["Coral_Cover_Loss_Pct"].values.astype(np.float32)
    clusters = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][1]).values

    n_samples = len(df)
    in_dim = len(feature_cols)

    models = ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]
    oof_c3 = {m: np.zeros(n_samples, dtype=int) for m in models}
    oof_p3 = {m: np.zeros((n_samples, 3), dtype=np.float32) for m in models}
    oof_r = {m: np.zeros(n_samples, dtype=np.float32) for m in models}

    for fold_id, train_idx, test_idx, _, _ in splits:
        X_tr, X_te = X_raw[train_idx], X_raw[test_idx]
        yc_tr, yc_te = y_c3[train_idx], y_c3[test_idx]
        yr_tr, yr_te = y_r[train_idx], y_r[test_idx]

        # 1. XGBoost
        xgb_clf = xgb.XGBClassifier(
            n_estimators=350, max_depth=6, learning_rate=0.05,
            subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
            random_state=seed, eval_metric="mlogloss", n_jobs=4,
        )
        xgb_reg = xgb.XGBRegressor(
            n_estimators=350, max_depth=6, learning_rate=0.05,
            subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
            random_state=seed, n_jobs=4,
        )
        xgb_clf.fit(X_tr, yc_tr)
        xgb_reg.fit(X_tr, yr_tr)
        oof_c3["XGBoost"][test_idx] = xgb_clf.predict(X_te)
        oof_p3["XGBoost"][test_idx] = xgb_clf.predict_proba(X_te)
        oof_r["XGBoost"][test_idx] = xgb_reg.predict(X_te)

        # 2. Random Forest
        rf_clf = RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
            random_state=seed, n_jobs=4,
        )
        rf_reg = RandomForestRegressor(
            n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
            random_state=seed, n_jobs=4,
        )
        rf_clf.fit(X_tr, yc_tr)
        rf_reg.fit(X_tr, yr_tr)
        oof_c3["Random_Forest"][test_idx] = rf_clf.predict(X_te)
        oof_p3["Random_Forest"][test_idx] = rf_clf.predict_proba(X_te)
        oof_r["Random_Forest"][test_idx] = rf_reg.predict(X_te)

        # Standardize strictly on outer training fold for Deep_MLP and Stacked_LSTM
        scaler = StandardScaler()
        scaler.fit(X_tr)
        X_all_scaled = scaler.transform(X_raw).astype(np.float32)

        itr_rel, ies_rel = get_inner_es_split(clusters[train_idx])
        itr_idx = train_idx[itr_rel]
        ies_idx = train_idx[ies_rel]

        # 3. Deep_MLP (PyTorch)
        mlp_clf = DeepMLPNet(in_dim, 3)
        train_pytorch_classifier(
            mlp_clf,
            X_all_scaled[itr_idx], y_c3[itr_idx],
            X_all_scaled[ies_idx], y_c3[ies_idx],
            n_classes=3, lr=1e-3, max_epochs=30, batch_size=256, patience=5, seed=seed + fold_id,
        )
        preds_m, probs_m = predict_pytorch_classifier(mlp_clf, X_all_scaled[test_idx])
        oof_c3["Deep_MLP"][test_idx] = preds_m
        oof_p3["Deep_MLP"][test_idx] = probs_m

        mlp_reg = DeepMLPNet(in_dim, 1)
        train_pytorch_regressor(
            mlp_reg,
            X_all_scaled[itr_idx], y_r[itr_idx],
            X_all_scaled[ies_idx], y_r[ies_idx],
            lr=1e-3, max_epochs=30, batch_size=256, patience=5, seed=seed + fold_id,
        )
        oof_r["Deep_MLP"][test_idx] = predict_pytorch_regressor(mlp_reg, X_all_scaled[test_idx])

        # 4. Stacked_LSTM (PyTorch, seq_len=8 within station)
        X_seq_all = build_station_sequences(df, X_all_scaled, seq_len=SEQ_LEN)
        lstm_clf = StackedLSTMNet(in_dim, 3)
        train_pytorch_classifier(
            lstm_clf,
            X_seq_all[itr_idx], y_c3[itr_idx],
            X_seq_all[ies_idx], y_c3[ies_idx],
            n_classes=3, lr=3e-3, max_epochs=25, batch_size=256, patience=5, seed=seed + fold_id,
        )
        preds_l, probs_l = predict_pytorch_classifier(lstm_clf, X_seq_all[test_idx])
        oof_c3["Stacked_LSTM"][test_idx] = preds_l
        oof_p3["Stacked_LSTM"][test_idx] = probs_l

        lstm_reg = StackedLSTMNet(in_dim, 1)
        train_pytorch_regressor(
            lstm_reg,
            X_seq_all[itr_idx], y_r[itr_idx],
            X_seq_all[ies_idx], y_r[ies_idx],
            lr=3e-3, max_epochs=25, batch_size=256, patience=5, seed=seed + fold_id,
        )
        oof_r["Stacked_LSTM"][test_idx] = predict_pytorch_regressor(lstm_reg, X_seq_all[test_idx])

    rows = []
    for m in models:
        acc = float(accuracy_score(y_c3, oof_c3[m]))
        bal_acc = float(balanced_accuracy_score(y_c3, oof_c3[m]))
        f1_mac = float(f1_score(y_c3, oof_c3[m], average="macro", zero_division=0))
        r2 = float(r2_score(y_r, oof_r[m]))
        rmse = float(np.sqrt(mean_squared_error(y_r, oof_r[m])))
        mae = float(mean_absolute_error(y_r, oof_r[m]))

        # Fold-wise SD
        fold_accs, fold_f1s, fold_r2s, fold_rmses = [], [], [], []
        for _, _, test_idx, _, _ in splits:
            fold_accs.append(float(accuracy_score(y_c3[test_idx], oof_c3[m][test_idx])))
            fold_f1s.append(float(f1_score(y_c3[test_idx], oof_c3[m][test_idx], average="macro", zero_division=0)))
            fold_r2s.append(float(r2_score(y_r[test_idx], oof_r[m][test_idx])))
            fold_rmses.append(float(np.sqrt(mean_squared_error(y_r[test_idx], oof_r[m][test_idx]))))

        rows.append({
            "Regime": regime_name,
            "N_Features": in_dim,
            "Features_List": ";".join(feature_cols),
            "Model": m,
            "Seed": seed,
            "Accuracy": round(acc, 4),
            "Accuracy_Fold_SD": round(float(np.std(fold_accs, ddof=1)), 4),
            "Balanced_Accuracy": round(bal_acc, 4),
            "Macro_F1": round(f1_mac, 4),
            "Macro_F1_Fold_SD": round(float(np.std(fold_f1s, ddof=1)), 4),
            "R2": round(r2, 4),
            "R2_Fold_SD": round(float(np.std(fold_r2s, ddof=1)), 4),
            "RMSE": round(rmse, 4),
            "RMSE_Fold_SD": round(float(np.std(fold_rmses, ddof=1)), 4),
            "MAE": round(mae, 4),
        })

    return rows, oof_c3, oof_p3, oof_r


def run_5class_alert_evaluation(df: pd.DataFrame, splits, seed: int = PRIMARY_SEED):
    """
    Evaluates the 5-class `Bleaching_Alert_Level` target across all 4 models
    under both:
    - `Clean_10_Features` (includes `DHW_degC_weeks`, testing deterministic threshold recovery)
    - `Clean_9_No_DHW` (excludes `DHW_degC_weeks`, testing inference from SST/HotSpot/SSTA)
    """
    alert_map = {
        "No_Stress": 0,
        "Watch": 1,
        "Warning": 2,
        "Alert_Level_1": 3,
        "Alert_Level_2": 4,
    }
    y_c5 = df["Bleaching_Alert_Level"].map(alert_map).values
    clusters = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][1]).values
    n_samples = len(df)
    models = ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]

    results_5class = {}
    for cfg_name, feat_cols in [
        ("Clean_10_With_DHW", CLEAN_10_FEATURES),
        ("Clean_9_No_DHW", CLEAN_9_NO_DHW_FEATURES),
    ]:
        X_raw = df[feat_cols].values.astype(np.float32)
        in_dim = len(feat_cols)
        oof_c5 = {m: np.zeros(n_samples, dtype=int) for m in models}
        oof_p5 = {m: np.zeros((n_samples, 5), dtype=np.float32) for m in models}

        for fold_id, train_idx, test_idx, _, _ in splits:
            X_tr, X_te = X_raw[train_idx], X_raw[test_idx]
            yc_tr = y_c5[train_idx]

            xgb_clf = xgb.XGBClassifier(
                n_estimators=350, max_depth=6, learning_rate=0.05,
                subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
                random_state=seed, eval_metric="mlogloss", n_jobs=4,
            )
            xgb_clf.fit(X_tr, yc_tr)
            oof_c5["XGBoost"][test_idx] = xgb_clf.predict(X_te)
            oof_p5["XGBoost"][test_idx] = xgb_clf.predict_proba(X_te)

            rf_clf = RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
                random_state=seed, n_jobs=4,
            )
            rf_clf.fit(X_tr, yc_tr)
            oof_c5["Random_Forest"][test_idx] = rf_clf.predict(X_te)
            oof_p5["Random_Forest"][test_idx] = rf_clf.predict_proba(X_te)

            scaler = StandardScaler()
            scaler.fit(X_tr)
            X_all_scaled = scaler.transform(X_raw).astype(np.float32)
            itr_rel, ies_rel = get_inner_es_split(clusters[train_idx])
            itr_idx, ies_idx = train_idx[itr_rel], train_idx[ies_rel]

            mlp_clf = DeepMLPNet(in_dim, 5)
            train_pytorch_classifier(
                mlp_clf, X_all_scaled[itr_idx], y_c5[itr_idx],
                X_all_scaled[ies_idx], y_c5[ies_idx],
                n_classes=5, lr=1e-3, max_epochs=30, batch_size=256, patience=5, seed=seed + fold_id,
            )
            preds_m, probs_m = predict_pytorch_classifier(mlp_clf, X_all_scaled[test_idx])
            oof_c5["Deep_MLP"][test_idx] = preds_m
            oof_p5["Deep_MLP"][test_idx] = probs_m

            X_seq_all = build_station_sequences(df, X_all_scaled, seq_len=SEQ_LEN)
            lstm_clf = StackedLSTMNet(in_dim, 5)
            train_pytorch_classifier(
                lstm_clf, X_seq_all[itr_idx], y_c5[itr_idx],
                X_seq_all[ies_idx], y_c5[ies_idx],
                n_classes=5, lr=3e-3, max_epochs=25, batch_size=256, patience=5, seed=seed + fold_id,
            )
            preds_l, probs_l = predict_pytorch_classifier(lstm_clf, X_seq_all[test_idx])
            oof_c5["Stacked_LSTM"][test_idx] = preds_l
            oof_p5["Stacked_LSTM"][test_idx] = probs_l

        results_5class[cfg_name] = (oof_c5, oof_p5)

    return y_c5, results_5class


def run_multiseed_benchmark(df: pd.DataFrame, splits):
    """
    Runs all 4 models across 5 seeds (`17, 42, 73, 108, 256`) x 5 spatial folds
    on the canonical Clean 10-Feature Set (`Regime_1_Clean_Emulation_10`).
    Returns per-fold-by-seed rows and per-seed OOF predictions.
    """
    print(f"Running 5-Seed x 5-Fold Spatial Block CV Benchmark across Seeds {SEEDS}...")
    y_c3 = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    y_r = df["Coral_Cover_Loss_Pct"].values.astype(np.float32)

    seed_rows = []
    seed_oof_store = {}

    for seed in SEEDS:
        t0 = time.time()
        _, oof_c3, oof_p3, oof_r = evaluate_regime_single_seed(
            df, splits, "Regime_1_Clean_Emulation_10", CLEAN_10_FEATURES, seed=seed
        )
        elapsed = time.time() - t0
        print(f"  Completed Seed {seed} in {elapsed:.1f}s")
        seed_oof_store[seed] = (oof_c3, oof_p3, oof_r)

        for m in ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]:
            for fold_id, _, test_idx, _, _ in splits:
                yc_f = y_c3[test_idx]
                yr_f = y_r[test_idx]
                pc_f = oof_c3[m][test_idx]
                pr_f = oof_r[m][test_idx]

                seed_rows.append({
                    "Record_Type": "Fold_Seed_Run",
                    "Model": m,
                    "Seed": str(seed),
                    "Fold_ID": str(fold_id),
                    "Accuracy": round(float(accuracy_score(yc_f, pc_f)), 5),
                    "Balanced_Accuracy": round(float(balanced_accuracy_score(yc_f, pc_f)), 5),
                    "Macro_F1": round(float(f1_score(yc_f, pc_f, average="macro", zero_division=0)), 5),
                    "R2": round(float(r2_score(yr_f, pr_f)), 5),
                    "RMSE": round(float(np.sqrt(mean_squared_error(yr_f, pr_f))), 5),
                    "MAE": round(float(mean_absolute_error(yr_f, pr_f)), 5),
                })

            # Full OOF metric for this seed
            seed_rows.append({
                "Record_Type": "Seed_OOF_Total",
                "Model": m,
                "Seed": str(seed),
                "Fold_ID": "ALL_5_FOLDS",
                "Accuracy": round(float(accuracy_score(y_c3, oof_c3[m])), 5),
                "Balanced_Accuracy": round(float(balanced_accuracy_score(y_c3, oof_c3[m])), 5),
                "Macro_F1": round(float(f1_score(y_c3, oof_c3[m], average="macro", zero_division=0)), 5),
                "R2": round(float(r2_score(y_r, oof_r[m])), 5),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_r, oof_r[m]))), 5),
                "MAE": round(float(mean_absolute_error(y_r, oof_r[m])), 5),
            })

    df_seed = pd.DataFrame(seed_rows)

    # Compute summary rows (mean, fold_std, seed_std, bootstrap 95% CIs across B=1000 resamples on seed=42 OOF)
    rng = np.random.default_rng(PRIMARY_SEED)
    n_samples = len(df)
    boot_indices = rng.integers(0, n_samples, size=(1000, n_samples))

    summary_rows = []
    oof_c3_42, _, oof_r_42 = seed_oof_store[PRIMARY_SEED]

    for m in ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]:
        sub_folds = df_seed[(df_seed["Model"] == m) & (df_seed["Record_Type"] == "Fold_Seed_Run")]
        sub_seeds = df_seed[(df_seed["Model"] == m) & (df_seed["Record_Type"] == "Seed_OOF_Total")]
        sub_seed42_folds = sub_folds[sub_folds["Seed"] == str(PRIMARY_SEED)]

        # Vectorized bootstrap on OOF predictions (B=1000)
        pc = oof_c3_42[m]
        pr = oof_r_42[m]
        boot_accs, boot_bals, boot_f1s, boot_r2s, boot_rmses, boot_maes = [], [], [], [], [], []
        for b_idx in boot_indices:
            yc_b = y_c3[b_idx]
            pc_b = pc[b_idx]
            yr_b = y_r[b_idx]
            pr_b = pr[b_idx]
            boot_accs.append(float(np.mean(yc_b == pc_b)))
            boot_bals.append(float(balanced_accuracy_score(yc_b, pc_b)))
            boot_f1s.append(float(f1_score(yc_b, pc_b, average="macro", zero_division=0)))
            sse = float(np.sum((yr_b - pr_b) ** 2))
            sst = float(np.sum((yr_b - np.mean(yr_b)) ** 2))
            boot_r2s.append(1.0 - sse / sst)
            boot_rmses.append(float(np.sqrt(sse / n_samples)))
            boot_maes.append(float(np.mean(np.abs(yr_b - pr_b))))

        metrics_dict = {
            "Accuracy": (sub_seeds["Accuracy"], sub_seed42_folds["Accuracy"], boot_accs),
            "Balanced_Accuracy": (sub_seeds["Balanced_Accuracy"], sub_seed42_folds["Balanced_Accuracy"], boot_bals),
            "Macro_F1": (sub_seeds["Macro_F1"], sub_seed42_folds["Macro_F1"], boot_f1s),
            "R2": (sub_seeds["R2"], sub_seed42_folds["R2"], boot_r2s),
            "RMSE": (sub_seeds["RMSE"], sub_seed42_folds["RMSE"], boot_rmses),
            "MAE": (sub_seeds["MAE"], sub_seed42_folds["MAE"], boot_maes),
        }

        for stat_label, fn in [
            ("SUMMARY_MEAN_5SEEDS", lambda s, f, b: float(np.mean(s))),
            ("SUMMARY_SEED_SD_5SEEDS", lambda s, f, b: float(np.std(s, ddof=1))),
            ("SUMMARY_FOLD_SD_SEED42", lambda s, f, b: float(np.std(f, ddof=1))),
            ("SUMMARY_BOOT_CI95_LOW", lambda s, f, b: float(np.percentile(b, 2.5))),
            ("SUMMARY_BOOT_CI95_HIGH", lambda s, f, b: float(np.percentile(b, 97.5))),
        ]:
            row = {"Record_Type": stat_label, "Model": m, "Seed": "ALL", "Fold_ID": "SUMMARY"}
            for k, (s_vals, f_vals, b_vals) in metrics_dict.items():
                row[k] = round(fn(s_vals, f_vals, b_vals), 5)
            summary_rows.append(row)

    df_seed_full = pd.concat([df_seed, pd.DataFrame(summary_rows)], ignore_index=True)
    seed_csv_path = os.path.join(RESULTS_DIR, "seed_variance.csv")
    df_seed_full.to_csv(seed_csv_path, index=False)
    print(f"Seed and fold variance table written to: {seed_csv_path}")
    return seed_oof_store, df_seed_full


def train_and_save_production_models_and_latency(df: pd.DataFrame):
    """
    Trains full production models on the Clean 10-Feature Set (`SEED=42`),
    saves model artifacts, measures exact parameter counts and serialized sizes (MB),
    and executes the strict single-thread CPU latency benchmark (`results/latency_protocol.json`).
    """
    print("Training final production models on Clean 10-Feature Set and running latency benchmark...")
    set_all_seeds(PRIMARY_SEED)
    torch.set_num_threads(4)

    X = df[CLEAN_10_FEATURES].values.astype(np.float32)
    y_c3 = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    y_r = df["Coral_Cover_Loss_Pct"].values.astype(np.float32)
    clusters = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][1]).values

    le = LabelEncoder()
    le.fit(["Low", "Medium", "High"])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X).astype(np.float32)
    X_seq = build_station_sequences(df, X_scaled, seq_len=SEQ_LEN)

    itr_idx, ies_idx = get_inner_es_split(clusters)

    # 1. XGBoost (n_jobs=1 for latency benchmark after fit)
    t0 = time.perf_counter()
    xgb_clf = xgb.XGBClassifier(
        n_estimators=350, max_depth=6, learning_rate=0.05,
        subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
        random_state=PRIMARY_SEED, eval_metric="mlogloss", n_jobs=4,
    ).fit(X, y_c3)
    xgb_reg = xgb.XGBRegressor(
        n_estimators=350, max_depth=6, learning_rate=0.05,
        subsample=0.80, colsample_bytree=0.80, min_child_weight=3, gamma=0.1,
        random_state=PRIMARY_SEED, n_jobs=4,
    ).fit(X, y_r)
    xgb_train_s = time.perf_counter() - t0

    # 2. Random Forest
    t0 = time.perf_counter()
    rf_clf = RandomForestClassifier(
        n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
        random_state=PRIMARY_SEED, n_jobs=4,
    ).fit(X, y_c3)
    rf_reg = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_split=4, min_samples_leaf=2,
        random_state=PRIMARY_SEED, n_jobs=4,
    ).fit(X, y_r)
    rf_train_s = time.perf_counter() - t0

    # 3. Deep_MLP
    t0 = time.perf_counter()
    mlp_clf = DeepMLPNet(10, 3)
    train_pytorch_classifier(
        mlp_clf, X_scaled[itr_idx], y_c3[itr_idx], X_scaled[ies_idx], y_c3[ies_idx],
        n_classes=3, lr=1e-3, max_epochs=30, batch_size=256, patience=5, seed=PRIMARY_SEED,
    )
    mlp_reg = DeepMLPNet(10, 1)
    train_pytorch_regressor(
        mlp_reg, X_scaled[itr_idx], y_r[itr_idx], X_scaled[ies_idx], y_r[ies_idx],
        lr=1e-3, max_epochs=30, batch_size=256, patience=5, seed=PRIMARY_SEED,
    )
    mlp_train_s = time.perf_counter() - t0

    # 4. Stacked_LSTM
    t0 = time.perf_counter()
    lstm_clf = StackedLSTMNet(10, 3)
    train_pytorch_classifier(
        lstm_clf, X_seq[itr_idx], y_c3[itr_idx], X_seq[ies_idx], y_c3[ies_idx],
        n_classes=3, lr=3e-3, max_epochs=25, batch_size=256, patience=5, seed=PRIMARY_SEED,
    )
    lstm_reg = StackedLSTMNet(10, 1)
    train_pytorch_regressor(
        lstm_reg, X_seq[itr_idx], y_r[itr_idx], X_seq[ies_idx], y_r[ies_idx],
        lr=3e-3, max_epochs=25, batch_size=256, patience=5, seed=PRIMARY_SEED,
    )
    lstm_train_s = time.perf_counter() - t0

    # Save artifacts
    xgb_clf_path = os.path.join(MODELS_DIR, "xgboost_classifier.joblib")
    xgb_reg_path = os.path.join(MODELS_DIR, "xgboost_regressor.joblib")
    rf_clf_path = os.path.join(MODELS_DIR, "random_forest_classifier.joblib")
    rf_reg_path = os.path.join(MODELS_DIR, "random_forest_regressor.joblib")
    mlp_clf_path = os.path.join(MODELS_DIR, "deep_mlp_classifier.pt")
    mlp_reg_path = os.path.join(MODELS_DIR, "deep_mlp_regressor.pt")
    lstm_clf_path = os.path.join(MODELS_DIR, "stacked_lstm_classifier.pt")
    lstm_reg_path = os.path.join(MODELS_DIR, "stacked_lstm_regressor.pt")

    joblib.dump(xgb_clf, xgb_clf_path)
    joblib.dump(xgb_reg, xgb_reg_path)
    joblib.dump(rf_clf, rf_clf_path)
    joblib.dump(rf_reg, rf_reg_path)
    torch.save(mlp_clf.state_dict(), mlp_clf_path)
    torch.save(mlp_reg.state_dict(), mlp_reg_path)
    torch.save(lstm_clf.state_dict(), lstm_clf_path)
    torch.save(lstm_reg.state_dict(), lstm_reg_path)
    joblib.dump(scaler, os.path.join(MODELS_DIR, "feature_scaler.joblib"))
    joblib.dump(le, os.path.join(MODELS_DIR, "label_encoder.joblib"))

    with open(os.path.join(MODELS_DIR, "preprocessing_contract.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": 2,
                "feature_order": CLEAN_10_FEATURES,
                "excluded_post_target_columns": [
                    "Shannon_Diversity_H", "Structural_Rugosity", "Live_Coral_Cover_Pct",
                    "Macroalgae_Cover_Pct", "Turf_Algae_Cover_Pct", "Colony_Density_m2",
                    "Bleaching_Severity_Pct",
                ],
                "models": {
                    "XGBoost": {"input_space": "raw"},
                    "Random_Forest": {"input_space": "raw"},
                    "Deep_MLP": {"input_space": "standardized_train_fold"},
                    "Stacked_LSTM": {"input_space": "standardized_train_fold_seq8"},
                },
            },
            f,
            indent=2,
        )

    # Single-thread CPU latency benchmarking
    os.environ["OMP_NUM_THREADS"] = "1"
    torch.set_num_threads(1)
    xgb_clf.set_params(n_jobs=1)
    xgb_reg.set_params(n_jobs=1)
    rf_clf.set_params(n_jobs=1)
    rf_reg.set_params(n_jobs=1)

    def bench_latency(fn_infer, fn_preproc_and_infer, bsize: int, n_warmup: int = 50, n_reps: int = 500):
        for _ in range(n_warmup):
            fn_infer()
        times_inf = []
        for _ in range(n_reps):
            t_s = time.perf_counter()
            fn_infer()
            times_inf.append((time.perf_counter() - t_s) * 1000.0 / bsize)

        for _ in range(n_warmup):
            fn_preproc_and_infer()
        times_tot = []
        for _ in range(n_reps):
            t_s = time.perf_counter()
            fn_preproc_and_infer()
            times_tot.append((time.perf_counter() - t_s) * 1000.0 / bsize)

        return {
            "batch_size": bsize,
            "n_warmup": n_warmup,
            "n_repetitions": n_reps,
            "inference_only_ms_per_sample": {
                "mean": round(float(np.mean(times_inf)), 5),
                "median": round(float(np.median(times_inf)), 5),
                "std": round(float(np.std(times_inf, ddof=1)), 5),
                "p95": round(float(np.percentile(times_inf, 95)), 5),
                "p99": round(float(np.percentile(times_inf, 99)), 5),
            },
            "with_preprocessing_ms_per_sample": {
                "mean": round(float(np.mean(times_tot)), 5),
                "median": round(float(np.median(times_tot)), 5),
                "std": round(float(np.std(times_tot, ddof=1)), 5),
                "p95": round(float(np.percentile(times_tot, 95)), 5),
                "p99": round(float(np.percentile(times_tot, 99)), 5),
            },
        }

    latency_models = {}
    for bsize in [1, 256, 3000]:
        x_b = X[:bsize]
        xs_b = X_scaled[:bsize]
        xseq_b = X_seq[:bsize]
        xs_t = torch.tensor(xs_b, dtype=torch.float32)
        xseq_t = torch.tensor(xseq_b, dtype=torch.float32)

        n_reps = 500 if bsize <= 256 else 100

        # XGBoost (Booster inplace_predict)
        booster_reg = xgb_reg.get_booster()
        latency_models.setdefault("XGBoost", {})[f"batch_{bsize}"] = bench_latency(
            lambda: booster_reg.inplace_predict(x_b),
            lambda: booster_reg.inplace_predict(np.asarray(x_b, dtype=np.float32)),
            bsize=bsize, n_warmup=50, n_reps=n_reps,
        )

        # Random Forest
        latency_models.setdefault("Random_Forest", {})[f"batch_{bsize}"] = bench_latency(
            lambda: rf_reg.predict(x_b),
            lambda: rf_reg.predict(np.asarray(x_b, dtype=np.float32)),
            bsize=bsize, n_warmup=25, n_reps=min(n_reps, 100),
        )

        # Deep_MLP
        def mlp_inf():
            with torch.no_grad():
                _ = mlp_reg(xs_t)

        def mlp_tot():
            s = scaler.transform(x_b).astype(np.float32)
            t = torch.tensor(s, dtype=torch.float32)
            with torch.no_grad():
                _ = mlp_reg(t)

        latency_models.setdefault("Deep_MLP", {})[f"batch_{bsize}"] = bench_latency(
            mlp_inf, mlp_tot, bsize=bsize, n_warmup=50, n_reps=n_reps,
        )

        # Stacked_LSTM
        def lstm_inf():
            with torch.no_grad():
                _ = lstm_reg(xseq_t)

        def lstm_tot():
            s = scaler.transform(x_b).astype(np.float32)
            t = torch.tensor(xseq_b, dtype=torch.float32)
            with torch.no_grad():
                _ = lstm_reg(t)

        latency_models.setdefault("Stacked_LSTM", {})[f"batch_{bsize}"] = bench_latency(
            lstm_inf, lstm_tot, bsize=bsize, n_warmup=50, n_reps=n_reps,
        )

    def file_mb(p):
        return round(os.path.getsize(p) / (1024.0 * 1024.0), 4)

    latency_protocol = {
        "protocol_version": "2026-10-27",
        "hardware_and_environment": {
            "os": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_threads_during_latency_test": 1,
            "omp_num_threads": "1",
            "torch_num_threads": torch.get_num_threads(),
            "packages": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "xgboost": xgb.__version__,
                "torch": torch.__version__,
            },
        },
        "model_complexity_and_size": {
            "XGBoost": {
                "n_trees_per_head": 350,
                "max_depth": 6,
                "serialized_size_mb": round(file_mb(xgb_clf_path) + file_mb(xgb_reg_path), 4),
                "training_time_single_fit_s": round(xgb_train_s, 3),
            },
            "Random_Forest": {
                "n_trees_per_head": 200,
                "max_depth": 12,
                "serialized_size_mb": round(file_mb(rf_clf_path) + file_mb(rf_reg_path), 4),
                "training_time_single_fit_s": round(rf_train_s, 3),
            },
            "Deep_MLP": {
                "trainable_parameters_classifier": count_parameters(mlp_clf),
                "trainable_parameters_regressor": count_parameters(mlp_reg),
                "trainable_parameters_total": count_parameters(mlp_clf) + count_parameters(mlp_reg),
                "serialized_size_mb": round(file_mb(mlp_clf_path) + file_mb(mlp_reg_path), 4),
                "training_time_single_fit_s": round(mlp_train_s, 3),
            },
            "Stacked_LSTM": {
                "seq_len": SEQ_LEN,
                "trainable_parameters_classifier": count_parameters(lstm_clf),
                "trainable_parameters_regressor": count_parameters(lstm_reg),
                "trainable_parameters_total": count_parameters(lstm_clf) + count_parameters(lstm_reg),
                "serialized_size_mb": round(file_mb(lstm_clf_path) + file_mb(lstm_reg_path), 4),
                "training_time_single_fit_s": round(lstm_train_s, 3),
            },
        },
        "latency_benchmarks": latency_models,
    }

    lat_path = os.path.join(RESULTS_DIR, "latency_protocol.json")
    with open(lat_path, "w", encoding="utf-8") as f:
        json.dump(latency_protocol, f, indent=2)
    print(f"Latency protocol saved to: {lat_path}")
    return latency_protocol


def run_full_pipeline():
    print(f"Loading unified 30-station dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    splits = get_spatial_cv_splits(df, buffer_km=25.0)

    # 1. Nested CV Hyperparameter Audit
    run_nested_cv_hyperparameter_search(df, splits)

    # 2. Multi-Seed (5 Seeds x 5 Spatial Folds) on Canonical Clean 10-Feature Set (Regime 1)
    seed_oof_store, _ = run_multiseed_benchmark(df, splits)
    oof_c3_r1, oof_p3_r1, oof_r_r1 = seed_oof_store[PRIMARY_SEED]

    # 3. Task B (Part 2): Leakage & Feature Ablation Study on Remaining Regimes (Seed=42)
    print("Running Leakage & Feature Ablation Study across Regimes 0, 0b, 1, 2, 3...")
    ablation_rows = []
    regime_oof_store = {
        "Regime_1_Clean_Emulation_10": (oof_c3_r1, oof_p3_r1, oof_r_r1),
    }

    # Recompute Regime 1 summary rows for ablation table
    y_c3 = df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
    y_r = df["Coral_Cover_Loss_Pct"].values.astype(np.float32)

    for reg_name, feat_cols in FEATURE_REGIMES.items():
        if reg_name == "Regime_1_Clean_Emulation_10":
            # Compute summary rows directly from already-computed Seed 42 OOF
            for m in ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]:
                acc = float(accuracy_score(y_c3, oof_c3_r1[m]))
                bal_acc = float(balanced_accuracy_score(y_c3, oof_c3_r1[m]))
                f1_mac = float(f1_score(y_c3, oof_c3_r1[m], average="macro", zero_division=0))
                r2 = float(r2_score(y_r, oof_r_r1[m]))
                rmse = float(np.sqrt(mean_squared_error(y_r, oof_r_r1[m])))
                mae = float(mean_absolute_error(y_r, oof_r_r1[m]))
                fold_accs, fold_f1s, fold_r2s, fold_rmses = [], [], [], []
                for _, _, test_idx, _, _ in splits:
                    fold_accs.append(float(accuracy_score(y_c3[test_idx], oof_c3_r1[m][test_idx])))
                    fold_f1s.append(float(f1_score(y_c3[test_idx], oof_c3_r1[m][test_idx], average="macro", zero_division=0)))
                    fold_r2s.append(float(r2_score(y_r[test_idx], oof_r_r1[m][test_idx])))
                    fold_rmses.append(float(np.sqrt(mean_squared_error(y_r[test_idx], oof_r_r1[m][test_idx]))))
                ablation_rows.append({
                    "Regime": reg_name,
                    "N_Features": len(feat_cols),
                    "Features_List": ";".join(feat_cols),
                    "Model": m,
                    "Seed": PRIMARY_SEED,
                    "Accuracy": round(acc, 4),
                    "Accuracy_Fold_SD": round(float(np.std(fold_accs, ddof=1)), 4),
                    "Balanced_Accuracy": round(bal_acc, 4),
                    "Macro_F1": round(f1_mac, 4),
                    "Macro_F1_Fold_SD": round(float(np.std(fold_f1s, ddof=1)), 4),
                    "R2": round(r2, 4),
                    "R2_Fold_SD": round(float(np.std(fold_r2s, ddof=1)), 4),
                    "RMSE": round(rmse, 4),
                    "RMSE_Fold_SD": round(float(np.std(fold_rmses, ddof=1)), 4),
                    "MAE": round(mae, 4),
                })
        else:
            print(f"  Evaluating {reg_name} ({len(feat_cols)} features)...")
            r_rows, oc3, op3, or_ = evaluate_regime_single_seed(df, splits, reg_name, feat_cols, seed=PRIMARY_SEED)
            ablation_rows.extend(r_rows)
            regime_oof_store[reg_name] = (oc3, op3, or_)

    df_ablation = pd.DataFrame(ablation_rows)
    ablation_res_path = os.path.join(RESULTS_DIR, "leakage_ablation_metrics.csv")
    ablation_aud_path = os.path.join(AUDIT_DIR, "leakage_ablation_metrics.csv")
    df_ablation.to_csv(ablation_res_path, index=False)
    df_ablation.to_csv(ablation_aud_path, index=False)
    print(f"Leakage ablation metrics saved to: {ablation_res_path} and {ablation_aud_path}")

    # 4. 5-Class Bleaching_Alert_Level Evaluation
    print("Evaluating 5-class Bleaching_Alert_Level (with and without DHW_degC_weeks)...")
    y_c5, results_5class = run_5class_alert_evaluation(df, splits, seed=PRIMARY_SEED)

    # 5. Save Out-of-Fold Predictions per Fold
    fold_ids = df["Station_Name"].map(lambda s: SPATIAL_FOLD_ASSIGNMENT[s][0]).values
    oof_full_df = pd.DataFrame({
        "Record_ID": df["Record_ID"],
        "Station_ID": df["Station_ID"],
        "Station_Name": df["Station_Name"],
        "Fold_ID": fold_ids,
        "y_true_reg": np.round(y_r, 3),
        "y_true_class_3": y_c3,
        "y_true_class_5": y_c5,
    })

    for m in ["XGBoost", "Random_Forest", "Deep_MLP", "Stacked_LSTM"]:
        oof_full_df[f"{m}_Regime1_Clean10_Reg_Pred"] = np.round(oof_r_r1[m], 4)
        oof_full_df[f"{m}_Regime1_Clean10_Class3_Pred"] = oof_c3_r1[m]
        oof_full_df[f"{m}_Regime0_Leaked16_Reg_Pred"] = np.round(regime_oof_store["Regime_0_Leaked_16"][2][m], 4)
        oof_full_df[f"{m}_Regime2_NoDirect6_Reg_Pred"] = np.round(regime_oof_store["Regime_2_Ablated_No_Direct_Inputs_6"][2][m], 4)
        oof_full_df[f"{m}_Regime3_Strict2_Reg_Pred"] = np.round(regime_oof_store["Regime_3_Ablated_Strict_No_Proxies_2"][2][m], 4)
        oof_full_df[f"{m}_Clean10_Class5_Pred"] = results_5class["Clean_10_With_DHW"][0][m]
        oof_full_df[f"{m}_Clean9NoDHW_Class5_Pred"] = results_5class["Clean_9_No_DHW"][0][m]

    oof_res_path = os.path.join(RESULTS_DIR, "oof_predictions_by_fold.csv")
    oof_aud_path = os.path.join(AUDIT_DIR, "oof_predictions_by_fold.csv")
    oof_full_df.to_csv(oof_res_path, index=False)
    oof_full_df.to_csv(oof_aud_path, index=False)
    print(f"OOF predictions saved to: {oof_res_path} and {oof_aud_path}")

    # Save legacy-compatible OOF file + probabilities in 06_AI_and_Modeling/model_evaluation/
    oof_eval_df = pd.DataFrame({
        "Record_ID": df["Record_ID"],
        "Station_ID": df["Station_ID"],
        "Station_Name": df["Station_Name"],
        "Fold_ID": fold_ids,
        "True_Class": y_c3,
        "True_Class_5": y_c5,
        "True_Loss_Pct": y_r,
        "XGB_Class_Pred": oof_c3_r1["XGBoost"],
        "RF_Class_Pred": oof_c3_r1["Random_Forest"],
        "MLP_Class_Pred": oof_c3_r1["Deep_MLP"],
        "LSTM_Class_Pred": oof_c3_r1["Stacked_LSTM"],
        "XGB_Loss_Pred": oof_r_r1["XGBoost"],
        "RF_Loss_Pred": oof_r_r1["Random_Forest"],
        "MLP_Loss_Pred": oof_r_r1["Deep_MLP"],
        "LSTM_Loss_Pred": oof_r_r1["Stacked_LSTM"],
    })
    oof_eval_df.to_csv(os.path.join(EVAL_DIR, "cross_validation_oof_predictions.csv"), index=False)

    np.savez_compressed(
        os.path.join(EVAL_DIR, "oof_probabilities_seed42.npz"),
        y_true_c3=y_c3,
        y_true_c5=y_c5,
        y_true_r=y_r,
        fold_ids=fold_ids,
        XGBoost_p3=oof_p3_r1["XGBoost"],
        Random_Forest_p3=oof_p3_r1["Random_Forest"],
        Deep_MLP_p3=oof_p3_r1["Deep_MLP"],
        Stacked_LSTM_p3=oof_p3_r1["Stacked_LSTM"],
        XGBoost_p5_10=results_5class["Clean_10_With_DHW"][1]["XGBoost"],
        Random_Forest_p5_10=results_5class["Clean_10_With_DHW"][1]["Random_Forest"],
        Deep_MLP_p5_10=results_5class["Clean_10_With_DHW"][1]["Deep_MLP"],
        Stacked_LSTM_p5_10=results_5class["Clean_10_With_DHW"][1]["Stacked_LSTM"],
        XGBoost_p5_9=results_5class["Clean_9_No_DHW"][1]["XGBoost"],
        Random_Forest_p5_9=results_5class["Clean_9_No_DHW"][1]["Random_Forest"],
        Deep_MLP_p5_9=results_5class["Clean_9_No_DHW"][1]["Deep_MLP"],
        Stacked_LSTM_p5_9=results_5class["Clean_9_No_DHW"][1]["Stacked_LSTM"],
    )

    # 6. Train production models and run single-thread latency benchmark
    train_and_save_production_models_and_latency(df)
    print("Unified training pipeline completed successfully.")


if __name__ == "__main__":
    run_full_pipeline()
