#!/usr/bin/python
# coding: UTF-8

import socket
import sys
import time
import json
import yaml
import datetime
import time
from multiprocessing import Process
import RPi.GPIO as GPIO

HOST = '0.0.0.0'
PORT = 50007
s = None

DIGITAL_ON_BUFFER_TIME = datetime.timedelta(seconds = 1)

# uploading data
# enumとかにして、まとめて管理したい
AIR_CONDITIONER_LED    = 'air_conditioner_led'
AIR_CONDITIONER_BUTTON = 'air_conditioner_button'
TEMPERATURE_NEAR_FACE  = 'temperature_near_face'
TEMPERATURE_NEAR_FLOOR = 'temperature_near_floor'
CIRCURATOR             = 'circurator'

# gpio pins
AIR_CONDITIONER_BUTTON_PIN = 17 

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(AIR_CONDITIONER_BUTTON_PIN, GPIO.OUT)

# これをjson変換時にdefaultに渡すことでdatatimeを期待撮りに変換
datetime_handler = lambda obj : (
  obj.isoformat()
  if isinstance(obj, datetime.datetime)
  or isinstance(obj, datetime.date)
  else None)

for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
    af, socktype, proto, acnonname, sa = res
    try:
        s = socket.socket(af, socktype, proto)
    except socket.error, msg:
        s = None
        continue
    try:
        s.bind(sa)
        s.listen(1)
    except socket.error, msg:
        s.close()
        s = None
        continue
    break

if s is None:
    print 'could not open socket'
    sys.exit(1)

def air_conditioner_switcher():
    GPIO.output(AIR_CONDITIONER_BUTTON_PIN, 1)
    time.sleep(1)
    GPIO.output(AIR_CONDITIONER_BUTTON_PIN, 0)

class Room:
    def __init__(self):
        self.status = {}
        self.status_at = {}
        for status_name in [AIR_CONDITIONER_LED, AIR_CONDITIONER_BUTTON, TEMPERATURE_NEAR_FLOOR, CIRCURATOR]:
            self.status[status_name] = 0
            self.status_at[status_name] = 0
        

    def upload(self, uploading_data):
        uploading_keys = uploading_data.keys()
        for status_name in [AIR_CONDITIONER_LED, TEMPERATURE_NEAR_FLOOR, AIR_CONDITIONER_BUTTON]:
            if status_name in uploading_keys:
                self.status[status_name] = uploading_data[status_name]
                self.status_at[status_name] = datetime.datetime.now()
        self.status[CIRCURATOR] = self.air_conditioner_is_on()
        if self.status[AIR_CONDITIONER_BUTTON]:
            self.status[AIR_CONDITIONER_BUTTON] = False
            p = Process(target=air_conditioner_switcher)
            p.start()

    def air_conditioner_is_on(self):
        uploaded_time = self.status_at[AIR_CONDITIONER_LED]
        if uploaded_time == 0 or datetime.datetime.now() - uploaded_time > DIGITAL_ON_BUFFER_TIME:
            return False
        return self.status[AIR_CONDITIONER_LED]

    def _temperature_of(self, value_mv):
        return ( value_mv - 600 ) / 10

    def get_all_status(self):
        status = {}
        status['status']          = self.status
        status['status_at']       = self.status_at
        return status

reivoRoom = Room()

while True:
    #print json.dumps(reivoRoom.get_all_status(), sort_keys=True, indent=2, default=datetime_handler)
    conn, addr = s.accept()
    received_hash = yaml.load( conn.recv(1024) )
    #print 'received', received_hash
    sending_data = {}
    hash_keys = received_hash.keys() if isinstance(received_hash, dict) else []
    if 'uploading_data' in hash_keys:
        reivoRoom.upload(received_hash['uploading_data'])
        sending_data = reivoRoom.get_all_status()
    if 'request' in hash_keys:
        request_type = received_hash['request']
        if request_type == 'status':
            sending_data = reivoRoom.get_all_status()
    #print 'send', sending_data
    conn.send( json.dumps(sending_data, sort_keys=True, indent=2, default=datetime_handler) )
    conn.close
