########################################################################################################
# PROGRAM TITLE: copy_Type-C1.py                                                                       #
# DESCRIPTION: sends messages from subscribed MQTT topics to pre-defined CAN nodes using the           #
#           configuration file: CANconfig.toml                                                         #
# WRITTEN BY: Capstone Project Team - Smart Yard                                                       #
#             Austin Smith; Adrienne Whitmore; Aaron James; Deonta McCluney                            #
# CODE STATUS: code is working but not as intended, please read the documentation report for details   #
# FINALISED & VERIFIED: 01,May,2024                                                                    #
########################################################################################################

from __future__ import print_function
import os
import subprocess
import can
from can import message
import paho.mqtt.client as mqttClient
import time
import toml
import codecs
import Adafruit_DHT
import RPi.GPIO as GPIO
import struct
from bluepy import btle
import binascii

# Import ble.py file obtained from espresso-ble project on github
import ble

# Bluez
import logging
"""import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from dbus.service import Object
from service import (Application, Service, Characteristic, Descriptor)
from advertisement import Advertisement
import sys
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib
from gi.overrides import override"""


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)
   

# MQTT setting
Connected = False   # global variable for the state of the connection
BL_Connected = False
wifi_Connected = False
  
broker_address= "192.168.205.172" # Type-b broker address "172.20.10.10"
own_address= "192.168.205.17"     # Own broker address
port = 1883                    # Common broker port

IDsTopics = {}
can_IDs = []
Topics = []
message_queue = []
ble_queue = []

# Configure DHT22 Sensor Pin
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Ultrasonic Sensor Pin
GPIO_TRIG = 2
GPIO_ECHO = 24

# Configure Rain Water Sensor Pin
POWER_PIN = 14
DO_PIN = 16


# Read topic in TOML
mqttConfig = '/home/group1/Downloads/CANconfig.toml'
mqttConfigDict = toml.load(mqttConfig)
# print(mqttConfigDict)
for i in mqttConfigDict.values():
    for x,y in i.items():
        if x == "id": 
            can_IDs.append(y)
        if x == "topic": 
            Topics.append(y)
                
print(can_IDs)
print(Topics)            


# L = len(Topics)

def on_connect(client, userdata, flags, rc, properties):
  
    if rc == 0:
  
        print("Connected to broker")
  
        global Connected                # Use global variable
        Connected = True                # Signal connection
  
    else:
        print("Connection failed")

def on_message(client, userdata, message):
    print ('Message received: ', message.payload)
    print ('Topic: ', message.topic)
    mqttMsg = message.payload.decode()
    print('Received data on the raspberryPi1: ', mqttMsg)
     
       
def own_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to own broker")
        global Connected                # Use global variable
        Connected = True                # Signal connection
    else:
        print("Connection failed")
        
def own_message(client, userdata, message):
    print ('Message received: ', message.payload)
    print ('Topic: ', message.topic)
    mqttMsg = message.payload.decode()
    print('Received data on the raspberryPi1: ', mqttMsg)
    for index, topic in enumerate(Topics):
        if ((message.topic == topic) and (not 'TypeC' in topic) and (not message.payload.decode() in message_queue)):
            # change topic to the topic for the type-c device
            client.publish(message.topic, payload=message.payload.decode(), qos=message.qos, retain=message.retain)
            message_queue.append(message.payload.decode())
            time.sleep(10)
    own_sensors_wifi()
    time.sleep(10)

client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION2)               # create instance for type-b
own_client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION2)            # create instance for self
client.on_connect = on_connect             # attach function to callback
client.on_message = on_message             # attach function to callback
own_client.on_connect = own_connect         # attach function to callback
own_client.on_message = own_message         # attach function to callback


