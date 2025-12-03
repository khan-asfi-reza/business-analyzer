from dotenv import load_dotenv
import os

load_dotenv()


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://admin:admin_password@localhost:5671/")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

DB_HOST=os.getenv("DB_HOST", "localhost")
DB_PORT=int(os.getenv("DB_PORT", "3306"))
DB_DATABASE=os.getenv("DB_NAME", "business_analyzer")
DB_USER=os.getenv("DB_USER", "business_user")
DB_PASSWORD=os.getenv("DB_PASSWORD", "business_password")