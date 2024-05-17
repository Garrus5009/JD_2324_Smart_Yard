########################################################################################################
# PROGRAM TITLE: ReceiveParsePublish.py                                                                #
# DESCRIPTION: receives CAN data, parses and publsihes it according to the configuration file:         #
#           CANconfig.toml                                                                             #
# WRITTEN BY: Capstone Project Team - Deere Bus Driver                                                 #
#             Batool Khader; Xinchen Hu; Judith Hernandez-Campillo; Haotian Wang                       #
# CODE STATUS: code is working very well and as intended, please read the documentation report         #
# FINALISED & VERIFIED: 18,JUN,2021                                                                    #
########################################################################################################

import os
import can
from can import message
import time
import paho.mqtt.client as mqtt
import toml
import struct

from bluepy import btle
import binascii

QueueSize = 60
InFlight = 50

can_IDs = []
Topics = []
Pub_freq = []
N = []
message_queue = []
message_queue_ble = []
past_data = []
past_data_ble = []
IdFreqDict = {}
SavedData = {}
connected_to_A = ''
connected_to_C = ''


global BL_Connected
BL_Connected = False
global wifi_Connected
wifi_Connected = False



def on_connect(client, userdata, flags, rc):
     print("Connected with result code : ", rc)


def on_message(client, userdata, msg):
  print("Message Received")
  message_queue.append(msg)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.max_queued_messages_set(QueueSize)
client.max_inflight_messages_set(InFlight)
client.connect("172.20.10.14", 1883, 600)  # change to Lab's ethernet / Test when back on campus


