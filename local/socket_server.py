#!/usr/bin/python
# coding: UTF-8

import socket
import sys
import time
import json
import yaml
import datetime

HOST = '0.0.0.0'
PORT = 50007
s = None

AIR_CONDITIONER_SENSOR_PORT  = '1'
TERMO_SENSOR_NEAR_FLOOR_PORT = '2'
TERMO_SENSOR_NEAR_FACE_PORT  = '3'

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

class Room:
    def __init__(self):
        self.twelite = {}
        # 1: Solenoid, 2: Circurator
        self.twelite['digitals'] = {'1': 0, '2': 0, '3': 0, '4': 0 }
        self.twelite['digitals_on_at'] = {'1': 0, '2': 0, '3': 0, '4': 0 }

        # 4: air conditioner light sensor
        self.twelite['analogs'] = {'1': 0, '2': 0, '3': 0, '4': 0 }
        self.twelite['analogs_reloaded_at'] = {'1': 0, '2': 0, '3': 0, '4': 0 }

    def upload_with_twelite(self, twelite_data):
        #upload digital values
        if 'digitals' in twelite_data.keys():
            for key, value in twelite_data['digitals'].items():
                if twelite_data['digitals'][key] == 1:
                    self.twelite['digitals_on_at'][key] = datetime.datetime.now()
                uploaded_time = self.twelite['digitals_on_at'][key]
                if uploaded_time != 0 and datetime.datetime.now() - uploaded_time < datetime.timedelta(microseconds = 500000): # 0.5sec
                    self.twelite['digitals'][key] = 1
                else:
                    self.twelite['digitals'][key] = 0
        #upload analog values
        if 'analogs' in twelite_data.keys():
            for key, value in twelite_data['analogs'].items():
                if twelite_data['analogs'][key] > 0:
                    self.twelite['analogs'][key] = twelite_data['analogs'][key]
                    self.twelite['analogs_reloaded_at'][key] = datetime.datetime.now()

    def air_conditioner_is_on(self):
        if not self._analog_port_is_active(AIR_CONDITIONER_SENSOR_PORT):
            return False
        return self.twelite['analogs'][AIR_CONDITIONER_SENSOR_PORT] > 100

    def needed_to_touch_solenoid(self):
        return self.twelite['digitals']['1'] == 1

    def new_twelite_values(self):
        new_digital_values = {}
        new_analog_values = {}
        new_digital_values['2'] = 1 if self.air_conditioner_is_on() else 0
        new_digital_values['1'] = 1 if self.needed_to_touch_solenoid() else 0
        return { 'digitals': new_digital_values, 'analogs': new_analog_values }

    def temperature_near_face(self):
        return self._temperature_of(TERMO_SENSOR_NEAR_FACE_PORT)

    def temperature_near_floor(self):
        return self._temperature_of(TERMO_SENSOR_NEAR_FLOOR_PORT)

    def _temperature_of(self, analog_port_index):
        if not self._analog_port_is_active(analog_port_index):
            return ''
        value_mv = self.twelite['analogs'][analog_port_index]
        return ( value_mv - 600 ) / 10

    def _analog_port_is_active(self, port_index):
        reloaded_time = self.twelite['analogs_reloaded_at'][port_index]
        if reloaded_time != 0 and datetime.datetime.now() - reloaded_time < datetime.timedelta(seconds = 10):
            return True
        else:
            return False

    def status(self):
        status = {}
        status['air_conditioner'] = self.air_conditioner_is_on()
        status['twelite']         = self.twelite
        status['temperatures'] = {
            'face': self.temperature_near_face(),
            'floor': self.temperature_near_floor()
        }
        return status

reivoRoom = Room()

while True:
    #print json.dumps(reivoRoom.status(), sort_keys=True, indent=2, default=datetime_handler)
    conn, addr = s.accept()
    received_hash = yaml.load( conn.recv(1024) )
    #print 'received', received_hash
    sending_data = {}
    hash_keys = received_hash.keys()
    if 'twelite_data' in hash_keys:
        reivoRoom.upload_with_twelite(received_hash['twelite_data'])
        sending_data['status'] = 'got it'
        sending_data['new_values'] = reivoRoom.new_twelite_values()
    if 'request' in hash_keys:
        request_type = received_hash['request']
        if request_type == 'status':
            sending_data = reivoRoom.status()
    #print 'send', sending_data
    conn.send( json.dumps(sending_data, sort_keys=True, indent=2, default=datetime_handler) )
    conn.close
