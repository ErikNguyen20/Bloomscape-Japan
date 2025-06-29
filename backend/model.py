import os

import lightgbm as lgb
import pandas as pd
from tqdm import tqdm

from data_processing import build_final_dataset


def train_model(processed_cities_directory: str):
    df = build_final_dataset(processed_cities_directory)

    df.dropna(subset=['label'], inplace=True)
    dropped_columns = ["date", "label", "date_label", "GDD", "day_of_year", "current_year", "temperature_2m_max",
                       "temperature_2m_min", "rain_sum", "snowfall_sum", "temperature_2m_mean",
                       "et0_fao_evapotranspiration", "weather_code", "sunlight_length", "total_precipitation"]

    X_train = df.drop(columns=dropped_columns, errors='ignore')
    y_train = df["label"]

    # Train quantile models
    quantiles = [0.1, 0.5, 0.9]
    models = {}

    for q in quantiles:
        model = lgb.LGBMRegressor(objective='quantile', alpha=q, n_estimators=250, learning_rate=0.05, max_depth=-1,
                                  colsample_bytree=0.3, num_leaves=31, random_state=42, verbosity=-1)
        model.fit(X_train, y_train, callbacks=[lgb.log_evaluation(period=0)])
        models[q] = model

    return models


def predict_model(processed_cities_directory: str, models):
    dropped_columns = ["date", "label", "date_label", "GDD", "day_of_year", "current_year", "temperature_2m_max",
                       "temperature_2m_min", "rain_sum", "snowfall_sum", "temperature_2m_mean",
                       "et0_fao_evapotranspiration", "weather_code", "sunlight_length", "total_precipitation"]

    predictions = {}
    for file in tqdm(os.listdir(processed_cities_directory), desc="Predicting for cities"):
        city = file.split('.')[0]

        old_df = pd.read_csv(os.path.join(processed_cities_directory, file))
        old_df['date'] = pd.to_datetime(old_df['date'])
        latest_row_df = old_df.loc[[old_df['date'].idxmax()]]
        latest_row_df = latest_row_df.drop(columns=dropped_columns, errors='ignore')

        preds = []
        for quantile in [0.1, 0.5, 0.9]:
            preds.append(models[quantile].predict(latest_row_df)[0])
        predictions[city] = preds

    return predictions
