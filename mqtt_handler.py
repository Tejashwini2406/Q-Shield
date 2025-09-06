import json
import paho.mqtt.publish as publish

BROKER = "localhost"

#♡ Publish to MQTT
def mqtt_publish(topic: str, message):
    if not isinstance(message, str):
        message = json.dumps(message)
    publish.single(topic, message, hostname=BROKER)