def BL_connect():
    global mainLoop
    global BL_Connected
    global client
    print("Line 133")
    print(BL_Connected)
    if(not BL_Connected):
        print("BLE connecting....")
        try:
            p = btle.Peripheral("F4:12:FA:65:7A:35") #Add the MAC "F4:12:FA:63:7C:55"
            BL_Connected = True
        except btle.BTLEDisconnectError:
            print("Failed to connect to Type-A")
            BL_Connected = False
    if(BL_Connected):
        print("Services.....")
        for svc in p.services:
            print(str(svc))
            for ch in svc.getCharacteristics():
                print(str(ch))
        service_uuid = btle.UUID("260e9bce-4240-4958-ba43-7fbbef17f97d")
        sensorService = p.getServiceByUUID(service_uuid)

        humidConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7b")
        time.sleep(1.0)
        tempConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7a")
        time.sleep(1.0)
        ultraConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7c")
        time.sleep(1.0)
        soilConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7d")
        time.sleep(1.0)
        rainConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7e")
        time.sleep(1.0)

        humid_val = humidConfig[0].read().decode('utf-8')
        logger.debug("Humidity Characteristic: " + str(humid_val))
        print(humid_val[0:4])
        temp_val = tempConfig[0].read().decode('utf-8')
        logger.debug("Temperature Characteristic: " + str(temp_val))
        ultra_val = ultraConfig[0].read().decode('utf-8')
        logger.debug("Distance Characteristic: " + str(ultra_val))
        soil_val = soilConfig[0].read().decode('utf-8')
        logger.debug("Soil Moisture Characteristic: " + str(soil_val))
        rain_val = rainConfig[0].read().decode('utf-8')
        logger.debug("Rain Water Characteristic: " + str(rain_val))
        
        
        print("humidity:", humid_val)
        print("temperature:", temp_val)
        print("distance:", ultra_val)
        print("soil moisture:", soil_val)
        print("rain water level:", rain_val)
        try:
           client.publish('TypeA/arduino4/sensors/humidity', payload=humid_val[4:], qos=1, retain=True)
           client.publish('TypeA/arduino4/sensors/temp', payload=temp_val[4:], qos=1, retain=True)
           client.publish('TypeA/arduino4/sensors/ultrasonic', payload=ultra_val[4:], qos=1, retain=True)
           client.publish('TypeA/arduino4/sensors/soil', payload=soil_val[4:], qos=1, retain=True)
           client.publish('TypeA/arduino4/sensors/rainwater', payload=rain_val[4:], qos=1, retain=True)
           for message in ble_queue:
              client.publish(Topics[can_IDs.index("0x" + message[0:3])], payload=message[4:], qos=1, retain=True)
        except:
           print("Unable to send to client")
           ble_queue.append(humid_val)
           ble_queue.append(temp_val)
           ble_queue.append(ultra_val)
           ble_queue.append(soil_val)
           ble_queue.append(rain_val)
        
    own_sensors_wifi()
    try:
       p.disconnect()
    except UnboundLocalError:
       print("Not connected to Type-A via BLE")
    wifi_connect()
       

def wifi_connect():
    print("In wifi_connect")
    global wifi_Connected
    while(not wifi_Connected):
        print("In while loop")
        try:
           client.connect(broker_address, port=port)          # connect to broker
           own_client.connect(own_address, port=port)          # connect to broker
           wifi_Connected = True
           print("In try block")
        except:
           print("Connection failed")
           wifi_Connected = False
           BL_connect()
           break   
    while(wifi_Connected):
        if(wifi_Connected and not BL_Connected):
          print("Here")
          client.loop_start()        # start the loop
          own_client.loop_start()        # start the loop
          for index,topic in enumerate(Topics):
             client.subscribe(topic)
             if(not 'TypeC' in topic):
                 own_client.subscribe(topic)

          # Publish the sensor data
          own_sensors_wifi()
          try:
             BL_connect() 
          except KeyboardInterrupt:
             print("exiting")
             own_client.disconnect()
             own_client.loop_stop()
             wifi_Connected = False
             client.disconnect()
             client.loop_stop()


def dht_sensors():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        print("Temp  {0:0.1f}*C Humidity = {1:0.1f}%".format(temperature, humidity))
        return humidity, temperature
    else:
        print("Sensor failure")
        return None, None

   

