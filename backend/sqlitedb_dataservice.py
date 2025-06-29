import os
import sqlite3
from datetime import datetime
from typing import List

from tqdm import tqdm

from features import FeatureExtractor
from interfaces import HeatmapPoint, DataService, BloomHistory, BloomHistoryPoint


class SQLiteDataService(DataService):
    def __init__(self, db_path: str = "heatmap.db"):
        self.db_path = db_path

    def is_first_time_initialized(self) -> bool:
        return os.path.exists(self.db_path)

    def set_history(self, data_directory: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Drop and recreate table
        cursor.execute("DROP TABLE IF EXISTS bloom_history")
        cursor.execute("""
            CREATE TABLE bloom_history (
                city TEXT,
                jp TEXT,
                year INT,
                lat REAL,
                lon REAL,
                day_of_year INT
            )
        """)

        extractor = FeatureExtractor(data_directory)

        total_rows_inserted = 0
        years_set = set()

        # Add full bloom data to db.
        for city in tqdm(extractor.city_names, desc="Building sqlite database."):
            city_years = extractor.full_bloom_dict[city].keys()
            for year in city_years:
                lat = extractor.cities_metadata_df.loc[city]["latitude"]
                lon = extractor.cities_metadata_df.loc[city]["longitude"]
                jp = extractor.cities_metadata_df.loc[city]["Jp"]
                val = extractor.full_bloom_dict[city].get(year)
                if val is None:
                    continue
                doy = val.dayofyear
                cursor.execute(
                    "INSERT INTO bloom_history VALUES (?, ?, ?, ?, ?, ?)",
                    (city, jp, year, lat, lon, doy)
                )
                years_set.add(year)
                total_rows_inserted += 1

        conn.commit()
        conn.close()

    def set_predictions(self, data_directory: str, predictions):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Drop and recreate table
        cursor.execute("DROP TABLE IF EXISTS bloom_predictions")
        cursor.execute("""
            CREATE TABLE bloom_predictions (
                city TEXT,
                year INT,
                jp TEXT,
                lat REAL,
                lon REAL,
                quantile_10 REAL,
                quantile_50 REAL,
                quantile_90 REAL
            )
        """)

        extractor = FeatureExtractor(data_directory)

        year = datetime.now().year
        month = datetime.now().month
        for city, preds in predictions.items():
            lat = extractor.cities_metadata_df.loc[city]["latitude"]
            lon = extractor.cities_metadata_df.loc[city]["longitude"]
            jp = extractor.cities_metadata_df.loc[city]["Jp"]

            cursor.execute(
                """
                SELECT 1 FROM bloom_history
                WHERE city = ? AND year = ?
                LIMIT 1
                """,
                (city, year)
            )
            row = cursor.fetchone()
            if row or month >= 6:
                cursor.execute(
                    "INSERT INTO bloom_predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (city, year+1, jp, lat, lon, preds[0], preds[1], preds[2])
                )
                continue

            cursor.execute(
                "INSERT INTO bloom_predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (city, year, jp, lat, lon, preds[0], preds[1], preds[2])
            )

        conn.commit()
        conn.close()

    def get_heatmap_points(self, year: int) -> List[HeatmapPoint]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT city, jp, lat, lon, day_of_year FROM bloom_history WHERE year = ?", (year,))
        rows = cursor.fetchall()

        points = [HeatmapPoint(city=row[0], city_jp=row[1], lat=row[2], lng=row[3], value=row[4], is_prediction=False) for row in rows]
        existing_cities = set(row[0] for row in rows)

        if year >= datetime.now().year:
            cursor.execute("""
                SELECT city, jp, lat, lon, quantile_50 
                FROM bloom_predictions 
                WHERE year = ?
            """, (year,))
            prediction_rows = cursor.fetchall()

            predicted_points = [HeatmapPoint(city=row[0], city_jp=row[1], lat=row[2], lng=row[3], value=row[4], is_prediction=True)
                                for row in prediction_rows if row[0] not in existing_cities]
            points.extend(predicted_points)

        conn.close()
        return points

    def get_city_history(self, city: str) -> BloomHistory:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT year, day_of_year FROM bloom_history WHERE city = ?", (city,))
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT year, quantile_10, quantile_50, quantile_90
            FROM bloom_predictions
            WHERE city = ?
        """, (city,))
        preds = cursor.fetchone()

        conn.close()

        points = [BloomHistoryPoint(year=row[0], value=row[1]) for row in rows]
        history = BloomHistory(points=points, prediction_year=preds[0], prediction_q10=preds[1], prediction_q50=preds[2], prediction_q90=preds[3])
        return history
