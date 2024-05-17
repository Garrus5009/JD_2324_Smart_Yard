/*
  ArduinoMqttClient - WiFi Simple Sender

  This example connects to a MQTT broker and publishes a message to
  a topic once a second. Extra stuff.

  The circuit:
  - Arduino MKR 1000, MKR 1010 or Uno WiFi Rev2 board

  This example code is in the public domain.
*/
#include <Arduino_CAN.h>
#include <ArduinoMqttClient.h>
#include <ArduinoBLE.h>
#include <WiFiS3.h>
#include "arduino_secrets.h"
#include <ArduinoJson.h>

// Added the CANconfig header file to get the topics 
//#include "CANconfig.h"
IPAddress raspberryPiIP1(172, 20, 10, 10); // add the actual raspi ip address //172, 20, 10, 12
IPAddress raspberryPiIP2(172, 20, 10, 9);  // add the actual raspi ip address

// Defines for the DHT22 code 
#include <DHT.h>
#define dataPin 5  //Defines pin number to which the sensor is connected 
DHT dht = DHT(5, DHT22); //Creates a DHT object 

//Ultrasonic Code Pin Setup
const int trigPin = 6;
const int echoPin = 9;

// Rainwater Code Pin Setup
#define sensorPower 7
#define sensorPin A1
int val = 0;

// Value for storing water level
int waterLevel = 0;

long duration;
int distance;

//Soil Moisture Code 
const int dry = 595;
const int wet = 239;

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;    // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

bool isPiConnected1, isPiConnected2 = false;

// To connect with SSL/TLS:
// 1) Change WiFiClient to WiFiSSLClient.
// 2) Change port value from 1883 to 8883.
// 3) Change broker value to a server with a known SSL/TLS root certificate 
//    flashed in the WiFi module.

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

String connected = "";
const char broker[] = "172.20.10.9";
int        port     = 1883;
const char *topic[]  = {"TypeA/arduino4/sensors/humidity", "TypeA/arduino4/sensors/temp", "TypeA/arduino4/sensors/ultrasonic", "TypeA/arduino4/sensors/soil", "TypeA/arduino4/sensors/rainwater"};

const long interval = 1000;
unsigned long previousMillis = 0;
// CAN IDs
static uint32_t const Temp_CAN_ID = 0x556;
static uint32_t const Humid_CAN_ID = 0x776;
static uint32_t const Ultra_CAN_ID = 0x116;
static uint32_t const Soil_CAN_ID = 0x226;
static uint32_t const Rain_CAN_ID = 0x166;
// BLE UUID Definitions
#define SERVICE_UUID "260e9bce-4240-4958-ba43-7fbbef17f97d"
#define TEMP_DATA_CHAR_UUID "14a628c5-3e44-4aa6-bac1-26046e291e7a"
#define HUMID_DATA_CHAR_UUID "14a628c5-3e44-4aa6-bac1-26046e291e7b"
#define ULTRA_DATA_CHAR_UUID "14a628c5-3e44-4aa6-bac1-26046e291e7c"
#define SOIL_DATA_CHAR_UUID "14a628c5-3e44-4aa6-bac1-26046e291e7d"
#define RAIN_DATA_CHAR_UUID "14a628c5-3e44-4aa6-bac1-26046e291e7e"
// BLE Service and Characteristic declarations
BLEService service(SERVICE_UUID);
BLEStringCharacteristic tempDataChar(TEMP_DATA_CHAR_UUID, BLERead | BLEBroadcast | BLENotify, 20);
BLEStringCharacteristic humidDataChar(HUMID_DATA_CHAR_UUID, BLERead | BLEBroadcast | BLENotify, 20);
BLEStringCharacteristic ultraDataChar(ULTRA_DATA_CHAR_UUID, BLERead | BLEBroadcast | BLENotify, 20);
BLEStringCharacteristic soilDataChar(SOIL_DATA_CHAR_UUID, BLERead | BLEBroadcast | BLENotify, 20);
BLEStringCharacteristic rainDataChar(RAIN_DATA_CHAR_UUID, BLERead | BLEBroadcast | BLENotify, 20);
// Count
int count = 0;

