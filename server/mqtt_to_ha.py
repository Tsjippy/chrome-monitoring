#!/usr/bin/env python3
from struct import *
import paho.mqtt.client as mqtt
import json
from mqtt_secrets import *
#from paho.mqtt.enums import MQTTProtocolVersion
#from paho.mqtt.enums import CallbackAPIVersion

class MqqtToHa:
    def __init__(self, device, sensors={}):
        self.device         = device
        self.sensors        = sensors

        #Store send commands till they are received
        self.sent           = {}
        self.queue          = {}
        self.client         = mqtt.Client()
        self.connected      = False

        self.main()

    def __str__(self):
        return f"{self.device.name}"

    def create_sensors(self, sensors=''):
        print('Creating Sensors')
        
        device_id       = self.device['identifiers'][0]
        device_name     = self.device['name'].lower().replace(" ", "_")

        if sensors  == '':
            sensors = self.sensors

        for index,sensor in sensors.items():
            if 'sensortype' in sensor:
                sensortype = sensor['sensortype']
            else:
                sensortype  = 'sensor'

            unique_id                           = sensor['name'].replace(' ', '_').replace('.', '_').replace(':', '__').lower()
            unique_id                           = f"{device_name}_{unique_id}"
            self.sensors[index]['base_topic']   = f"homeassistant/{sensortype}/{device_id}/{unique_id}"

            print(f"Creating sensor '{sensor['name']}' with unique id {unique_id}")

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
            result  = self.client.publish(topic=self.sensors[index]['base_topic'] + "/config", payload=payload, qos=1, retain=False)

            # Store
            self.sent[result.mid]    = payload

            if('init' in sensor):
                self.send_value(sensor['name'], sensor['init'])

        print('Sensors created')

    def on_connect(self, client, userdata, flags, reason_code):
        print(f"Connected with result code {reason_code}")

        self.connected  = True

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("$SYS/#")

        client.subscribe("homeassistant/status")

    def on_message(self, client, userdata, message):
        if( '$SYS/' not in message.topic):
            print(message.topic + " " + str(message.payload.decode()) + userdata)

    def on_log(self, client, userdata, paho_log_level, message):
        if paho_log_level == mqtt.LogLevel.MQTT_LOG_ERR:
            print(message)

    # Called when the server received our publish succesfully
    def on_publish(self, client, userdata, mid, reason_code='', properties=''):
        #print(send[mid] )

        #Remove from send dict
        del self.sent[mid]

    # Sends a sensor value
    def send_value(self, sensor, value):
        if not 'base_topic' in sensor:
            return 
        
        topic                   = sensor['base_topic'] + "/state"
        payload                 = json.dumps(value)

        # add current messgae to the queue
        self.queue[topic]   = payload

        if not self.connected:
            print('Not connected, adding to queue')
        else:
            # post queued messages
            for topic, payload in self.queue.items():
                result                  = self.client.publish(topic=topic, payload=payload, qos=1, retain=False)
                self.sent[result.mid]   = payload

    def main(self):
        print('Starting application')
        #client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.on_connect   = self.on_connect
        self.client.on_message   = self.on_message
        self.client.on_log       = self.on_log
        self.client.on_publish   = self.on_publish

        print('Connecting to Home Assistant')
        self.client.connect(mqtt_host, mqtt_port)

        self.client.loop_start()
