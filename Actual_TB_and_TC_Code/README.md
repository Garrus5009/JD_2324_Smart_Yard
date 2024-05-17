The CANconfig.toml file contains the list of all CAN IDs, the device/sensor that ID belongs to, as well as any other necessary information.

The OrigTB.py file contains the python code for the Type-B (Raspberry Pi) device, which contains the code that allows for MQTT communication between Type-A, Type-B, and Type-C devices, as well as BLE communication between Type-A and Type-B.

The copy_Type-C (1).py file contains the python code for the Type-C (Raspberry Pi) device, which contains the code that allows for MQTT/BLE communication between Type-A and Type-C, as well as MQTT communication between Type-C and Type-B.

The flows (10).json file contains the NodeRed flow structure, with all nodes that allow for the influx of information from all device types, and a way to display this incoming information and display it on a dashboard. NodeRed currently is set up to run from the Type-B device.

The Arduino folder contains the following files:

1. A4_copy.ino - This file contains all of the Arduino code that allows it to collect sensor information and send all data to either the Type-B or Type-C device via MQTT or BLE.
2. CANconfig.h - This file isn't strictly necessary, as we aren't using the actual CAN bus, but we've included it from the legacy code provided for the project.
3. arduino_secrets.h - This file contains definitions for the Network SSID and Password, just replace the information there with the information for the Wifi Network that you plan to use.
