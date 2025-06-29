import time

import pandas as pd
import openmeteo_requests
import requests
import requests_cache
from openmeteo_requests.Client import OpenMeteoRequestsError
from retry_requests import retry
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

from tqdm import tqdm

from features import FeatureExtractor


def update_bloom_dates(url: str, bloom_dates_csv: str, metadata_csv: str):
    response = requests.get(url)
    response.encoding = response.apparent_encoding  # Correct Japanese encoding

    soup = BeautifulSoup(response.text, "html.parser")

    pre_element = soup.find("pre")

    if not pre_element:
        raise ValueError("No <pre> element found.")

    text = pre_element.get_text()

    lines = text.split('\n')

    # Extract years from header
    years = []
    for line in lines:
        if '地点名' in line and '平年値' in line:
            years = re.findall(r'\d{4}', line)
            years = [int(y) for y in years]
            break

    if not years:
        raise ValueError("Could not find year headers!")

    result = {}

    for line in lines:
        if re.match(r'^\s*地点名', line) or re.match(r'^\s*月\s*日', line) or not line.strip():
            continue

        m = re.match(r'^(\S+)\s+\*?\s*(.*)$', line)
        if not m:
            continue

        city = m.group(1)
        data = m.group(2).strip()

        fields = re.findall(r'(\d+)\s+(\d+)|-', data)

        result[city] = {}
        year_idx = 0
        for field in fields[:len(years)]:
            date = None  # default

            if field == '-':
                date = None
            elif isinstance(field, tuple):
                month, day = field
                month = month.strip()
                day = day.strip()

                if month and day:
                    try:
                        dt = datetime(year=years[year_idx], month=int(month), day=int(day))
                        date = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        date = None  # skip if invalid
            else:
                date = None

            result[city][years[year_idx]] = date
            year_idx += 1

    metadata = pd.read_csv(metadata_csv)
    jp_to_en = {}

    for _, row in metadata.iterrows():
        jp = row['Jp']
        en = row['City']

        # Always map full Japanese name → English name
        jp_clean = jp.strip()
        jp_to_en[jp_clean] = en

        # If parenthesis present, map inner name → English name too
        m = re.search(r'[(（](.*?)[)）]', jp)
        if m:
            inner_jp = m.group(1).strip()
            jp_to_en[inner_jp] = en

    for city in result:
        g = jp_to_en.get(city, None)
        if g is None:
            print("MISSED ", city)

    df = pd.read_csv(bloom_dates_csv)

    for year in years:
        year = int(year)
        col_name = str(year)

        new_col = {jp_to_en[city]: result[city].get(year) for city in result}

        if col_name not in df.columns:
            # If column doesn’t exist, just add it fully
            df[col_name] = df['Site Name'].map(new_col)
        else:
            # Column exists -> only fill NaN cells
            df[col_name] = df[col_name].combine_first(df['Site Name'].map(new_col))

    df.to_csv(bloom_dates_csv, index=False)


def update_from_live_bloom_dates(url: str, bloom_dates_csv: str, metadata_csv: str,):
    metadata = pd.read_csv(metadata_csv)
    jp_to_en = {}

    for _, row in metadata.iterrows():
        jp = row['Jp']
        en = row['City']

        # Always map full Japanese name → English name
        jp_clean = jp.strip()
        jp_to_en[jp_clean] = en

        # If parenthesis present, map inner name → English name too
        m = re.search(r'[(（](.*?)[)）]', jp)
        if m:
            inner_jp = m.group(1).strip()
            jp_to_en[inner_jp] = en

    response = requests.get(url)
    response.encoding = response.apparent_encoding  # Correct Japanese encoding

    soup = BeautifulSoup(response.text, "html.parser")


    # Find <title> text
    title_text = soup.title.string if soup.title else ""
    match = re.search(r"(\d{4})年", title_text)

    selected_year = datetime.now().year
    if match:
        selected_year = int(match.group(1))

    city_date_dict = {}
    for tr in soup.find_all("tr", class_="mtx"):
        th = tr.find("th", scope="row")
        if th:
            city_jp = th.text.strip()
            city = jp_to_en.get(city_jp)
            if city is None:
                print(f"Error: No valid mapping from {city_jp} in dict")
                continue
            # The first td after the th is the observed date
            tds = tr.find_all("td", align="right")
            if tds:
                date_text = tds[0].text.strip()
                try:
                    month, day = map(int, date_text.replace("月", " ").replace("日", "").split())
                    obs_date = datetime(selected_year, month, day)
                    city_date_dict[city] = obs_date
                except Exception as e:
                    print(f"Error parsing date for {city}: {date_text} — {e}")

    df = pd.read_csv(bloom_dates_csv)

    new_col = {city: city_date_dict[city].strftime("%Y-%m-%d") for city in city_date_dict.keys()}
    if str(selected_year) not in df.columns:
        # If column doesn’t exist, just add it fully
        df[str(selected_year)] = df['Site Name'].map(new_col)
    else:
        # Column exists -> only fill NaN cells
        df[str(selected_year)] = df[str(selected_year)].combine_first(df['Site Name'].map(new_col))

    df.to_csv(bloom_dates_csv, index=False)


def get_meteorological_data(latitude, longitude, start_date, end_date):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum", "snowfall_sum", "temperature_2m_mean", "et0_fao_evapotranspiration", "weather_code"],
        "timezone": "Asia/Tokyo"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(2).ValuesAsNumpy()
    daily_snowfall_sum = daily.Variables(3).ValuesAsNumpy()
    daily_temperature_2m_mean = daily.Variables(4).ValuesAsNumpy()
    daily_et0_fao_evapotranspiration = daily.Variables(5).ValuesAsNumpy()
    daily_weather_code = daily.Variables(6).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}

    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["rain_sum"] = daily_rain_sum
    daily_data["snowfall_sum"] = daily_snowfall_sum
    daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
    daily_data["et0_fao_evapotranspiration"] = daily_et0_fao_evapotranspiration
    daily_data["weather_code"] = daily_weather_code

    daily_dataframe = pd.DataFrame(data = daily_data)
    return daily_dataframe