def ultra_sensor():
    # Configure Ultrasonic GPIO Pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_TRIG, GPIO.OUT)
    GPIO.setup(GPIO_ECHO, GPIO.IN)
    time.sleep(1.0)
    GPIO.output(GPIO_TRIG, GPIO.LOW)
    time.sleep(2.0)
    GPIO.output(GPIO_TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIG, GPIO.LOW)
    while GPIO.input(GPIO_ECHO) == 0:
        start_time = time.time()
        print("Line 287")
    while GPIO.input(GPIO_ECHO) == 1:
        Bounce_back_time = time.time()
    pulse_duration = Bounce_back_time - start_time 
    distance = round(pulse_duration * 17150, 2)
    print( f"Distance: {distance} cm") 
    GPIO.cleanup()
    return distance


def rainwater_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(POWER_PIN, GPIO.OUT) # To power the sensor
    GPIO.setup(DO_PIN, GPIO.IN) # To get the Sensor Reading
    GPIO.output(POWER_PIN, GPIO.HIGH)
    time.sleep(0.01)

    rain_state = GPIO.input(DO_PIN)
    GPIO.output(POWER_PIN, GPIO.HIGH)
    if rain_state == GPIO.HIGH:
       print("The rainwater level is low: ", rain_state)
       return rain_state
    else:
       print("The rainwater level is high: ", rain_state)
       return rain_state
    time.sleep(1)
    GPIO.cleanup()

# For future BLE development
"""def own_sensors_ble():
    humidity, temperature = dht_sensors()
    ultrasonic = ultra_sensor()
    water_level = rainwater_sensor()
    
    logger.debug("Humidity : " + str(humidity))
    logger.debug("Temperature : " + str(temperature))
    logger.debug("Distance : " + str(ultrasonic))
    logger.debug("Rain water level : " + str(water_level))
    
    humid = [int(humidity),0,0,0,0,0,0,0]
    temp = [int(temperature),0,0,0,0,0,0,0]
    distance = [int(ultrasonic),0,0,0,0,0,0,0]
    water = [int(water_level),0,0,0,0,0,0,0]

    msg = can.message.Message(arbitration_id = 0x372, data = humid, is_extended_id=False)
    msg2 = can.message.Message(arbitration_id = 0x145, data = temp, is_extended_id=False)
    msg3 = can.message.Message(arbitration_id = 0x198, data = distance, is_extended_id=False)
    msg5 = can.message.Message(arbitration_id = 0x158, data = water, is_extended_id=False)

    # Pack the CAN message into a bytearray format 
    humid_msg = bytes(msg)
    temp_msg = bytes(msg2)
    ultra_msg = bytes(msg3)
    rain_msg = bytes(msg5)
    ## Write to the characteristics defined above
    

    time.sleep(10)"""

    
def own_sensors_wifi():
    global client
    humidity, temperature = dht_sensors()
    print("Line 349")
    ultrasonic = ultra_sensor()
    print("Line 351")
    water_level = rainwater_sensor()
    
    humid = [int(humidity),0,0,0,0,0,0,0]
    temp = [int(temperature),0,0,0,0,0,0,0]
    distance = [int(ultrasonic),0,0,0,0,0,0,0]
    water = [int(water_level),0,0,0,0,0,0,0]

    humid = bytes(humid)
    temp = bytes(temp)
    distance = bytes(distance)
    water = bytes(water)

    msg = can.message.Message(arbitration_id = 0x372, data = humid, is_extended_id=False)
    msg2 = can.message.Message(arbitration_id = 0x145, data = temp, is_extended_id=False)
    msg3 = can.message.Message(arbitration_id = 0x171, data = distance, is_extended_id=False)
    msg4 = can.message.Message(arbitration_id = 0x158, data = water, is_extended_id=False)
    
    print(msg)
    #print(msg.data.decode('utf-8'))
    client.publish("TypeC/sensors/ultrasonic", payload=str(msg3).replace(" ",""), qos=1, retain=True)
   
    if humidity is not None and temperature is not None:
       client.publish("TypeC/sensors/humidity", payload=str(msg).replace(" ",""), qos=1, retain=True)
       client.publish("TypeC/sensors/temp", payload=str(msg2).replace(" ",""), qos=1, retain=True)
    
    client.publish("TypeC/sensors/rainwater", payload=str(msg4).replace(" ",""), qos=1, retain=True)
       
    time.sleep(10)


if __name__ == '__main__':
    print("Line 521")
  
    try:
        while(True):
            wifi_connect()            
    except KeyboardInterrupt:
        print("keyboard interrupt")
  
