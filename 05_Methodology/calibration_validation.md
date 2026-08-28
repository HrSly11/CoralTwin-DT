# Calibration, Cross-Validation & Verification Strategy: CoralTwin-DT

## 1. Spatial Block Cross-Validation Framework

To prevent artificial inflation of predictive metrics caused by spatial autocorrelation between neighboring pixels, we implement a 5-Fold Spatially Stratified Cross-Validation scheme:

```
[ Full Benthic-Oceanographic Dataset (N = 12,500 samples) ]
                          |
    +---------------------+---------------------+
    | Spatial Clustering (K-Means on Lat/Lon)   |
    +---------------------+---------------------+
                          |
   +----------+----------+----------+----------+----------+
   | Cluster 1| Cluster 2| Cluster 3| Cluster 4| Cluster 5|
   | (Fold 1) | (Fold 2) | (Fold 3) | (Fold 4) | (Fold 5) |
   +----------+----------+----------+----------+----------+
   |   TEST   |   TRAIN  |   TRAIN  |   TRAIN  |   TRAIN  | -> Iteration 1
   |   TRAIN  |   TEST   |   TRAIN  |   TRAIN  |   TRAIN  | -> Iteration 2
   |   TRAIN  |   TRAIN  |   TEST   |   TRAIN  |   TRAIN  | -> Iteration 3
   |   TRAIN  |   TRAIN  |   TRAIN  |   TEST   |   TRAIN  | -> Iteration 4
   |   TRAIN  |   TRAIN  |   TRAIN  |   TRAIN  |   TEST   | -> Iteration 5
```

---

## 2. Quantitative Verification Metrics

### Regression Performance (Coral Cover Loss $\Delta C$):
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
- **Coefficient of Determination ($R^2$):**
  $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

### Classification Performance (Bleaching Risk):
- **Balanced Accuracy:** Average recall obtained on each class.
- **Macro Precision, Recall, and F1-Score:**
  $$\text{Macro-F1} = \frac{1}{K} \sum_{k=1}^K \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$$
- **Area Under the Multi-Class Receiver Operating Characteristic Curve (ROC-AUC).**
