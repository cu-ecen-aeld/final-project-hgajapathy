#!/usr/bin/python3

# This file contains all the constants needed for this project

ADAPTER_NAME = "hci0"
BLUEZ_SERVICE_NAME = "org.bluez"
BLUEZ_NAMESPACE = "/org/bluez/"
DBUS_PROPERTIES="org.freedesktop.DBus.Properties"
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
ADAPTER_INTERFACE = BLUEZ_SERVICE_NAME + ".Adapter1"
DEVICE_INTERFACE = BLUEZ_SERVICE_NAME + ".Device1"
GATT_MANAGER_INTERFACE = BLUEZ_SERVICE_NAME + ".GattManager1"
GATT_SERVICE_INTERFACE = BLUEZ_SERVICE_NAME + ".GattService1"
GATT_CHARACTERISTIC_INTERFACE = BLUEZ_SERVICE_NAME + ".GattCharacteristic1"
GATT_DESCRIPTOR_INTERFACE = BLUEZ_SERVICE_NAME + ".GattDescriptor1"

RESULT_OK = 0
RESULT_ERR = 1
RESULT_ERR_NOT_CONNECTED = 2
RESULT_ERR_NOT_SUPPORTED = 3
RESULT_ERR_SERVICES_NOT_RESOLVED = 4
RESULT_ERR_WRONG_STATE = 5
RESULT_ERR_ACCESS_DENIED = 6
RESULT_EXCEPTION = 7
RESULT_ERR_BAD_ARGS = 8
RESULT_ERR_NOT_FOUND = 9

UUID_NAMES = {
    "00001801-0000-1000-8000-00805f9b34fb" : "Generic Attribute Service",
    "0000180a-0000-1000-8000-00805f9b34fb" : "Device Information Service",
    "e95d93b0-251d-470a-a062-fa1922dfa9a8" : "DFU Control Service",
    "e95d93af-251d-470a-a062-fa1922dfa9a8" : "Event Service",
    "e95d9882-251d-470a-a062-fa1922dfa9a8" : "Button Service",
    "e95d6100-251d-470a-a062-fa1922dfa9a8" : "Temperature Service",
    "e95dd91d-251d-470a-a062-fa1922dfa9a8" : "LED Service",
    "00002a05-0000-1000-8000-00805f9b34fb" : "Service Changed",
    "e95d93b1-251d-470a-a062-fa1922dfa9a8" : "DFU Control",
    "00002a05-0000-1000-8000-00805f9b34fb" : "Service Changed",
    "00002a24-0000-1000-8000-00805f9b34fb" : "Model Number String",
    "00002a25-0000-1000-8000-00805f9b34fb" : "Serial Number String",
    "00002a26-0000-1000-8000-00805f9b34fb" : "Firmware Revision String",
    "e95d9775-251d-470a-a062-fa1922dfa9a8" : "micro:bit Event",
    "e95d5404-251d-470a-a062-fa1922dfa9a8" : "Client Event",
    "e95d23c4-251d-470a-a062-fa1922dfa9a8" : "Client Requirements",
    "e95db84c-251d-470a-a062-fa1922dfa9a8" : "micro:bit Requirements",
    "e95dda90-251d-470a-a062-fa1922dfa9a8" : "Button A State",
    "e95dda91-251d-470a-a062-fa1922dfa9a8" : "Button B State",
    "e95d9250-251d-470a-a062-fa1922dfa9a8" : "Temperature",
    "e95d93ee-251d-470a-a062-fa1922dfa9a8" : "LED Text",
    "00002902-0000-1000-8000-00805f9b34fb" : "Client Characteristic Configuration",
}

# These UUIDs are unique for EFR32BG22 Thunderboard Kit SoC Blinky example
BUTTON_SVC_UUID = "de8a5aac-a99b-c315-0c80-60d4cbb51224"
BUTTON_CHR_UUID = "61a885a4-41c3-60d0-9a53-6d652a70d29c"
LED_CHR_UUID    = "5b026510-4088-c297-46d8-be6c736a087a"
