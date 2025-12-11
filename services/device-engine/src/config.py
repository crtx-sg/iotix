"""Configuration settings for the device engine service."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service configuration
    service_name: str = "device-engine"
    service_port: int = 8080
    log_level: str = "INFO"

    # MQTT broker configuration
    mqtt_broker_host: str = Field(default="localhost", alias="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, alias="MQTT_BROKER_PORT")
    mqtt_use_tls: bool = Field(default=False, alias="MQTT_USE_TLS")
    mqtt_username: str | None = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: str | None = Field(default=None, alias="MQTT_PASSWORD")

    # Kafka configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_telemetry_topic: str = Field(
        default="iotix.telemetry", alias="KAFKA_TELEMETRY_TOPIC"
    )
    kafka_events_topic: str = Field(default="iotix.events", alias="KAFKA_EVENTS_TOPIC")

    # InfluxDB configuration
    influxdb_url: str = Field(default="http://localhost:8086", alias="INFLUXDB_URL")
    influxdb_token: str = Field(default="", alias="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="iotix", alias="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="telemetry", alias="INFLUXDB_BUCKET")

    # Device engine settings
    max_devices_per_instance: int = Field(
        default=10000, alias="MAX_DEVICES_PER_INSTANCE"
    )
    device_model_path: str = Field(
        default="/app/device-models", alias="DEVICE_MODEL_PATH"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