def BL_connect():
    print("line 52")
    global connected_to_C
    global connected_to_A
    global BL_Connected
    if(not BL_Connected):
        print("BLE connecting....")
        try:
            p = btle.Peripheral("F4:12:FA:63:7C:55") #Add the MAC
            connected_to_A = 'Type-A'
            BL_Connected = True
        except btle.BTLEDisconnectError:
            print("Failed to connect to Type-A")
        try:
            pC = btle.Peripheral("B8:27:EB:92:08:1C") # Add the MAC
            connected_to_C = 'Type-C'
            BL_Connected = True
        except btle.BTLEDisconnectError:
            print("Failed to connect to Type-C")
    while(BL_Connected):
        # From Engine_ble
        print("Connected to A: ", connected_to_A)
        print("Connected to C: ", connected_to_C)
        print("Let's start receiving CAN data ...")
        try:
            count = 0
            while True:
                print("Services.....")
                for svc in p.services: # Might need to pass in 'p' from BL_Connect
                    print(str(svc))
                    for ch in svc.getCharacteristics():
                        print(str(ch))
                service_uuid = btle.UUID("260e9bce-4240-4958-ba43-7fbbef17f97d")
                sensorService = p.getServiceByUUID(service_uuid)

                humidConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7b")
                time.sleep(0.20)
                tempConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7a")
                time.sleep(0.20)
                ultraConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7c")
                time.sleep(0.20)
                soilConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7d")
                time.sleep(0.20)
                rainConfig = sensorService.getCharacteristics("14a628c5-3e44-4aa6-bac1-26046e291e7e")
                time.sleep(0.20)

                try:

                #Copy line 97-104 into the Type-C if Block
                    humid_val = humidConfig[0].read()#.decode("utf-8")
                    
                except btle.BTLEException as e:
                    print("Failed to read Config: ", e)
                    humid_val = 0
               
                try:
                    temp_val = tempConfig[0].read()#.decode("utf-8")
                except btle.BTLEException as e:
                    print("Failed to read Config: ", e)  
                    temp_val = 0
                    
                try:
                    ultra_val = ultraConfig[0].read()#.decode("utf-8")
                except btle.BTLEException as e:
                    print("Failed to read Config: ", e)
                    ultra_val = 0
                    
                try:
                    soil_val = soilConfig[0].read()#.decode("utf-8")
                except btle.BTLEException as e:
                    print("Failed to read Config: ", e)
                    soil_val = 0
                    
                try:
                    rain_val = rainConfig[0].read()#.decode("utf-8")
                except btle.BTLEException as e:
                    print("Failed to read Config: ", e)
                    rain_val = 0
                     
                
                current_message = [humid_val, temp_val, ultra_val, soil_val, rain_val]
                for i in current_message:
                    message_queue_ble.append(i)
                 
                print("humidity:", humid_val)
                print("temperature:", temp_val)
                print("distance:", ultra_val)
                print("soil moisture:", soil_val) # May need to put in try-except block
                print("rain water level:", rain_val) # May need to put in try-except block
                if(connected_to_C == 'Type-C'):
                    pc_service_uuid = btle.UUID("bad935db-b3a4-4068-9bb6-28a84312fdbc")
                    pc_sensorService = pc.getServiceByUUID(pc_service_uuid)
                    humidUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30b")
                    time.sleep(0.25)
                    tempUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30a")
                    time.sleep(0.25)
                    ultraUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30c")
                    time.sleep(0.25) 
                    rainUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30d")
                    time.sleep(0.25) 
                    soilUUID = btle.UUID("94e6b46c-3b97-4212-a29d-df94f28ab30e")
                    
                    humidConfigC = pc_sensorService.getCharacteristics(humidUUID)
                    time.sleep(0.25)
                    tempConfigC = pc_sensorService.getCharacteristics(tempUUID)
                    time.sleep(0.25)
                    ultraConfigC = pc_sensorService.getCharacteristics(ultraUUID)
                    time.sleep(0.25) 
                    rainConfigC = pc_sensorService.getCharacteristics(rainUUID)
                    time.sleep(0.25) 
                    soilConfigC = pc_sensorService.getCharacteristics(soilUUID)
                    
                    try:

                        #Copy line 97-104 into the Type-C if Block
                        humid_valC = humidConfigC[0].read()#.decode("utf-8")
                        
                    except btle.BTLEException as e:
                        print("Failed to read Config: ", e)
                        humid_valC = 0
                   
                    try:
                        temp_valC = tempConfigC[0].read()#.decode("utf-8")
                    except btle.BTLEException as e:
                        print("Failed to read Config: ", e)  
                        temp_valC = 0
                        
                    try:
                        ultra_valC = ultraConfigC[0].read()#.decode("utf-8")
                    except btle.BTLEException as e:
                        print("Failed to read Config: ", e)
                        ultra_valC = 0
                        
                    try:
                        soil_valC = soilConfigC[0].read()#.decode("utf-8")
                    except btle.BTLEException as e:
                        print("Failed to read Config: ", e)
                        soil_valC = 0
                        
                    try:
                        rain_valC = rainConfigC[0].read()#.decode("utf-8")
                    except btle.BTLEException as e:
                        print("Failed to read Config: ", e)
                        rain_valC = 0
                    
                receivedMessage = message_queue_ble  # may need to edit this after prior changes
                print("Line 160")
                for i in receivedMessage:
                   print(i)
                   
                if receivedMessage is not None:
                    for message in receivedMessage:
                      print("Line 162")
                      print(message)
                      print(str(message)[2])
                      count = count + 1
                      if(connected_to_C == 'Type-C'):
                         canID = hex(int(message[21:24], 16))  #hex(int(str(message)[21:24], 16))
                         data = bytes.fromhex(message[31:])  #bytes.fromhex(str(message)[31:])
                      if(connected_to_A == 'Type-A'):
                         print("Line 170")
                         canID = hex(int(message[0:3], 16))  #hex(int("""str"""(message)[0:3], 16))
                         print(canID)
                         print(message[3])
                         print(str(message[4:]))
                         print(message[4:])
                         data = message[4:]
                         print("CAN ID: " + str(canID))
                         print("CAN Data: " + str(data))
                      can_message = can.message.Message(arbitration_id=canID, data=data, is_extended_id=False)
                      print("There's a message!")
                      print("Right AREA")
                      print("CAN Message: " + str(can_message.data))
                      str_data = can_message.data.decode('utf-8')
                      print("CAN ID: " + str(can_message.arbitration_id))
                      print("CAN Data: " + str_data)
                      for index, ID in enumerate(can_IDs):
                        if canID == ID:
                          print("CAN ID matches!")
                          for x in can_message.data:
                             print("x" + str(x))
                          #NewData[index] = ' '.join(format(x, '02X') for x in can_message.data)
                          NewData[index] = ' '.join(str_data[x:x+2] for x in range(0, len(str_data), 2))
                          print(NewData[index])
                          Flags[index] = msgFlags(can_message)
                          TimeStamp[index] = can_message.timestamp
                          SaveData(ID, NewData[index], TimeStamp[index])
                          print("Right AREA")
                          if(connected_to_A == 'Type-A'):
                             BLEpub(str(canID), str(NewData[index]), Flags[index], connected_to_A, 1, TimeStamp[index], N[index])
                          if(connected_to_C == 'Type-C'):
                             BLEpub(str(canID), str(NewData[index]), Flags[index], connected_to_C, 1, TimeStamp[index], N[index])

                      if count > 1:
                        past_data_ble.append(message)
                        receivedMessage.pop()
                      
                      time.sleep(0.5)

        except KeyboardInterrupt:
            # Catch keyboard interrupt
            os.system("sudo /sbin/ip link set can0 down")


