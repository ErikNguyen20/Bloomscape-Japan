from datetime import datetime

import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from data_processing import date_update_cron_job
from interfaces import HeatmapPoint, DataService, BloomHistory
from model import train_model, predict_model
from sqlitedb_dataservice import SQLiteDataService


# Load env vars
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  # OR: "redis"
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
FRONTEND_ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(',') if o]


# Create app
app = FastAPI(debug=True)
dataService: DataService = SQLiteDataService(os.path.join("data", "heatmap.db"))  # Select SQLite data service
scheduler = AsyncIOScheduler()


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Redis cache init
@app.on_event("startup")
async def startup():
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="api-cache")

    # Only runs initialization if the data service has not been initialized yet
    await first_time_data_service_init()

    scheduler.add_job(daily_job, CronTrigger(hour=0, minute=0))
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


@cache(expire=3600)
@app.get("/heatmap", response_model=List[HeatmapPoint])
def get_heatmap(
    year: int = Query(..., description="Year to filter bloom points"),
):
    points = dataService.get_heatmap_points(year=year)
    return points


@cache(expire=3600)
@app.get("/history", response_model=BloomHistory)
def get_history(
    city: str = Query(..., description="City to get historic data"),
):
    history = dataService.get_city_history(city=city)
    return history


async def first_time_data_service_init():
    if not dataService.is_first_time_initialized():
        await daily_job()


async def daily_job():
    DATA_DIR = "data"
    print("Running daily Cron job...")
    start = datetime.now()
    print("Start time:", start.strftime("%Y-%m-%d %H:%M:%S"))

    print("Updating data...")
    date_update_cron_job(DATA_DIR)

    print("Training model...")
    models = train_model(os.path.join(DATA_DIR, "processed_cities"))
    print("Predicting from model...")
    predictions = predict_model(os.path.join(DATA_DIR, "processed_cities"), models)

    dataService.set_history(DATA_DIR)
    dataService.set_predictions(DATA_DIR, predictions)

    duration = datetime.now() - start
    print("Cron Job Done! Duration:", duration)


# Run app
if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