void setup() {
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  pinMode(sensorPower, OUTPUT); // Sets sensorPower as an Output

  // Set sensorPower LOW so no power flows
  digitalWrite(sensorPower, LOW);
  //Initialize serial and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  delay(1000);

  // attempt to connect to bluetooth module

  // attempt to connect to WiFi network:
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  while (connected == "") {
    if(WiFi.begin(ssid, pass) != WL_CONNECTED){
      // failed, try bluetooth
      Serial.print("Failed to connect to WiFi Network");
      delay(5000);
    }else{
      Serial.println("You're connected to the network");
      connected = "wifi";
      break;
    }
    if(!BLE.begin()){
      // failed, try wifi
      while(!BLE.begin()){
        Serial.print("Failed to connect to BLE");
        delay(5000);
      }
    }else{
      Serial.println("You're connected to the BLE module");
      Serial.println(BLE.address());
      BLE.setLocalName("Type-A");
      // Setting BLE Service Advertisement
      BLE.setAdvertisedService(service);
      // Adding characteristics to Service
      service.addCharacteristic(tempDataChar);
      service.addCharacteristic(humidDataChar);
      service.addCharacteristic(ultraDataChar);
      service.addCharacteristic(soilDataChar);
      service.addCharacteristic(rainDataChar);
      // Adding the service to the BLE stack
      BLE.addService(service);
      BLE.setConnectable(true);
      tempDataChar.broadcast();
      humidDataChar.broadcast();
      ultraDataChar.broadcast();
      soilDataChar.broadcast();
      rainDataChar.broadcast();
      BLE.advertise();
      Serial.println("Bluetooth Device is now active, waiting for connections");
      connected = "ble";
      break;
    }
    connected = "";
  }

  Serial.println("Line 157");
  Serial.println(connected);

  // You can provide a unique client ID, if not set the library uses Arduino-millis()
  // Each client must have a unique client ID
  // mqttClient.setId("clientId");

  // You can provide a username and password for authentication
  // mqttClient.setUsernamePassword("username", "password");

  
  while(!mqttClient.connected() && connected == "wifi") {
    Serial.print("Attempting to connect to the MQTT broker: ");
    Serial.println("RaspberryPi1");
    if(!mqttClient.connect(raspberryPiIP1, port)){
      Serial.print("MQTT connection failed! Error code = ");
      Serial.println(mqttClient.connectError());
    }
    else{
      isPiConnected1 = true;
      Serial.println("Connected to RaspberryPi1");
      continue;
    }
    Serial.print("Attempting to connect to the MQTT broker: ");
    Serial.println("RaspberryPi2");
    if(!mqttClient.connect(raspberryPiIP2, port)){
      Serial.print("MQTT connection failed! Error code = ");
      Serial.println(mqttClient.connectError());
    }
    else{
      isPiConnected2 = true;
      Serial.println("Connected to RaspberryPi2");
      continue;
    }
    delay(1000);
  }

  Serial.println("You're connected to the MQTT broker!");
  Serial.println();

  if (!CAN.begin(CanBitRate::BR_250k))
  {
    Serial.println("CAN.begin(...) failed.");
    for (;;) {}
  }
}

static uint32_t msg_cnt = 0;
unsigned char stmp[8] = {1, 2, 3, 4, 5, 6, 7, 8};

void loop() {
  if(connected == "wifi"){
    if (isPiConnected1) {
      // Raspberry Pi is connected, proceed with sending messages
      Serial.println("Raspberry Pi 1 is connected");
      sensors();
    } else {
      // Raspberry Pi is not connected, handle the situation accordingly
      Serial.println("Raspberry Pi 1 is not connected.");
    }
    if (isPiConnected2) {
      // Raspberry Pi is connected, proceed with sending messages
      Serial.println("Raspberry Pi 2 is connected");
      sensors();
    } else {
      // Raspberry Pi is not connected, handle the situation accordingly
      Serial.println("Raspberry Pi 2 is not connected.");
    }
  }if(connected == "ble"){
    Serial.println("Line 225");
    sensors();
  }
}

int readSensor(){
  digitalWrite(sensorPower, HIGH); // Turn sensor on
  delay(10);                       // Wait 10 ms
  val = analogRead(sensorPin);     // Read analog value from sensor
  digitalWrite(sensorPower, LOW);  // Turn sensor off
  return val;
}

