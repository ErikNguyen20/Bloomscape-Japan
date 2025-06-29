import os.path
import time

import lightgbm as lgb
import pandas as pd
from tqdm import tqdm
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import ParameterSampler

from data_processing import build_final_dataset


# Load data
df = build_final_dataset(os.path.join("data", "processed_cities"))
df.dropna(subset=['label'], inplace=True)

dropped_columns = ["date", "label", "date_label", "year", "GDD", "day_of_year", "current_year"]


df['year'] = df['date'].dt.year
train = df[df['year'] < 2013]
val = df[df['year'] >= 2015]

X_train = train.drop(columns=dropped_columns)
y_train = train["label"]

X_val = val.drop(columns=dropped_columns)
y_val = val["label"]

# Extensive hyperparameter grid
param_grid = {
    'n_estimators': [100, 250, 400],
    'max_depth': [-1, 3, 4],
    'learning_rate': [0.01, 0.05, 0.1],
    'min_child_weight': [0.001, 0.01, 0.1, 1.0, 5.0, 10.0],
    'colsample_bytree': [0.1, 0.2, 0.3, 0.5, 0.7],
    'num_leaves': [30, 45, 60]
}

grid = list(ParameterSampler(param_grid, 500))
print(f"Total hyperparameter combinations: {len(grid)}")

# For tracking best model
best_score = float('inf')
best_params = None
results = []

start_time = time.time()

for i, params in enumerate(tqdm(grid, desc="Tuning... ")):
    model = lgb.LGBMRegressor(objective='quantile', alpha=0.5, random_state=42, verbosity=-1, **params)
    model.fit(X_train, y_train, callbacks=[lgb.log_evaluation(period=0)])

    preds = model.predict(X_val)
    mae = mean_absolute_error(y_val, preds)

    results.append({**params, 'val_mae': mae})

    if mae < best_score:
        best_score = mae
        best_params = params

    if (i + 1) % 50 == 0 or i == 0:
        elapsed = time.time() - start_time
        print(f"[{i + 1}/{len(grid)}] Current best MAE: {best_score:.4f} | Elapsed: {elapsed / 60:.2f} min")

# Save results as DataFrame for inspection
results_df = pd.DataFrame(results).sort_values(by='val_mae')
print("\nTop 15 parameter sets:")
with pd.option_context('display.max_columns', None, 'display.max_colwidth', None, 'display.expand_frame_repr',False):
    print(results_df.head(15))

print("\nBest hyperparameters found:")
print(best_params)
