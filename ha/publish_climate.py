#!/usr/bin/env python3
"""Publish two MQTT-discovery climate entities (comfort / reduced setpoint) for the boiler.

The poll list already exposes temp_confort (0x2306) and temp_reduite (0x2307) as number
entities; these climate entities are a thermostat-style front end for the same datapoints.
Run once (messages are retained). Configure with environment variables MQTT_HOST, MQTT_PORT,
MQTT_USER and MQTT_PASSWORD. Requires: pip install "paho-mqtt<2".

Part of viessmann-optolink-ha - GPL-3.0-or-later.
"""
import json
import os

import paho.mqtt.client as mqtt

HOST = os.environ.get("MQTT_HOST", "homeassistant.local")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
USER = os.environ.get("MQTT_USER", "mqtt_user")
PASSWORD = os.environ["MQTT_PASSWORD"]  # never hard-code it
NODE = "chaudiere"  # must match node_id in the poll list

device = {
    "identifiers": ["vitorondens_222f"],
    "name": "Chaudiere Vitorondens",
    "model": "Vitorondens 222-F",
    "manufacturer": "Viessmann",
}


def climate_config(name, suffix, state_topic, addr):
    return {
        "name": name,
        "unique_id": f"{NODE}_thermostat_{suffix}",
        "device": device,
        "availability_topic": f"{NODE}/LWT",
        "current_temperature_topic": f"{NODE}/temperature_ambiante",
        "temperature_state_topic": state_topic,
        "temperature_command_topic": f"{NODE}/cmnd",
        "temperature_command_template": "w;" + addr + ";1;{{ value | round | int }}",
        "min_temp": 10,
        "max_temp": 30,
        "temp_step": 1,
        "modes": ["heat"],
        "temperature_unit": "C",
    }


client = mqtt.Client()
client.username_pw_set(USER, PASSWORD)
client.connect(HOST, PORT, 10)
for suffix, name, state, addr in (
    ("confort", "Thermostat Confort", f"{NODE}/temp_confort", "0x2306"),
    ("reduite", "Thermostat Reduite", f"{NODE}/temp_reduite", "0x2307"),
):
    topic = f"homeassistant/climate/{NODE}/thermostat_{suffix}/config"
    client.publish(topic, json.dumps(climate_config(name, suffix, state, addr)), retain=True)
    print("published", topic)
client.disconnect()
