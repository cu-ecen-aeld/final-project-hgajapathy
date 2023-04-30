#!/usr/bin/python3

import random
import time
import signal
import sys
import dbus
import dbus.mainloop.glib
import bluetooth_utils
import bluetooth_constants
import mqtt_constants

from gi.repository import GLib
from paho.mqtt import client as mqtt_client

sys.path.insert(0, '.')

bus = None
adapter_interface = None
device_interface = None
mainloop = None
timer_id = None

devices = {}

found_bs = False
found_bc = False
found_lc = False
bs_path = None
bc_path = None
lc_path = None

client = None

# Callback for MQTT connect
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

# Button state notification callback
def button_received(interface, changed, invalidated, path):
    if 'Value' in changed:
        button = bluetooth_utils.dbus_to_python(changed['Value'])
        print("Button State: " + str(button[0]))
        client.publish(mqtt_constants.publish_topic, str(button[0]))

# Enable notification for button state characteristics.
def start_notifications():
    global bc_path
    global bus

    char_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, bc_path)
    char_interface = dbus.Interface(char_proxy, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
    bus.add_signal_receiver(button_received,
                            dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
                            signal_name = "PropertiesChanged",
                            path = bc_path,
                            path_keyword = "path")
    try:
        print("Starting notifications")
        char_interface.StartNotify()
        print("Done starting notifications")
    except Exception as e:
        print("Failed to start temperature notifications")
        print(e.get_dbus_name())
        print(e.get_dbus_message())
        return bluetooth_constants.RESULT_EXCEPTION
    else:
        return bluetooth_constants.RESULT_OK

def service_discovery_completed():
    bus.remove_signal_receiver(sd_interfaces_added,"InterfacesAdded")
    bus.remove_signal_receiver(sd_properties_changed,"PropertiesChanged")
    start_notifications()

def sd_properties_changed(interface, changed, invalidated, path):
    global device_path

    if path != device_path:
        return
    if 'ServicesResolved' in changed:
        sr = bluetooth_utils.dbus_to_python(changed['ServicesResolved'])
        print("ServicesResolved  : ", sr)
        if sr == True:
            service_discovery_completed()

def sd_interfaces_added(path, interfaces):
    global found_bs
    global found_bc
    global found_lc
    global bs_path
    global bc_path
    global lc_path

    if bluetooth_constants.GATT_SERVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_SERVICE_INTERFACE]
        print("--------------------------------------------------------------------------------")
        print("SVC path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            if uuid == bluetooth_constants.BUTTON_SVC_UUID:
                found_bs = True
                bs_path = path
            print("SVC UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("SVC name   : ", bluetooth_utils.get_name_from_uuid(uuid))
        return
    if bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE]
        print("  CHR path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            if uuid == bluetooth_constants.BUTTON_CHR_UUID:
                found_bc = True
                bc_path = path
            elif uuid == bluetooth_constants.LED_CHR_UUID:
                found_lc = True
                lc_path = path
            print("  CHR UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("  CHR name   : ", bluetooth_utils.get_name_from_uuid(uuid))
            flags  = ""
            for flag in properties['Flags']:
                flags = flags + flag + ","
            print("  CHR flags  : ", flags)
        return
    if bluetooth_constants.GATT_DESCRIPTOR_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.GATT_DESCRIPTOR_INTERFACE]
        print("    DSC path   :", path)
        if 'UUID' in properties:
            uuid = properties['UUID']
            print("    DSC UUID   : ", bluetooth_utils.dbus_to_python(uuid))
            print("    DSC name   : ", bluetooth_utils.get_name_from_uuid(uuid))
        return

def connect():
    global device_interface

    try:
        device_interface.Connect()
    except Exception as e:
        print("Failed to connect")
        print(e.get_dbus_name())
        print(e.get_dbus_message())
        if ("UnknownObject" in e.get_dbus_name()):
            print("Try scanning first to resolve this problem")
        return bluetooth_constants.RESULT_EXCEPTION
    else:
        print("Connected OK")
        return bluetooth_constants.RESULT_OK

def is_connected(device_proxy):
    props_interface = dbus.Interface(device_proxy, bluetooth_constants.DBUS_PROPERTIES)
    connected = props_interface.Get(bluetooth_constants.DEVICE_INTERFACE,"Connected")
    return connected

def dd_interfaces_added(path, interfaces):
    # interfaces is an array of dictionary entries
    if not bluetooth_constants.DEVICE_INTERFACE in interfaces:
        return
    device_properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
    if path not in devices:
        devices[path] = device_properties
        dev = devices[path]

def dd_interfaces_removed(path, interfaces):
    # interfaces is an array of dictionary strings in this signal
    if not bluetooth_constants.DEVICE_INTERFACE in interfaces:
        return
    if path in devices:
        dev = devices[path]
        del devices[path]

def dd_properties_changed(interface, changed, invalidated, path):
    if interface != bluetooth_constants.DEVICE_INTERFACE:
        return
    if path in devices:
        devices[path] = dict(devices[path].items())
        devices[path].update(changed.items())
    else:
        devices[path] = changed
    dev = devices[path]

# we don't need the signals registered when device discovery
# timeout ends
def discovery_timeout():
    global adapter_interface
    global mainloop
    global timer_id

    GLib.source_remove(timer_id)
    mainloop.quit()
    adapter_interface.StopDiscovery()
    bus = dbus.SystemBus()
    bus.remove_signal_receiver(dd_interfaces_added,"InterfacesAdded")
    bus.remove_signal_receiver(dd_interfaces_added,"InterfacesRemoved")
    bus.remove_signal_receiver(dd_properties_changed,"PropertiesChanged")
    return True

# discover devices, characteristics and descriptor usineg
# d-bus signals (InterfacesAdded, InterfacesRemoved, and PropertiesChanged)
# and callback interface
def discover_devices(bus, timeout):
    global adapter_interface
    global mainloop
    global timer_id

    # acquire the adapter interface so we can call its methods
    adapter_object = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_path)
    adapter_interface=dbus.Interface(adapter_object, bluetooth_constants.ADAPTER_INTERFACE)

    # register signal handler functions so we can asynchronously report discovered devices
    # InterfacesAdded signal is emitted by BlueZ when an advertising packet from a device it doesn't
    # already know about is received
    bus.add_signal_receiver(dd_interfaces_added,
            dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
            signal_name = "InterfacesAdded")

    # InterfacesRemoved signal is emitted by BlueZ when a device "goes away"
    bus.add_signal_receiver(dd_interfaces_removed,
            dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
            signal_name = "InterfacesRemoved")

    # PropertiesChanged signal is emitted by BlueZ when something re: a device already encountered
    # changes e.g. the RSSI value
    bus.add_signal_receiver(dd_properties_changed,
           dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
            signal_name = "PropertiesChanged",
            path_keyword = "path")

    mainloop = GLib.MainLoop()
    timer_id = GLib.timeout_add(timeout, discovery_timeout)
    adapter_interface.StartDiscovery(byte_arrays=True)
    mainloop.run()

# disconnect from device and mqtt broker
# this is needed when we are running this script again to connect
# to the same device
def disconnect():
    global device_interface

    try:
        device_interface.Disconnect()
    except Exception as e:
        print("Failed to disconnect")
        print(e.get_dbus_name())
        print(e.get_dbus_message())
        return bluetooth_constants.RESULT_EXCEPTION
    else:
        print("Disconnected OK")
        return bluetooth_constants.RESULT_OK

# Disconnect from device and exit gracefully
def signal_handler(signal, frame):
    print("Disconnecting from " + bdaddr)
    disconnect()
    adapter_interface.RemoveDevice(device_path)
    sys.exit(0)

# read bluetooth device address to connect
if (len(sys.argv) != 2):
    print("usage: python3 client.py [bdaddr]")
    sys.exit(1)

bdaddr = sys.argv[1]

# install signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# setup MQTT client
client = mqtt_client.Client(mqtt_constants.client_id)
client.on_connect = on_connect
client.connect(mqtt_constants.broker, mqtt_constants.port)
client.loop_start()

# dbus initialisation
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME
print("adapter_path: " + adapter_path)

device_path = bluetooth_utils.device_address_to_path(bdaddr, adapter_path)
print("device_path:  " + device_path)

device_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, device_path)
device_interface = dbus.Interface(device_proxy, bluetooth_constants.DEVICE_INTERFACE)

# before connecting to the device, bluez daemon must scan
# near-by devices and discover its services
print("Scanning")
discover_devices(bus, 1 * 1000)

if is_connected(device_proxy) == False:
    connect()

print("Discovering services")
bus.add_signal_receiver(sd_interfaces_added,
        dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
        signal_name = "InterfacesAdded")

bus.add_signal_receiver(sd_properties_changed,
        dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
        signal_name = "PropertiesChanged",
        path_keyword = "path")

mainloop.run()
