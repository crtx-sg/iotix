"""
Locust load test for IoT device simulation.

This script simulates thousands of IoT devices connecting and publishing telemetry
to an MQTT broker using Locust for load testing.

Usage:
    locust -f iot_device_simulation.py --host mqtt://localhost:1883

Requirements:
    pip install locust locust-plugins paho-mqtt
"""

import json
import random
import time
from datetime import datetime, timezone

from locust import User, task, between, events
from locust_plugins.users.mqtt import MqttUser


class IoTDeviceUser(MqttUser):
    """
    Simulates an IoT device that connects to MQTT broker and publishes telemetry.

    Each user represents one virtual device that:
    - Connects to the MQTT broker
    - Publishes telemetry data at regular intervals
    - Subscribes to command topics
    - Responds to commands
    """

    # Wait time between telemetry publications
    wait_time = between(1, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = f"locust-device-{self.greenlet.getcurrent()}"
        self.telemetry_topic = f"devices/{self.device_id}/telemetry"
        self.command_topic = f"devices/{self.device_id}/commands/#"

    def on_start(self):
        """Called when a user starts - subscribe to command topic."""
        self.subscribe(self.command_topic, qos=1)

    @task(10)
    def publish_temperature(self):
        """Publish temperature telemetry."""
        payload = {
            "deviceId": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(random.uniform(18.0, 28.0), 2),
            "unit": "celsius",
        }
        self.publish(
            self.telemetry_topic,
            json.dumps(payload),
            qos=1,
            name="publish_temperature",
        )

    @task(5)
    def publish_humidity(self):
        """Publish humidity telemetry."""
        payload = {
            "deviceId": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "humidity": round(random.uniform(30.0, 70.0), 2),
            "unit": "percent",
        }
        self.publish(
            self.telemetry_topic,
            json.dumps(payload),
            qos=1,
            name="publish_humidity",
        )

    @task(1)
    def publish_battery(self):
        """Publish battery level telemetry."""
        payload = {
            "deviceId": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "batteryLevel": random.randint(10, 100),
            "unit": "percent",
        }
        self.publish(
            self.telemetry_topic,
            json.dumps(payload),
            qos=1,
            name="publish_battery",
        )


class GatewayDeviceUser(MqttUser):
    """
    Simulates a gateway device that aggregates data from multiple sensors.
    """

    wait_time = between(5, 15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_id = f"locust-gateway-{self.greenlet.getcurrent()}"
        self.telemetry_topic = f"gateways/{self.device_id}/telemetry"

    @task(5)
    def publish_gateway_stats(self):
        """Publish gateway statistics."""
        payload = {
            "deviceId": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connectedDevices": random.randint(5, 50),
            "cpuUsage": round(random.uniform(10.0, 80.0), 2),
            "memoryUsage": round(random.uniform(20.0, 90.0), 2),
            "uptime": int(time.time()),
        }
        self.publish(
            self.telemetry_topic,
            json.dumps(payload),
            qos=2,
            name="publish_gateway_stats",
        )

    @task(1)
    def publish_heartbeat(self):
        """Publish gateway heartbeat."""
        payload = {
            "deviceId": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "alive",
        }
        self.publish(
            f"gateways/{self.device_id}/heartbeat",
            json.dumps(payload),
            qos=0,
            name="publish_heartbeat",
        )


# Custom event handlers for metrics collection
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log MQTT request metrics."""
    if exception:
        print(f"MQTT Error: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("Starting IoT device simulation load test...")
    print(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("IoT device simulation load test completed.")
