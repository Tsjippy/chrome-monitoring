#!/usr/bin/env python3
from struct import *
import paho.mqtt.client as mqtt
import json
from mqtt_secrets import *
import logger
from datetime import time
#from paho.mqtt.enums import MQTTProtocolVersion
#from paho.mqtt.enums import CallbackAPIVersion

# https://developers.home-assistant.io/docs/core/entity/sensor/

class MqqtToHa:
    def __init__(self, device, sensors={}):
        self.device         = device
        self.sensors        = sensors

        if 'last_message' not in self.sensors:
            self.sensors['last_message'] = {
                'name': 'Last Message',
                "state": "measurement",
                'type': 'timestamp',
                'icon': 'mdi:clock-check'
            }

        #Store send commands till they are received
        self.sent           = {}
        self.queue          = {}
        self.client         = mqtt.Client()
        self.connected      = False

        self.logger         = logger.Logger('info')

        self.main()

    def __str__(self):
        return f"{self.device.name}"

    def create_sensors(self, sensors=''):
        self.logger.log_message('Creating Sensors')
        
        device_id       = self.device['identifiers'][0]
        device_name     = self.device['name'].lower().replace(" ", "_")

        if sensors  == '':
            sensors = self.sensors

        for index, sensor in sensors.items():
            if 'sensortype' in sensor:
                sensortype                      = sensor['sensortype']
            else:
                sensortype                      = 'sensor'

            unique_id                           = sensor['name'].replace(' ', '_').replace('.', '_').replace(':', '__').lower()
            unique_id                           = f"{device_name}_{unique_id}"
            self.sensors[index]['base_topic']   = f"homeassistant/{sensortype}/{device_id}/{unique_id}"

            self.logger.log_message(f"Creating sensor '{sensor['name']}' with unique id {unique_id}")

            config_payload  = {
                "name": sensor['name'],
                "state_topic": sensor['base_topic'] + "/state",
                "unique_id": unique_id,
                "device": self.device,
                "platform": "mqtt"
            }

            if 'state' in sensor:
                config_payload["state_class"]           = sensor['state']
            
            if 'unit' in sensor:
                config_payload["unit_of_measurement"]   = sensor['unit']

            if 'type' in sensor:
                config_payload["device_class"]          = sensor['type']

            if 'icon' in sensor:
                config_payload["icon"]                  = sensor['icon']

            payload                                     = json.dumps(config_payload)

            # Send
            result  = self.client.publish(
                topic   = self.sensors[index]['base_topic'] + "/config", 
                payload = payload, 
                qos     = 1, 
                retain  = False
            )

            # Store
            self.sent[result.mid]    = payload

            if('init' in sensor):
                self.send_value(sensor['name'], sensor['init'])

        self.logger.log_message('Sensors created')

    def delete_sensor(self, url, sensortype='sensor'):
        device_id       = self.device['identifiers'][0]
        device_name     = self.device['name'].lower().replace(" ", "_")
        unique_id       = url.replace(' ', '_').replace('.', '_').replace(':', '__').lower()
        unique_id       = f"{device_name}_{unique_id}"
        base_topic      = f"homeassistant/{sensortype}/{device_id}/{unique_id}"

        result  = self.client.publish(
            topic   = base_topic + "/config", 
            payload = None, 
            qos     = 0, 
            retain  = True
        )

        # Store
        self.sent[result.mid]    = ''

    def on_connect(self, client, userdata, flags, reason_code):
        self.logger.log_message(f"Connected with result code {reason_code}")

        self.connected  = True

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("$SYS/#")

        client.subscribe("homeassistant/status")

    def on_disconnect(self, client, userdata, rc):
        self.logger.log_message('Disconnected from Home Assistant')
        while True:
            # loop until client.reconnect()
            # returns 0, which means the
            # client is connected
            try:
                self.logger.log_message('Trying to Reconnect to Home Assistant')
                if not client.reconnect():
                    self.logger.log_message('Reconnected')
                    self.create_sensors()

                    self.logger.log_message('Sensors created')
                    break
            except ConnectionRefusedError:
                # if the server is not running,
                # then the host rejects the connection
                # and a ConnectionRefusedError is thrown
                # getting this error > continue trying to
                # connect
                pass
            # if the reconnect was not successful,
            # wait 10 seconds
            time.sleep(10)

    def on_message(self, client, userdata, message):
        if message.topic == 'homeassistant/status':
            if message.payload.decode() == 'offline':
                self.connected  = False
                self.logger.log_message('Disconnected from Home Assistant')
            elif message.payload.decode() == 'online':
                self.connected  = True

                self.logger.log_message('Reconnected To Home Assistant')
                self.create_sensors()

                self.logger.log_message('Sensors created')

        elif( 'SYS/' not in message.topic):
            self.logger.log_message(f"{message.topic} {message.payload.decode()}")

    def on_log(self, client, userdata, paho_log_level, message):
        if paho_log_level == mqtt.LogLevel.MQTT_LOG_ERR:
            self.logger.log_message(message)

    # Called when the server received our publish succesfully
    def on_publish(self, client, userdata, mid, reason_code='', properties=''):
        #self.logger.log_message(send[mid] )

        #Remove from send dict
        del self.sent[mid]

    # Sends a sensor value
    def send_value(self, sensor, value, use_json=True):
        if not 'base_topic' in sensor:
            return 
        
        topic                   = sensor['base_topic'] + "/state"

        if use_json:
            payload                 = json.dumps(value)
        else:
            payload                 = value

        # add current messgae to the queue
        self.queue[topic]   = payload

        if not self.connected:
            self.logger.log_message('Not connected, adding to queue')
        else:
            # post queued messages
            for topic, payload in self.queue.items():
                result                  = self.client.publish(topic=topic, payload=payload, qos=1, retain=False)
                self.sent[result.mid]   = payload

    def main(self):
        self.logger.log_message('Starting application')
        #client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.on_connect      = self.on_connect
        self.client.on_disconnect   = self.on_disconnect
        self.client.on_message      = self.on_message
        self.client.on_log          = self.on_log
        self.client.on_publish      = self.on_publish

        self.logger.log_message('Connecting to Home Assistant')
        self.client.connect(mqtt_host, mqtt_port)

        self.client.loop_start()
