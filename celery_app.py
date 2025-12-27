"""
Celery configuration for background tasks
"""
import os
import pathlib

from celery import Celery
from dotenv import load_dotenv

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

load_dotenv()


TASK_DIRECTORY = "tasks"

def fetch_tasks():
    task_dir = pathlib.Path(__file__).parent / TASK_DIRECTORY
    files = os.listdir(task_dir)
    return [
        f"{TASK_DIRECTORY}.{file.replace(".py", "")}" for file in files if file.endswith(".py") and not file.startswith("__")
    ]


app = Celery(
    "business_analyzer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=fetch_tasks()
)
app.autodiscover_tasks([
    "tasks",
])
app.conf.update()
# Celery configuration
app.conf.update(
    task_routes={
        "tasks.*": "business_analyzer.queue"
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_default_queue="business_analyzer.queue",
)
# # Celery Beat schedule for periodic tasks
# app.conf.beat_schedule = {
#     # Scrape news sources every 4 hours
#     "scrape-sources-every-4-hours": {
#         "task": "tasks.scraping.scrape_sources",
#         "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
#     },
#     # Analyze new scraped content every hour
#     "analyze-content-every-hour": {
#         "task": "tasks.sentiment.analyze_new_content",
#         "schedule": crontab(minute=15, hour="*"),  # Every hour at :15
#     },
#     # Update company recommendations daily
#     "update-company-recommendations-daily": {
#         "task": "tasks.recommendations.update_company_recommendations",
#         "schedule": crontab(minute=0, hour=2),  # Daily at 2:00 AM
#     },
#     # Update asset recommendations daily
#     "update-asset-recommendations-daily": {
#         "task": "tasks.recommendations.update_asset_recommendations",
#         "schedule": crontab(minute=30, hour=2),  # Daily at 2:30 AM
#     },
# }