def wifi_connect():
    print("line 72")
    global wifi_Connected
    
    wifi_Connected = True
    while(wifi_Connected):
        print("line 83")
        if(wifi_Connected and not BL_Connected):
            print("line 85")
            Engine_wifi()
        
        
    
    

def msgFlags(canMsg):

  Ex = 2  # Extended ID frame flag
  Re = 2  # Remote frame flag
  Er = 2  # Error frame flag
  FD = 2  # Flexible Data flag,
  BS = 2  # BitrateSwitch flag: If this is a CAN FD message, this indicates higher bitrate was used for transmission.
  ErInd = 2  # ErrorStateIndicator flag, if this is a CAN FD message, this indicates an error active state.

  if canMsg.is_extended_id == True:
    Ex = 1
  else:
    Ex = 0
  if canMsg.is_remote_frame == True:
    Re = 1
  else:
    Re = 0
  if canMsg.is_error_frame == True:
    Er = 1
  else:
    Er = 0
  if canMsg.is_fd == True:
    FD = 1
    if canMsg.bitrate_switch == True:
      BS = 1
    else:
      BS = 0
    if canMsg.error_state_indicator == True:
      ErInd = 1
    else:
      ErInd = 0

  else:
    FD = 0
    BS = 0
    ErInd = 0
  Flags = [Ex, Re, Er, FD, BS, ErInd]

  return (Flags)


def DBpub(canID, msg, flags, topic, pubFreq, dirtyBit, timeStamp, N):
  if dirtyBit == 1:
    print("SendBit topic:", topic, " SendBit Message: ", msg,
          " SendBit Frequency: ", pubFreq)
    mqttPub(canID, topic, msg, pubFreq, flags, timeStamp, N)
    dirtyBit = 0
    print("SendBit Done")
  else:
    print("Already published:")
  return ()

def BLEpub(canID, msg, flags, source, dirtyBit, timeStamp, N):
  if dirtyBit == 1:
    print("SendBit source:", source, " SendBit Message: ", msg)
    BLPub(canID, source, msg, flags, timeStamp, N)
    dirtyBit = 0
    print("SendBit Done")
  else:
    print("Already published:")
  return ()

def mqttPub(canID, Topic, publishedMessage, pubFreq, flags, timeStamp, N):

  Message = canID, Topic, publishedMessage, str(flags), pubFreq, N
  canMessage = str(Message)

  if canID in OnChange_canIDs:
    OnChangePup(canID, publishedMessage, flags, Topic, timeStamp, pubFreq)
  else:
    PubFreqCase(canMessage, Topic, pubFreq, N, publishedMessage)