def update_raw_city(city, raw_cities_directory: str, metadata_csv: str):
    file_path = os.path.join(raw_cities_directory, f"{city}.csv")

    # Get the latest date and also the current date
    old_df = pd.read_csv(file_path)
    old_df['date'] = pd.to_datetime(old_df['date'])
    latest_date = old_df['date'].max()
    two_days_ago = datetime.now(latest_date.tz) - timedelta(days=2)

    if two_days_ago - timedelta(days=1) <= latest_date:
        return None

    # Get the longtitude and latitude of the city
    metadata = pd.read_csv(metadata_csv)
    metadata.set_index('City', inplace=True)

    lat = metadata.loc[city]["latitude"]
    lon = metadata.loc[city]["longitude"]

    # Get the updated weather data
    # Retry logic
    downloadedDF = None
    MAX_ATTEMPTS = 5
    for attempt in range(MAX_ATTEMPTS):
        try:
            downloadedDF = get_meteorological_data(lat, lon, latest_date.strftime('%Y-%m-%d'), two_days_ago.strftime("%Y-%m-%d"))
            downloadedDF['date'] = pd.to_datetime(downloadedDF['date'])
            break
        except OpenMeteoRequestsError as e:
            if "Minutely API" in str(e):
                wait_time = 60 * (attempt + 1)
                print(
                    f"Attempt {attempt + 1}/{MAX_ATTEMPTS} | Error occurred... sleeping for {wait_time} seconds and then retrying")
                print(e)
                time.sleep(wait_time)
            else:
                return str(e)
        time.sleep(5)

    # Combine and deduplicate
    combinedDF = pd.concat([old_df, downloadedDF]).drop_duplicates(subset='date', keep='last')
    combinedDF.to_csv(file_path, index=False)

    return None


def process_cities(data_directory: str):
    extractor = FeatureExtractor(data_directory)

    file_list = os.listdir(extractor.RAW_CITIES_DIRECTORY)
    pbar = tqdm(file_list, desc="Processing cities")

    for file in pbar:
        city = file.split('.')[0]
        df = pd.read_csv(os.path.join(extractor.RAW_CITIES_DIRECTORY, file), parse_dates=["date"])

        pbar.set_description(f"{city}: Building static features")
        extractor.build_static_features(df, city)

        pbar.set_description(f"{city}: Building temporal features")
        extractor.build_temporal_features(df)

        pbar.set_description(f"{city}: Saving")
        df.to_csv(os.path.join(extractor.PROCESSED_CITIES_DIRECTORY, file), index=False)


def build_final_dataset(processed_cities_directory: str):
    dfs = []
    for file in tqdm(os.listdir(processed_cities_directory), desc="Processing cities"):
        df = pd.read_csv(os.path.join(processed_cities_directory, file), parse_dates=["date", "date_label"])
        df.drop(columns=[
            "temperature_2m_max", "temperature_2m_min", "rain_sum", "snowfall_sum", "temperature_2m_mean",
            "et0_fao_evapotranspiration", "weather_code", "sunlight_length", "total_precipitation"
        ], inplace=True, errors='ignore')
        dfs.append(df)

    df_combined = pd.concat(dfs, ignore_index=True)
    return df_combined


def date_update_cron_job(data_directory: str):

    now = datetime.now()
    month = now.month

    if 1 <= month <= 6:
        # Japan Meteorlogical agency updates this url frequently during these months
        print("Update Full Historic Bloom Date")
        update_from_live_bloom_dates(url="https://www.data.jma.go.jp/sakura/data/sakura_mankai.html",
                                     bloom_dates_csv=os.path.join(data_directory, "sakura_full_bloom_dates.csv"),
                                     metadata_csv=os.path.join(data_directory, "cities_metadata.csv"))

        print("Update First Historic Bloom Date")
        update_from_live_bloom_dates(url="https://www.data.jma.go.jp/sakura/data/sakura_kaika.html",
                                     bloom_dates_csv=os.path.join(data_directory, "sakura_first_bloom_dates.csv"),
                                     metadata_csv=os.path.join(data_directory, "cities_metadata.csv"))
    else:
        # Just take the slower-updating historic info in other months
        print("Update Full Historic Bloom Date")
        update_bloom_dates(url="https://www.data.jma.go.jp/sakura/data/sakura004_07.html",
                           bloom_dates_csv=os.path.join(data_directory, "sakura_full_bloom_dates.csv"),
                           metadata_csv=os.path.join(data_directory, "cities_metadata.csv")
                           )
        print("Update First Historic Bloom Date")
        update_bloom_dates(url="https://www.data.jma.go.jp/sakura/data/sakura003_07.html",
                           bloom_dates_csv=os.path.join(data_directory, "sakura_first_bloom_dates.csv"),
                           metadata_csv=os.path.join(data_directory, "cities_metadata.csv")
                           )

    print("Update the weather data for each city")
    for file in tqdm(os.listdir(os.path.join(data_directory, "raw_cities")), desc="Update raw cities"):
        city = file.split('.')[0]
        err = update_raw_city(city, os.path.join(data_directory, "raw_cities"), os.path.join(data_directory, "cities_metadata.csv"))
        if err is not None:
            print("Problem with OpenMateo: ", err)
            break

    print("Building features for cities")
    process_cities(data_directory)
