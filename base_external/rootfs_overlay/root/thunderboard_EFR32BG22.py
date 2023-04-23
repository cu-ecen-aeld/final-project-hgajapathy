#!/usr/bin/python3

from gi.repository import GLib

import signal
import sys
import dbus
import dbus.mainloop.glib
import bluetooth_utils
import bluetooth_constants

import random
import time
from paho.mqtt import client as mqtt_client

sys.path.insert(0, '.')

server = "84:2E:14:31:BA:03"
managed_objects_found = 0
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

broker = 'localhost'
port = 1883
topic = "python/mqtt"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
client = None

def signal_handler(signal, frame):
    print("Disconnecting from " + server)
    disconnect()
    adapter_interface.RemoveDevice("/org/bluez/hci0/dev_84_2E_14_31_BA_03")
    sys.exit(0)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def button_received(interface, changed, invalidated, path):
    if 'Value' in changed:
        button = bluetooth_utils.dbus_to_python(changed['Value'])
        print("Button State: " + str(button[0]))
        client.publish(topic, str(button[0]))

def on_message(client, userdata, msg):
    global lc_path
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    print(" ", msg.payload, type(msg.payload.decode()))
    # char_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,lc_path)
    # char_interface = dbus.Interface(char_proxy, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
    # try:
    #     ascii = bluetooth_utils.text_to_ascii_array(msg.payload.decode())
    #     value = char_interface.WriteValue(ascii, {})
    # except Exception as e:
    #     print("Failed to write to LED Text")
    #     print(e.get_dbus_name())
    #     print(e.get_dbus_message())
    #     return bluetooth_constants.RESULT_EXCEPTION
    # else:
    #     print("LED Text written OK")
    #     return bluetooth_constants.RESULT_OK

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

def disconnect():
    global bus
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

def connect():
    global bus
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
    global bus
    props_interface = dbus.Interface(device_proxy, bluetooth_constants.DBUS_PROPERTIES)
    connected = props_interface.Get(bluetooth_constants.DEVICE_INTERFACE,"Connected")
    return connected

def list_devices_found():
    print("Full list of devices",len(devices),"discovered:")
    print("------------------------------")
    for path in devices:
        dev = devices[path]
        print(bluetooth_utils.dbus_to_python(dev['Address']))

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
    list_devices_found()
    return True

def discover_devices(bus,timeout):
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

    device_list = devices.values()
    discovered_devices = []
    for device in device_list:
        dev = {}
        discovered_devices.append(dev)

    return discovered_devices

def get_known_devices(bus):
    global managed_objects_found

    object_manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, "/"), bluetooth_constants.DBUS_OM_IFACE)
    managed_objects = object_manager.GetManagedObjects()

    for path, ifaces in managed_objects.items():
        for iface_name in ifaces:
            if iface_name == bluetooth_constants.DEVICE_INTERFACE:
                managed_objects_found += 1
                device_properties = ifaces[bluetooth_constants.DEVICE_INTERFACE]
                devices[path] = device_properties

signal.signal(signal.SIGINT, signal_handler)


client = mqtt_client.Client(client_id)
client.on_connect = on_connect
client.connect(broker, port)

client.subscribe("python/reply")
client.on_message = on_message

client.loop_start()

# dbus initialisation steps
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME
device_path = bluetooth_utils.device_address_to_path(server, adapter_path)
device_proxy = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,device_path)
device_interface = dbus.Interface(device_proxy, bluetooth_constants.DEVICE_INTERFACE)

# ask for a list of devices already known to the BlueZ daemon
print("Listing devices already known to BlueZ:")
get_known_devices(bus)
print("Found ",managed_objects_found," managed device objects")

print("Scanning")
discover_devices(bus, 1 * 1000)

print(bool(is_connected(device_proxy)))

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