def BLPub(canID, source, publishedMessage, flags, timeStamp, N):

  Message = canID, source, publishedMessage, str(flags), N
  canMessage = str(Message)

  if BL_Connected: 
     if canID in OnChange_canIDs:
       global SavedData
       # TimeStampsList = SavedData.get(canID).keys()
       PreviousData = list(SavedData.get(canID).values())
       print(PreviousData)
       L = len(PreviousData)

       if msg == PreviousData[L - 2]:
         print("Data didn't change")

       elif msg != PreviousData[L - 2]:
         print("Data Changed")
         print("PreviousData[index - 2]", PreviousData[L - 2])
         Message = canID, topic, msg, str(flags), pubFreq
         print(Message)
         canMessage = str(Message)
         client.publish("TypeB", payload=canMessage, qos=1, retain=False) # change for ble


def CANPubMQTT(canMessage):
  client.publish("TypeB", payload=canMessage, qos=1, retain=False)


def OnChangePup(canID, msg, flags, topic, timeStamp, pubFreq):
  global SavedData
  # TimeStampsList = SavedData.get(canID).keys()
  PreviousData = list(SavedData.get(canID).values())
  print(PreviousData)
  L = len(PreviousData)

  if msg == PreviousData[L - 2]:
    print("Data didn't change")

  elif msg != PreviousData[L - 2]:
    print("Data Changed")
    print("PreviousData[index - 2]", PreviousData[L - 2])
    Message = canID, topic, msg, str(flags), pubFreq
    print(Message)
    canMessage = str(Message)
    client.publish("TypeB", payload=canMessage, qos=1, retain=False)


def PubFreqCase(canMessage, Topic, pubFreq, N, publishedMessage):

  def timeFreq():
    current = time.time()
    current = int(current)
    i = current - begin
    print(begin, current, i, canMessage)

    if i % N == 0:
      print(str(N), 's past')
      CANPubMQTT(canMessage)
      print(Topic, " ", canMessage, " ", N, current)

  def Greaterthan():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] > N:
        CANPubMQTT(canMessage)

  def LessThan():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] < N:
        CANPubMQTT(canMessage)

  def Equal():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] == N:
        CANPubMQTT(canMessage)

  def GreaterThanOrEqual():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] >= N:
        CANPubMQTT(canMessage)

  def LessThanOrEqual():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] <= N:
        CANPubMQTT(canMessage)

  def NotEqual():
    print("Threshold larger than", N)
    StrCanMessage = publishedMessage.split(' ')
    data_integer = [0] * 8
    for index, data in enumerate(StrCanMessage):

      data_integer[index] = int(data, 16)

      if data_integer[index] != N:
        CANPubMQTT(canMessage)

  if pubFreq == "Always":
    CANPubMQTT(canMessage)
  elif pubFreq == "EverySeconds":
    timeFreq()
  elif pubFreq == "GreaterThan":
    Greaterthan()
  elif pubFreq == "LessThan":
    LessThan()
  elif pubFreq == "Equal":
    Equal()
  elif pubFreq == "GreaterThanOrEqual":
    GreaterThanOrEqual()
  elif pubFreq == "LessThanOrEqual":
    LessThanOrEqual()
  elif pubFreq == "NotEqual":
    NotEqual()


def SaveData(canID, newData, timeStamp):
  global SavedData
  ListOfKeys = SavedData.keys()
  if canID in ListOfKeys:
    SavedData[canID].update({timeStamp: newData})
  else:
    SavedData[canID] = {timeStamp: newData}
  # print("SavedData: ", SavedData)


