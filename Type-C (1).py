########################################################################################################
# PROGRAM TITLE: SubscribeSend.py                                                                      #
# DESCRIPTION: sends messages from subscribed MQTT topics to pre-defined CAN nodes using the           #
#           configuration file: CANconfig.toml                                                         #
# WRITTEN BY: Capstone Project Team - Deere Bus Driver                                                 #
#             Batool Khader; Xinchen Hu; Judith Hernandez-Campillo; Haotian Wang                       #
# CODE STATUS: code is working but not as intended, please read the documentation report for details   #
# FINALISED & VERIFIED: 18,JUN,2021                                                                    #
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
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from dbus.service import Object
from ble import (Advertisement, Characteristic, Service, Application, find_adapter, Descriptor, Agent)
import sys
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib
from gi.overrides import override

"""MainLoop = None

try:
   from gi.repository import GLib
   MainLoop = GLib.MainLoop
except ImportError:
   import gobject as Gobject
   MainLoop = GObject.MainLoop
   
mainloop = None"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)
   
#### Necessary bits from ble.py #########
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"

#AGENT_PATH = "/com/punchthrough/agent"

# MQTT setting
Connected = False   # global variable for the state of the connection
BL_Connected = False
wifi_Connected = False
  
broker_address= "172.20.10.8"  # Broker address
own_address= "172.20.10.12"  # Broker address
port = 1883                      # Broker port
# user = 'hu'                   # Connection username
# password = '123456'            # Connection password
IDsTopics = {}
can_IDs = []
Topics = []

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

def on_connect(client, userdata, flags, rc):
  
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
            
def own_connect(client, userdata, flags, rc):
  
    if rc == 0:
  
        print("Connected to broker")
  
        global Connected                # Use global variable
        Connected = True                # Signal connection
  
    else:
        print("Connection failed")




print("Line 156")

#Own BLE Service?
service_uuid = ("bad9e5db-b3a4-4068-9bb6-28a84312fdbc")
humidUUID = ("94e6b46c-3b97-4212-a29d-df94f28ab30b")
tempUUID = ("94e6b46c-3b97-4212-a29d-df94f28ab30a")
ultraUUID = ("94e6b46c-3b97-4212-a29d-df94f28ab30c")
rainUUID = ("94e6b46c-3b97-4212-a29d-df94f28ab30d")
print("Line 164")
#Initialize the D-Bus system bus and BLE adapter:
bus = dbus.SystemBus()
BLE = ble.find_adapter(bus)
ble_obj = bus.get_object(BLUEZ_SERVICE_NAME, BLE)
adapter_props = dbus.Interface(ble_obj, "org.freedesktop.DBus.Properties")
adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

#Get manager objs
service_manager = dbus.Interface(ble_obj, GATT_MANAGER_IFACE)
ad_manager = dbus.Interface(ble_obj, LE_ADVERTISING_MANAGER_IFACE)

#Set up Advertising Data
advert = ble.Advertisement(bus, 0, 'peripheral')
advert.add_service_uuid(service_uuid)
advert.add_local_name("Type-C")
advert.include_tx_power = (True)
print("Line 180")
obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")
#agent = Agent(bus, AGENT_PATH)


######### Create Service ? Or is that done in bluetoothctl? ########################
service = ble.Service(bus, 0, service_uuid, True)

######### Repeat for all characteristics ###########################################
#Create humid characteristic
humid_char = Characteristic(bus, 0, humidUUID, ["read"], service)
service.add_characteristic(humid_char)
#Create temp characteristic
temp_char = Characteristic(bus, 1, tempUUID, ["read"], service)
service.add_characteristic(temp_char)
#Create ultra characteristic
ultra_char = Characteristic(bus, 2, ultraUUID, ["read"], service)
service.add_characteristic(ultra_char)
#Create rain characteristic
rain_char = Characteristic(bus, 3, rainUUID, ["read"], service)
service.add_characteristic(rain_char)

################## Non-characteristic code ############################################
#Create Application
app = Application(bus)
app.add_service(service)
print("Line 206")
#mainloop = MainLoop()

#agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
#agent_manager.RegisterAgent(AGENT_PATH, "NOInputNoOutput")


#### Create reply_handler and error_handler  for Advert ######
def register_ad_cb():
    logger.info("Advertisement registered")

def register_ad_error_cb(error):
    logger.critical("Failed to register advertisement: " + str(error))
    mainLoop.quit()
    
#### Create reply_handler and error_handler  for App ######
def register_app_cb():
    logger.info("GATT application registered")

def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainLoop.quit()

ad_manager.RegisterAdvertisement(advert.get_path(), {}, 
   reply_handler=register_ad_cb,
   error_handler=register_ad_error_cb,)

service_manager.RegisterApplication(app.get_path(), {}, 
   reply_handler=register_app_cb,
   error_handler=[register_app_error_cb],)

print("Line 237")



#ad_manager.UnregisterAdvertisement(advert)
#dbus.service.Object.remove_from_connection(advert)
#agent_manager.RequestDefaultAgent(AGENT_PATH)

#Create an advertisement
"""advertisement_path = PERIPHERAL_PATH + "/advertisement"
advertisement = dbus_object(bus, advertisement_path) # do we need to get rid of that 'n'?

