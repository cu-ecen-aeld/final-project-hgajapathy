import random

client_id = f'python-mqtt-{random.randint(0, 1000)}'
broker = 'localhost'
port = 1883
publish_topic = 'client/btn_status'