def Engine_wifi():
    print("Let's start receiving CAN data ...")
    try:

        for topic in Topics:
            client.subscribe(topic)

    except OSError:
        print('Cannot connect to MQTT Client.')  # create different error message
        exit()

    try:
        count = 0
        while True:
            client.loop_start()
            receivedMessage = message_queue  # may need to edit this after prior changes
            if receivedMessage is not None:
                for message in receivedMessage:
                    print(message)
                    payload = message.payload.decode()
                    topic = message.topic
                    qos = message.qos
                    retain = message.retain
                    print("Received message: ", payload)
                    print("Received message on topic: ", topic)
                    print("Received message with QoS: ", qos)
                    print("Message retained: ", retain)
                    count = count + 1
                    if(topic.startswith("TypeC")):
                        canID = hex(int(payload[21:24], 16))
                        print(canID)
                        data = bytes.fromhex(payload[31:])
                        print(data)
                    if(topic.startswith("TypeA")):
                        canID = hex(int(payload[1:4], 16))
                        print(canID)
                        data = bytes.fromhex(payload[12:20])
                        print(data)
                    can_message = can.message.Message(arbitration_id=canID, data=data, is_extended_id=False)
                    print("There's a message!")
                    print("Right AREA")
                    print("CAN ID: " + str(canID))
                    for index, ID in enumerate(can_IDs):
                        if canID == ID:
                            print("CAN ID matches!")
                            NewData[index] = ' '.join(format(x, '02x') for x in can_message.data)
                            Flags[index] = msgFlags(can_message)
                            TimeStamp[index] = can_message.timestamp
                            SaveData(ID, NewData[index], TimeStamp[index])
                            print("Right AREA")
                            DBpub(str(canID), str(NewData[index]), Flags[index], Topics[index], Pub_freq[index], 1, TimeStamp[index], N[index])

                    if count > 1:
                        past_data.append(message)
                        receivedMessage.pop()

                    time.sleep(0.5)

    except KeyboardInterrupt:
        # Catch keyboard interrupt
        os.system("sudo /sbin/ip link set can0 down")

    return ()


def pubAllCAN():
  print("Let's receive and publish ALL CAN data ...")
  
  try:
    print("here")
    client.subscribe('TypeC')

  except OSError:
    print('Cannot connect to MQTT Client.')  # create different error message
    exit()

  try:
    print("here")
    while True:
      client.loop_start()
      receivedMessage = message_queue  # may need to edit this after prior changes
      if receivedMessage is not None:
        for message in receivedMessage:
          print("here")
          payload = message.payload.decode()
          topic = message.topic
          qos = message.qos
          retain = message.retain
          print("Received message: ", payload)
          print("Received message on topic: ", topic)
          print("Received message with QoS: ", qos)
          print("Message retained: ", retain)
          client.publish("TypeB", payload, qos=1, retain=True)

  except KeyboardInterrupt:
    # Catch keyboard interrupt
    os.system("sudo /sbin/ip link set can0 down")

  return ()



if __name__ == "__main__":
  begin = time.time()
  begin = int(begin)
  canConfigIn = input("Do you want to use a config file (y/n)?")
  if canConfigIn == "y":
    try:
      canConfig = '/home/group1/Downloads/CANconfig.toml'
      canConfigDict = toml.load(canConfig)
      for i in canConfigDict.values():
        for x, y in i.items():
          if x == 'id':
            can_IDs.append(y)
          if x == 'topic':
            Topics.append(y)
          if x == 'freq':
            Pub_freq.append(y)
          if x == 'N':
            N.append(y)

      n = len(can_IDs)
      Flags = [0] * n
      NewData = [0] * n
      DirtyBit = [0] * n
      TimeStamp = [0] * n

      canMqttDS = [can_IDs, Topics, Pub_freq, Flags, NewData, DirtyBit]

      IdFreqDict = dict(zip(can_IDs,
                            Pub_freq))  # a dict that holds canIDs and Pub_freq
      OnChange_canIDs = [0]
      # creates a list  to be used to hold the data for each canID with
      # a pub_freq of OnChange:
      for ID, freq in IdFreqDict.items():
        if freq == "OnChange":
          OnChange_canIDs.append(ID)
      while(not wifi_Connected and not BL_Connected):
          wifi_connect()
          """if(not wifi_Connected and not BL_Connected):
              BL_connect()"""
          
    except OSError:
      print("No Config file found")
  else:
    print("Publishing all CAN messages")
    pubAllCAN()