#Define the properties 
advertisement_props = {
       "Type": dbus.String("peripheral", variant_level=1),
       "ServiceUUIDS": dbus.Array([serviceUUID], signature="s", variant_level=1)
       }
       
#Add the advertisement properties to the advertisement object
advertisement.update_properties(advertisement_props)

#Start the advertisement
advertisement.Start()

#Run the main event loop
loop = GLib.MainLoop()
loop.run()"""


def BL_connect():
    global mainLoop
    global BL_Connected
    """if(not BL_Connected):
        print("BLE connecting....")
        p = btle.Peripheral("F4:12:FA:65:7A:35") #Add the MAC
        
        BL_Connected = True
    while(BL_Connected):
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

        humid_val = humidConfig[0].read()
        logger.debug("Humidity Characteristic: " + str(humid_val.decode("utf-8")))
        temp_val = tempConfig[0].read()
        logger.debug("Temperature Characteristic: " + str(temp_val.decode("utf-8")))
        ultra_val = ultraConfig[0].read()
        logger.debug("Distance Characteristic: " + str(ultra_val.decode("utf-8")))
        soil_val = soilConfig[0].read()
        logger.debug("Soil Moisture Characteristic: " + str(soil_val.decode("utf-8")))
        rain_val = rainConfig[0].read()
        logger.debug("Rain Water Characteristic: " + str(rain_val.decode("utf-8")))
        
        
        print("humidity:", humid_val)
        print("temperature:", temp_val)
        print("distance:", ultra_val)
        print("soil moisture:", soil_val)
        print("rain water level:", rain_val)

        msg = can.message.Message(arbitration_id = 0x372, data = humid_val, is_extended_id=False)
        msg2 = can.message.Message(arbitration_id = 0x145, data = temp_val, is_extended_id=False)
        msg3 = can.message.Message(arbitration_id = 0x198, data = ultra_val, is_extended_id=False)
        msg4 = can.message.Message(arbitration_id = 0x171, data = soil_val, is_extended_id=False)
        msg5 = can.message.Message(arbitration_id = 0x158, data = rain_val, is_extended_id=False)
        
        humidUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30b")
        time.sleep(1.0)
        tempUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30a")
        time.sleep(1.0)
        ultraUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30c")
        time.sleep(1.0) 
        rainUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30d")
        time.sleep(1.0) 
        soilUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30e")
        
        
        temp_msg = bytes(msg2)
        ultra_msg = bytearray(struct.pack("f", msg3)).decode('utf-8')
        soil_msg = bytearray(struct.pack("f", msg4)).decode('utf-8')
        rain_msg = bytearray(struct.pack("f", msg5)).decode('utf-8')
        
        humid_msg = humid_val
        temp_msg = temp_val
        ultra_msg = ultra_val
        soil_msg = soil_val
        rain_msg = rain_val
        print("Line 327")
        print(humid_msg)
        print(temp_msg)
        print(ultra_msg)
        print(soil_msg)
        print(rain_msg)

        humidConfig[0].write(humid_msg)
        tempConfig[0].write(temp_msg)
        ultraConfig[0].write(ultra_msg)
        soilConfig[0].write(soil_msg)
        rainConfig[0].write(rain_msg)"""
        
    own_sensors_ble()
       

def wifi_connect():
    if(not wifi_Connected):
        client = mqttClient.Client()               # create new instance
        own_client = mqttClient.Client()               # create new instance
        # client.username_pw_set(user, password=password)    # set username and password
        client.on_connect = on_connect                      # attach function to callback
        client.on_message = on_message                      # attach function to callback
        own_client.on_connect = own_connect                      # attach function to callback
        own_client.on_message = own_message                      # attach function to callback
  
        try:
           client.connect(broker_address, port=port)          # connect to broker
           own_client.connect(own_address, port=port)          # connect to broker
        except:
           print("connection failed")
        
        
    while(wifi_Connected):
        if(wifi_Connected and not BL_Connected):
          client.loop_start()        # start the loop
          for index,topic in enumerate(Topics):
             client.subscribe(topic)

          # Publish the sensor data
          try:
             while True:
                own_sensors_wifi()
            
  
          except KeyboardInterrupt:
             print("exiting")
             client.disconnect()
             client.loop_stop()
             
def own_message(client, userdata, message):
    print ('Message received: ', message.payload)
    print ('Topic: ', message.topic)
    mqttMsg = message.payload.decode()
    print('Received data on the raspberryPi1: ', mqttMsg)
    for index, topic in enumerate(Topics):
        if message.topic == topic:
            # change topic to the topic for the type-c device
            client.publish(message.topic, payload=mqttMsg, qos=1, retain=True)


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
    GPIO.output(GPIO_TRIG, GPIO.LOW)
    time.sleep(2.0)
    GPIO.output(GPIO_TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIG, GPIO.LOW)
    while GPIO.input(GPIO_ECHO) == 0:
        start_time = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        Bounce_back_time = time.time()
    pulse_duration = Bounce_back_time - start_time 
    distance = round(pulse_duration * 17150, 2)
    print( f"Distance: {distance} cm") 
    GPIO.cleanup()
    return distance

"""def soil_sensor():
    raw_value = chan.value
    moisture_per = (raw_value - 5000) / 10
    print("Moisture Percentage: {:.2f}%".format(moisture_per))
    time.sleep(1)
    return moisture_value"""

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

def own_sensors_ble():
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
    humid_char.value = (humid_msg)
    temp_char.value = (temp_msg)
    ultra_char.value = (ultra_msg)
    rain_char.value = (rain_msg)

    time.sleep(10)
    
def own_sensors_wifi():
    humidity, temperature = dht_sensors()
    ultrasonic = ultra_sensor()
    water_level = rainwater_sensor()
    
    """humid = [humidity,0,0,0,0,0,0,0]
    temp = [temperature,0,0,0,0,0,0,0]
    distance = [distance,0,0,0,0,0,0,0]
    soil = [soil_moisture,0,0,0,0,0,0,0]
    water = [water_level,0,0,0,0,0,0,0]"""

    humid = bytearray(struct.pack("f", humidity))
    temp = bytearray(struct.pack("f", temperature))
    distance = bytearray(struct.pack("f", ultrasonic))
    water = bytearray(struct.pack("f", water_level))

    msg = can.message.Message(arbitration_id = 0x372, data = humid, is_extended_id=False)
    msg2 = can.message.Message(arbitration_id = 0x145, data = temp, is_extended_id=False)
    msg3 = can.message.Message(arbitration_id = 0x198, data = distance, is_extended_id=False)
    #msg4 = can.message.Message(arbitration_id = 0x171, data = soil, is_extended_id=False)
    msg5 = can.message.Message(arbitration_id = 0x158, data = water, is_extended_id=False)

    client.publish("TypeC/sensors/ultrasonic", payload=str(msg3).replace(" ",""), qos=1, retain=True)
   

    if humidity is not None and temperature is not None:
       client.publish("TypeC/sensors/humidity", payload=str(msg).replace(" ",""), qos=1, retain=True)
       client.publish("TypeC/sensors/temp", payload=str(msg2).replace(" ",""), qos=1, retain=True)

    #client.publish("TypeC/sensors/soil", payload=msg4, qos=1, retain=True)
    #client.publish("TypeC/sensors/rainwater", payload=str(msg5).replace(" ",""), qos=1, retain=True)
    
    time.sleep(10)



if __name__ == '__main__':
    print("Line 521")
    

    while(True):
        wifi_connect()

        if(not wifi_Connected and not BL_Connected):
            BL_connect()
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            mainloop = GLib.MainLoop()
            mainloop.run()
            print("Line 532")
            
        mainloop.quit()
  
