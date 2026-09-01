import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_v1_router
from src.config import get_settings
from src.mqtt.client import mqtt_service
from src.mqtt.worker import MqttWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smartrent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info("Starting SmartRent Backend in %s mode...", settings.ENVIRONMENT)

    # Initialize background MQTT Worker and connect
    worker = MqttWorker(settings=settings)
    mqtt_client = mqtt_service.create_client()
    mqtt_client.on_message = worker.on_message

    # Chain on_connect handlers so worker subscribes upon connection
    def combined_on_connect(client, userdata, flags, reason_code, properties=None):
        mqtt_service._on_connect(client, userdata, flags, reason_code, properties)
        worker.on_connect(client, userdata, flags, reason_code, properties)

    mqtt_client.on_connect = combined_on_connect
    mqtt_service.client = mqtt_client
    mqtt_service.start()

    yield

    # Shutdown
    logger.info("Shutting down SmartRent Backend...")
    mqtt_service.stop()


app = FastAPI(
    title="SmartRent SaaS API",
    description="Multi-tenant IoT control backend for short-term rental properties",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_service.is_connected,
        "environment": settings.ENVIRONMENT,
    }