void sensors(){
   //DHT22 Code
  Serial.println("Line 241");
  dht.begin();
  //Uncomment whatever type you're using!
	int readData = dht.read(dataPin); // DHT22/AM2302
	//int readData = DHT.read11(dataPin); // DHT11

	float t = dht.readTemperature(); // Gets the values of the temperature
	float h = dht.readHumidity(); // Gets the values of the humidity

	// Printing the results on the serial monitor
	Serial.print("Temperature = ");
	Serial.print(t);
	Serial.print(" ");
	Serial.print((char)176);//shows degrees character
	Serial.print("C | ");
	Serial.print((t * 9.0) / 5.0 + 32.0);//print the temperature in Fahrenheit
  float temp = ((t * 9.0) / 5.0 + 32.0);
	Serial.print(" ");
	Serial.print((char)176);//shows degrees character
	Serial.println("F ");
	Serial.print("Humidity = ");
	Serial.print(h);
	Serial.println(" % ");
	Serial.println("");
  uint8_t temperature[8] = {temp,0,0,0,0,0,0,0};
  uint8_t humidity[8] = {h,0,0,0,0,0,0,0};
  Serial.print("Size of humidity array: ");
  Serial.println(sizeof(humidity));
  Serial.print("Size of temp array: ");
  Serial.println(sizeof(temperature));
	delay(500); // Delays 2 secods
  //End of DHT22 code

  //Begin Ultrasonic code 
  // Clears the trigPin
  digitalWrite(trigPin, LOW);
  delay(1000);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delay(1000);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distance = duration * 0.034 / 2;
  // Prints the distance on the Serial Monitor
  Serial.print("Distance: ");
  Serial.println(distance);
  uint8_t ultrasonic[8] = {distance,0,0,0,0,0,0,0};
  Serial.print("Size of ultra array: ");
  Serial.println(sizeof(ultrasonic));
  
  // End of ultrasonic code 

  // Begin Rain Water code
  // Sensor when dry ~= 0
  // Sensor when partially immersed ~= 420
  // Sensor when fully immersed ~= 520
  int level = readSensor();
  Serial.print("Water Level: ");
  Serial.println(level);
  delay(1000);
  uint8_t rain[8] = {level,0,0,0,0,0,0,0};
  Serial.print("Size of rain array: ");
  Serial.println(sizeof(rain));

  // Begin Soil Moisture Code
  // Sensor has a range of 239 to 595
  // We want to translate this to a scale or 0% to 100%
  // More info: https://www.arduino.cc/reference/en/language/functions/math/map/
  int sensorVal = analogRead(A0);
  int percentageHumididy = map(sensorVal, wet, dry, 100, 0); 
  Serial.print("Soil Moisture Reading: ");
  Serial.print(percentageHumididy);
  uint8_t soil[8] = {percentageHumididy,0,0,0,0,0,0,0};
  Serial.println("%");
  Serial.print("Size of soil array: ");
  Serial.println(sizeof(soil));
  //End of Soil Moisture Code
  
  delay(500);
  Serial.println("Line 321");
  Serial.println(connected);
  //////////////////// BLE PORTION /////////////////////////////////
  if(connected == "ble"){
    Serial.println("Line 326");
    // Attempt to connect to central device
    BLEDevice central = BLE.central();
    if(!central){
      while(!central){
        central = BLE.central();
      }
    }
    if(central){
      Serial.print("Connected to central: ");
      Serial.println(central.address());
      while(central.connected()){
        delay(200);
        // Read values from sensors
        // Writing sensor values to the characteristics
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis >= interval) {
          // save the last time a message was sent
          previousMillis = currentMillis;

          /* Assemble a CAN message with the format of
          * 0xCA 0xFE 0x00 0x00 [4 byte message counter]
          */
          /*uint8_t const msg_data[] = {0xCA,0xFE,0,0,0,0,0,0};
          memcpy((void *)(msg_data + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg(CanStandardId(CAN_ID), sizeof(msg_data), msg_data);*/

          //Temperature
          Serial.println("In Loop");
          
          memcpy((void *)(temperature + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg(Temp_CAN_ID, 8, temperature);
          Serial.println(msg);
          Serial.print("Size of can message 1: ");
          Serial.println(sizeof(msg));
          Serial.println("Temperature Sent To RPI");
          String msg_ID = String(msg.id, HEX);
          String msg_DL = String(msg.data_length, HEX);
          String msg_D;
          for (int i = 0; i < msg.data_length; i++) {
            Serial.println(msg.data[i]);
            if (i >= 1 && (msg.data[i] <= 0x0F)) {
              msg_D += String(0) + String(msg.data[i], HEX); // Add leading zero if necessary
              //Serial.println(count);
            }else if(i == 0 && msg.data[i] == 0x00){
              msg_D += String(0) + String(msg.data[i], HEX);
            }else{
              msg_D += String(msg.data[i], HEX);
            }
            msg_D.toUpperCase(); // Convert the letters to uppercase
          }
          String can = msg_ID + msg_DL + msg_D;
          Serial.println(can);
          Serial.print("Size of message string 1: ");
          Serial.println(sizeof(can));
          tempDataChar.writeValue(can);
          Serial.println();

          /* Increase the message counter. */
          msg_cnt++;
          count++;

          delay(1000);

          //Humidity

          memcpy((void *)(humidity + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg2(Humid_CAN_ID, 8, humidity);
          Serial.println(msg2);
          Serial.print("Size of can message 2: ");
          Serial.println(sizeof(msg2));
          Serial.println("Humidity Sent To RPI");
          String msg2_ID = String(msg2.id, HEX);
          String msg2_DL = String(msg2.data_length, HEX);
          String msg2_D;
          for (int i = 0; i < msg2.data_length; i++) {
            Serial.println(msg2.data[i]);
            if (i >= 1 && (msg2.data[i] <= 0x0F)) {
              msg2_D += String(0) + String(msg2.data[i], HEX); // Add leading zero if necessary
              //Serial.println(count);
            }else{
              msg2_D += String(msg2.data[i], HEX);
            }
            msg2_D.toUpperCase(); // Convert the letters to uppercase
          }
          String can2 = msg2_ID + msg2_DL + msg2_D;
          Serial.println(can2);
          Serial.print("Size of message string 2: ");
          Serial.println(sizeof(can2));
          humidDataChar.writeValue(can2);
          Serial.println();

          /* Increase the message counter. */
          msg_cnt++;
          count++;

          delay(1000);

          //Ultrasonic 

          memcpy((void *)(ultrasonic + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg3(Ultra_CAN_ID, 8, ultrasonic);
          Serial.println(msg3);
          Serial.print("Size of can message 3: ");
          Serial.println(sizeof(msg3));
          Serial.println("Ultrasonic Sent To RPI");
          String msg3_ID = String(msg3.id, HEX);
          String msg3_DL = String(msg3.data_length, HEX);
          String msg3_D;
          for (int i = 0; i < msg3.data_length; i++) {
            Serial.println(msg3.data[i]);
            if (i >= 1 && (msg3.data[i] <= 0x0F)) {
              msg3_D += String(0) + String(msg3.data[i], HEX); // Add leading zero if necessary
              //Serial.println(count);
            }else{
              msg3_D += String(msg3.data[i], HEX);
            }
            msg3_D.toUpperCase(); // Convert the letters to uppercase
          }
          String can3 = msg3_ID + msg3_DL + msg3_D;
          Serial.println(can3);
          Serial.print("Size of message string 31: ");
          Serial.println(sizeof(can3));
          ultraDataChar.writeValue(can3);
          Serial.println();

          /* Increase the message counter. */
          msg_cnt++;
          count++;

          delay(1000);

          //Soil Moisture 

          memcpy((void *)(soil + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg4(Soil_CAN_ID, 8, soil);
          Serial.println(msg4);
          Serial.print("Size of can message 4: ");
          Serial.println(sizeof(msg4));
          Serial.println("Soil Moisture Sent To RPI");
          String msg4_ID = String(msg4.id, HEX);
          String msg4_DL = String(msg4.data_length, HEX);
          Serial.println(msg4_ID);
          String msg4_D;
          for (int i = 0; i < msg4.data_length; i++) {
            Serial.println(msg4.data[i]);
            if (i >= 1 && (msg4.data[i] <= 0x0F)) {
              msg4_D += String(0) + String(msg4.data[i], HEX); // Add leading zero if necessary
              //Serial.println(count);
            }else{
              msg4_D += String(msg4.data[i], HEX);
            }
            msg4_D.toUpperCase(); // Convert the letters to uppercase
          }
          String can4 = msg4_ID + msg4_DL + msg4_D;
          Serial.println(can4);
          Serial.print("Size of message string 4: ");
          Serial.println(sizeof(can4));
          soilDataChar.writeValue(can4);
          Serial.println();

          delay(1000);
          
          /* Increase the message counter. */
          msg_cnt++;
          count++;

          // Rain Water Level

          memcpy((void *)(rain + 4), &msg_cnt, sizeof(msg_cnt));
          CanMsg const msg5(Rain_CAN_ID, 8, rain);
          Serial.println(msg5);
          Serial.print("Size of can message 5: ");
          Serial.println(sizeof(msg5));
          Serial.println("Rain Water Level Sent To RPI");
          String msg5_ID = String(msg5.id, HEX);
          Serial.println(msg5.id);
          String msg5_DL = String(msg5.data_length, HEX);
          Serial.println(msg5.data_length);
          Serial.println(msg5_ID);
          String msg5_D;
          for (int i = 0; i < msg5.data_length; i++) {
            Serial.println(msg5.data[i]);
            if (i >= 1 && (msg5.data[i] <= 0x0F)) {
              msg5_D += String(0) + String(msg5.data[i], HEX); // Add leading zero if necessary
              //Serial.println(count);
            }else{
              msg5_D += String(msg5.data[i], HEX);
            }
            msg5_D.toUpperCase(); // Convert the letters to uppercase
          }
          Serial.println();
          String can5 = msg5_ID + msg5_DL + msg5_D;
          Serial.println(can5);
          Serial.print("Size of message string 5: ");
          Serial.println(sizeof(can5));
          rainDataChar.writeValue(can5);
          Serial.println();

          /* Increase the message counter. */
          msg_cnt++;
          count++;

          /* Only send one message per 0.1 minutes. */
          delay(6000);
        }
      }
    Serial.println("Line 528");
    }
  }
  ///////////// WIFI PORTION///////////////////////////
  if(connected == "wifi" && mqttClient.connected()){
    // call poll() regularly to allow the library to send MQTT keep alives which
    // avoids being disconnected by the broker
    mqttClient.poll();

    // to avoid having delays in loop, we'll use the strategy from BlinkWithoutDelay
    // see: File -> Examples -> 02.Digital -> BlinkWithoutDelay for more info
    unsigned long currentMillis = millis();
    
    if (currentMillis - previousMillis >= interval) {
      // save the last time a message was sent
      previousMillis = currentMillis;

      /* Assemble a CAN message with the format of
      * 0xCA 0xFE 0x00 0x00 [4 byte message counter]
      */
      /*uint8_t const msg_data[] = {0xCA,0xFE,0,0,0,0,0,0};
      memcpy((void *)(msg_data + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg(CanStandardId(CAN_ID), sizeof(msg_data), msg_data);*/

      //Temperature
      Serial.println("In Loop");
      
      memcpy((void *)(temperature + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg(Temp_CAN_ID, 8, temperature);
      Serial.println("Temperature Sent To RPI");
    

      Serial.print("Sending message to topic: ");
      Serial.println(topic[1]);
      Serial.println(msg);

      // send message, the Print interface can be used to set the message contents
      mqttClient.beginMessage(topic[1]);
      mqttClient.print(msg);
      mqttClient.endMessage();

      Serial.println();

      /* Increase the message counter. */
      msg_cnt++;

      count++;

      delay(1000);

      //Humidity

      memcpy((void *)(humidity + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg2(Humid_CAN_ID, 8, humidity);
      Serial.println("Humdity Sent To RPI");

      Serial.print("Sending message to topic: ");
      Serial.println(topic[0]);
      Serial.println(msg2);

      // send message, the Print interface can be used to set the message contents
      mqttClient.beginMessage(topic[0]);
      mqttClient.print(msg2);
      mqttClient.endMessage();

      Serial.println();

      /* Increase the message counter. */
      msg_cnt++;

      count++;

      delay(1000);

      //Ultrasonic 

      memcpy((void *)(ultrasonic + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg3(Ultra_CAN_ID, 8, ultrasonic);
      Serial.println("Ultrasonic Sent To RPI");

      Serial.print("Sending message to topic: ");
      Serial.println(topic[2]);
      Serial.println(msg3);

      // send message, the Print interface can be used to set the message contents
      mqttClient.beginMessage(topic[2]);
      mqttClient.print(msg3);
      mqttClient.endMessage();

      Serial.println();

      /* Increase the message counter. */
      msg_cnt++;

      count++;

      delay(1000);

      //Soil Moisture 

      memcpy((void *)(soil + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg4(Soil_CAN_ID, 8, soil);
      Serial.println("Soil Moisture Sent To RPI");

      Serial.print("Sending message to topic: ");
      Serial.println(topic[3]);
      Serial.println(msg4);

      // send message, the Print interface can be used to set the message contents
      mqttClient.beginMessage(topic[3]);
      mqttClient.print(msg4);
      mqttClient.endMessage();

      Serial.println();

      delay(1000);
      
      /* Increase the message counter. */
      msg_cnt++;

      count++;

      // Rain Water Level

      memcpy((void *)(rain + 4), &msg_cnt, sizeof(msg_cnt));
      CanMsg const msg5(Rain_CAN_ID, 8, rain);
      Serial.println("Rain Water Level Sent To RPI");

      Serial.print("Sending message to topic: ");
      Serial.println(topic[4]);
      Serial.println(msg5);

      // send message, the Print interface can be used to set the message contents
      mqttClient.beginMessage(topic[4]);
      mqttClient.print(msg5);
      mqttClient.endMessage();

      Serial.println();

      /* Increase the message counter. */
      msg_cnt++;

      count++;

      /* Only send one message per 0.1 minutes. */
      delay(6000);
    }
  }else{
    connected = "";
    setup();
  }
}