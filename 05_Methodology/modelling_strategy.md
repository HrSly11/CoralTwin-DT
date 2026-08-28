# Machine Learning & Biophysical Modeling Strategy: CoralTwin-DT

## 1. Machine Learning Formulation

We model coral bleaching risk as a dual-task problem:
1. **Multi-Class Classification:**
   $$\hat{y}_{\text{class}} \in \{\text{Low}, \text{Medium}, \text{High}\}$$
2. **Continuous Ecological Degradation (Regression):**
   $$\hat{y}_{\text{loss}} = \Delta C \in [0, 100]\% \quad (\text{Projected Live Coral Cover Loss})$$

### Feature Vector Composition ($\mathbf{x}_i$):
$$\mathbf{x}_i = [SST, SSTA, DHW, pH, \Omega_{\text{arag}}, \text{Turbidity}_{NTU}, PAR, \text{Rugosity}, \text{Depth}_m, \text{BaselineCover}\%]$$

---

## 2. Evaluated Model Architectures

### 2.1 Random Forest Classifier & Regressor (Breiman 2001)
- Non-parametric ensemble of $M = 300$ decorrelated decision trees.
- Splitting criterion: Gini impurity for classification; mean squared error for regression.
- Maximum tree depth: tuned via Grid Search ($\text{max\_depth} \in [10, 25]$).

### 2.2 Extreme Gradient Boosting (XGBoost - Chen & Guestrin 2016)
- Regularized gradient boosting minimizing regularized objective:
  $$\mathcal{L}(\theta) = \sum_{i=1}^n l(y_i, \hat{y}_i) + \sum_{k=1}^K \left( \gamma T_k + \frac{1}{2} \lambda \|\mathbf{w}_k\|^2 \right)$$
- Learning rate $\eta = 0.05$, subsample ratio $0.8$, colsample by tree $0.8$.

### 2.3 Deep Multi-Layer Perceptron (MLP Neural Network)
- 4-layer fully connected architecture with LeakyReLU activations, Batch Normalization, and Dropout ($p = 0.25$):
  $$\mathbf{h}^{(1)} = \operatorname{LeakyReLU}(\mathbf{W}_1 \mathbf{x} + \mathbf{b}_1)$$
  $$\mathbf{h}^{(2)} = \operatorname{Dropout}(\operatorname{LeakyReLU}(\mathbf{W}_2 \mathbf{h}^{(1)} + \mathbf{b}_2))$$
  $$\hat{\mathbf{y}} = \operatorname{Softmax}(\mathbf{W}_3 \mathbf{h}^{(2)} + \mathbf{b}_3)$$
- Optimizer: Adam with weight decay ($10^{-4}$), trained over 150 epochs with cosine annealing schedule.

---

## 3. Explainability via Game-Theoretic TreeSHAP

SHAP (SHapley Additive exPlanations) computes the exact Shapley value for feature $j$ across subset $\mathcal{S} \subseteq \mathcal{F} \setminus \{j\}$:
$$\phi_j(x) = \sum_{\mathcal{S} \subseteq \mathcal{F} \setminus \{j\}} \frac{|\mathcal{S}|! (|\mathcal{F}| - |\mathcal{S}| - 1)!}{|\mathcal{F}|!} \left[ f_x(\mathcal{S} \cup \{j\}) - f_x(\mathcal{S}) \right]$$

Enables exact quantification of the marginal contribution of $DHW$, $pH$, and optical clarity to predicted bleaching risk.
