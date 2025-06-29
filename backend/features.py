import os

import pandas as pd
import numpy as np


class FeatureExtractor:
    def __init__(self, data_directory_path: str):
        self.RAW_CITIES_DIRECTORY = os.path.join(data_directory_path, "raw_cities")
        self.CLUSTERS_DIRECTORY = os.path.join(data_directory_path, "clusters")
        self.PROCESSED_CITIES_DIRECTORY = os.path.join(data_directory_path, "processed_cities")

        # City mapping
        self.cities_metadata_df = pd.read_csv(os.path.join(data_directory_path, "cities_metadata.csv"))
        self.cities_metadata_df.set_index('City', inplace=True)
        self.city_names = self.cities_metadata_df.index.to_numpy()

        # Builds bloom dictionary for fast lookup based on city and year.
        self.first_bloom_dict = self.build_bloom_dates_dict(os.path.join(data_directory_path, "sakura_first_bloom_dates.csv"))
        self.full_bloom_dict = self.build_bloom_dates_dict(os.path.join(data_directory_path, "sakura_full_bloom_dates.csv"))

    def build_static_features(self, df, city: str):
        metadata = self.cities_metadata_df.loc[city]
        first_bloom_dates = self.first_bloom_dict.get(city)
        full_bloom_dates = self.full_bloom_dict.get(city)

        # Static Features
        df["latitude"] = metadata["latitude"]
        df["longitude"] = metadata["longitude"]

        avg_temp = (df["temperature_2m_max"] + df["temperature_2m_min"]) / 2
        df["GDD"] = np.clip(avg_temp - 3, 30, 0)

        df["day_of_year"] = df["date"].dt.dayofyear

        doy_fraction = df["day_of_year"] / 365.25
        df["doy_cos"] = np.cos(2 * np.pi * doy_fraction)
        df["doy_sin"] = np.sin(2 * np.pi * doy_fraction)

        df["sunlight_length"] = df.apply(self.sunlight_length, axis=1, args=(metadata["latitude"],))
        df["total_precipitation"] = df["rain_sum"] + df["snowfall_sum"]
        df["current_year"] = df["date"].dt.year
        df["global_average_temp_increase"] = df.apply(self.global_average_temp_increase, axis=1, args=(metadata["latitude"],))
        df[['days_since_prev_first_bloom', 'first_bloom_data_available']] = df.apply(self.days_since_last_bloom, axis=1,
                                                                                     args=(first_bloom_dates,))
        df[['days_since_prev_full_bloom', 'full_bloom_data_available']] = df.apply(self.days_since_last_bloom, axis=1,
                                                                                   args=(full_bloom_dates,))
        df["label"] = df.apply(self.Label, axis=1, args=(full_bloom_dates,))
        df["date_label"] = df.apply(self.DateLabel, axis=1, args=(full_bloom_dates,))

    def build_temporal_features(self, df):
        # Temporal Features
        self.GDD_accumulation(df)
        self.sunlight_length_accumulation(df)
        self.frostdays_accumulation(df)
        self.non_frostdays_accumulation(df)
        self.snow_accumulation(df)
        self.et0_fao_evapotranspiration_accumulation(df)
        self.temperature_avg_accumulation(df)
        self.snow_streak(df)
        self.GDD_window(df)
        self.temperature_avg_window(df)
        self.et0_fao_evapotranspiration_window(df)
        self.snowfall_sum_avg_window(df)
        self.rain_sum_avg_window(df)

    # === Helper Functions ===

    def build_bloom_dates_dict(self, bloom_dates_csv: str = "data/sakura_first_bloom_dates.csv"):
        df = pd.read_csv(bloom_dates_csv)
        df.drop(["Currently Being Observed", "30 Year Average 1981-2010", "Notes"], axis=1, inplace=True)
        df.set_index('Site Name', inplace=True)

        bloom_dict = {}
        for site_name, row in df.iterrows():
            bloom_dict[site_name] = {}
            for col, date_str in row.items():
                if pd.isna(date_str) or date_str == '':
                    continue

                try:
                    year = int(col)
                    bloom_dict[site_name][year] = pd.to_datetime(date_str).tz_localize('UTC')
                except Exception:
                    continue
        return bloom_dict



    # === STATIC FEATURES: === #

    def GDD(self, row, BASE: float = 3, MAXIMUM: float = 30, MINIMUM: float = 0):
        max_temp = row["temperature_2m_max"]
        min_temp = row["temperature_2m_min"]
        return max(min(((max_temp + min_temp) / 2) - BASE, MAXIMUM), MINIMUM)

    def sunlight_length(self, row, latitude):
        doy = row['date'].dayofyear

        # Convert latitude to radians
        lat_rad = np.radians(latitude)

        # Declination of the sun (in radians)
        decl = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)

        # Hour angle
        cos_ha = -np.tan(lat_rad) * np.tan(decl)
        cos_ha = np.clip(cos_ha, -1, 1)  # avoid math domain error
        ha = np.arccos(cos_ha)

        # Day length in hours = (2 * ha * 24) / (2π)
        day_length_normalized = ha / np.pi  # Normally there is a factor of *24 to return day length as a unit of hours
        return day_length_normalized

    def global_average_temp_increase(self, row, latitude):
        fractional_year = row['date'].year + (row['date'].timetuple().tm_yday / 365.25)
        return 0.02392396 * fractional_year + -0.00447833 * latitude + -47.81821267686717

    def days_since_last_bloom(self, row, bloom_dates):
        if bloom_dates is None:
            return pd.Series({'days_since_prev_bloom': -1, 'bloom_data_available': False})

        current_date = row['date']
        prev_year = current_date.year - 1

        current_bloom_date = bloom_dates.get(current_date.year, pd.NaT)
        prev_bloom_date = bloom_dates.get(prev_year, pd.NaT)
        if not pd.isna(current_bloom_date) and current_date >= current_bloom_date:
            return pd.Series({
                'days_since_prev_bloom': (current_date - current_bloom_date).days,
                'bloom_data_available': True
            })
        elif not pd.isna(prev_bloom_date) and not pd.isna(current_bloom_date):
            # We have both previous and current bloom date, but current day is not >= current year bloom date
            return pd.Series({
                'days_since_prev_bloom': (current_date - prev_bloom_date).days,
                'bloom_data_available': True
            })
        elif not pd.isna(prev_bloom_date) and pd.isna(current_bloom_date):
            # We don't have current year's bloom date, only last year's
            days = (current_date - prev_bloom_date).days
            if days <= 400:  # Set a cap on how long it'll take for bloom until we assume that data is missing
                return pd.Series({'days_since_prev_bloom': days, 'bloom_data_available': True})
            else:
                return pd.Series({'days_since_prev_bloom': -1, 'bloom_data_available': False})

        # We don't have any bloom date info
        return pd.Series({'days_since_prev_bloom': -1, 'bloom_data_available': False})

    def Label(self, row, bloom_dates):
        if bloom_dates is None:
            return np.nan

        current_date = row['date']
        next_year = current_date.year + 1

        current_bloom_date = bloom_dates.get(current_date.year, pd.NaT)
        next_bloom_date = bloom_dates.get(next_year, pd.NaT)
        if not pd.isna(current_bloom_date) and current_date <= current_bloom_date:
            # return (current_bloom_date - current_date).days  # Days until next bloom
            return current_bloom_date.dayofyear
        elif not pd.isna(next_bloom_date) and not pd.isna(current_bloom_date):
            # return (next_bloom_date - current_date).days  # Days until next bloom
            return next_bloom_date.dayofyear
        return np.nan  # No label exists here

    def DateLabel(self, row, bloom_dates):
        if bloom_dates is None:
            return np.nan

        current_date = row['date']
        next_year = current_date.year + 1

        current_bloom_date = bloom_dates.get(current_date.year, pd.NaT)
        next_bloom_date = bloom_dates.get(next_year, pd.NaT)
        if not pd.isna(current_bloom_date) and current_date <= current_bloom_date:
            return current_bloom_date
        elif not pd.isna(next_bloom_date) and not pd.isna(current_bloom_date):
            return next_bloom_date
        return np.nan  # No label exists here


    # === TEMPORAL FEATURES: === #

    def GDD_accumulation(self, df):
        # Assumes static features 'GDD' are already there
        df["temp_year"] = df["date"].dt.year
        df.loc[df["date"].dt.month >= 12, "temp_year"] += 1  # Start summing from December of previous year
        df["GDD_accumulation"] = df.groupby("temp_year")["GDD"].cumsum()
        df.drop(columns="temp_year", inplace=True)

    def sunlight_length_accumulation(self, df):
        # Assumes static feature 'sunlight_length' are already there
        df["temp_year"] = df["date"].dt.year
        df.loc[df["date"].dt.month >= 12, "temp_year"] += 1  # Start summing from December of previous year
        df['sunlight_length_accumulation'] = df.groupby("temp_year")["sunlight_length"].cumsum()
        df.drop(columns="temp_year", inplace=True)

    def frostdays_accumulation(self, df):
        df['temp_year'] = df["date"].dt.year
        df['frost_days'] = (df['temperature_2m_min'] <= 0).astype(int).groupby(df['temp_year']).cumsum()
        df.drop(columns='temp_year', inplace=True)

    def non_frostdays_accumulation(self, df):
        df['temp_year'] = df["date"].dt.year
        df['non_frost_days'] = (df['temperature_2m_min'] > 0).astype(int).groupby(df['temp_year']).cumsum()
        df.drop(columns='temp_year', inplace=True)

    def snow_accumulation(self, df):
        # Assumes static feature 'snowfall_sum' are already there
        df['temp_year'] = df["date"].dt.year
        df.loc[df["date"].dt.month >= 12, 'temp_year'] += 1  # Start summing from December of previous year
        df['snow_accumulation'] = df.groupby('temp_year')['snowfall_sum'].cumsum()
        df.drop(columns='temp_year', inplace=True)

    def rain_accumulation(self, df):
        # Assumes static feature 'rain_sum' are already there
        df['temp_year'] = df["date"].dt.year
        df['rain_accumulation'] = df.groupby('temp_year')['rain_sum'].cumsum()
        df.drop(columns='temp_year', inplace=True)

    def et0_fao_evapotranspiration_accumulation(self, df):
        # Assumes static feature 'et0_fao_evapotranspiration' are already there
        df['temp_year'] = df["date"].dt.year
        df.loc[df["date"].dt.month >= 12, 'temp_year'] += 1  # Start summing from December of previous year
        df['et0_fao_evapotranspiration_accumulation'] = df.groupby('temp_year')['et0_fao_evapotranspiration'].cumsum()
        df.drop(columns='temp_year', inplace=True)

    def temperature_avg_accumulation(self, df):
        # Assumes static feature 'temperature_2m_mean' are already there
        df['temp_year'] = df["date"].dt.year
        df.loc[df["date"].dt.month >= 12, 'temp_year'] += 1  # Start summing from December of previous year
        df['temperature_avg_accumulation'] = df.groupby('temp_year')['temperature_2m_mean'].cumsum()
        df.drop(columns='temp_year', inplace=True)

    def snow_streak(self, df):
        df['temp_year'] = df["date"].dt.year
        df['snow_free'] = df['snowfall_sum'] == 0
        df['snow_free_streak'] = df['snow_free'].astype(int).groupby(df["temp_year"]).cumsum()
        df.drop(columns=["snow_free", "temp_year"], inplace=True)

    def GDD_window(self, df):
        df['GDD_14day_avg'] = df['GDD'].rolling(window=14, center=False, min_periods=1).mean()
        df['GDD_30day_avg'] = df['GDD'].rolling(window=30, center=False, min_periods=1).mean()


    def temperature_avg_window(self, df):
        df['temperature_2m_mean_14day_avg'] = df['temperature_2m_mean'].rolling(window=14, center=False, min_periods=1).mean()
        df['temperature_2m_mean_30day_avg'] = df['temperature_2m_mean'].rolling(window=30, center=False, min_periods=1).mean()

    def et0_fao_evapotranspiration_window(self, df):
        df['et0_fao_evapotranspiration_14day_avg'] = df['et0_fao_evapotranspiration'].rolling(window=14, center=False, min_periods=1).mean()
        df['et0_fao_evapotranspiration_30day_avg'] = df['et0_fao_evapotranspiration'].rolling(window=30, center=False, min_periods=1).mean()

    def snowfall_sum_avg_window(self, df):
        df['snowfall_sum_14day_avg'] = df['snowfall_sum'].rolling(window=14, center=False, min_periods=1).mean()

    def rain_sum_avg_window(self, df):
        df['rain_sum_14day_avg'] = df['rain_sum'].rolling(window=14, center=False, min_periods=1).mean()

