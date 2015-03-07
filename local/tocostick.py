#!/usr/bin/python
# coding: UTF-8

import socket
import json
import yaml
from serial import *
from sys import stdout, stdin, stderr, exit
from datetime import datetime, timedelta
import os

TWELITE_DEVICE_DIR = '/dev/serial/by-id'
HOST = '0.0.0.0'
PORT = 50007

recomended_to_print = False
if '-p' in sys.argv:
    print 'set recomended_to_print True'
    recomended_to_print = True

class Twelite:
    def __init__(self, serial_port_path = ''):
        if serial_port_path == '':
            for file_name in os.listdir(TWELITE_DEVICE_DIR):
                if 'TWE-Lite' in file_name:
                    serial_port_path = TWELITE_DEVICE_DIR + '/' + file_name
                    break;
        if serial_port_path == '':
            print 'Could not find twelite device'
            exit(0)
        try:
            self.serial_port = Serial(serial_port_path, 115200)
            print "opened serial port: " + serial_port_path
        except:
            print "cannot open serial port: " + serial_port_path
            exit(1)
        self.digital_values = { 1: 0, 2: 0, 3: 0, 4: 0 }
        self.digital_on_at = { 1: 0, 2: 0, 3: 0, 4: 0 }
        self.analog_values = { 1: 0, 2: 0, 3: 0, 4: 0 }

    def upload_digital_values(self):
        new_digital_values = self.read_digital_values_from_hex(self.hex_data)
        for index, digital_value in new_digital_values.items():
            if digital_value == 1:
                self.digital_on_at[index] = datetime.now()
            if self.digital_on_at[index] != 0 and datetime.now() - self.digital_on_at[index] < timedelta(seconds = 1): #1sec
                self.digital_values[index] = 1
            else:
                self.digital_values[index] = 0

    def read_digital_values_from_hex(self, hex_data):
        dibm = hex_data[16]
        dibm_chg = hex_data[17]
        di = {} # 現在の状態
        di_chg = {} # 一度でもLo(1)になったら1
        for i in range(1,5):
            di[i] = 0 if (dibm & 0x1) == 0 else 1
            di_chg[i] = 0 if (dibm_chg & 0x1) == 0 else 1
            dibm >>= 1
            dibm_chg >>= 1
            pass
        return di

    def read_analog_values_from_hex(self, hex_data):
        ad = {}
        er = hex_data[22]
        for i in range(1,5):
            av = hex_data[i + 18 - 1]
            if av == 0xFF:
                # ADポートが未使用扱い(0xFF)なら -1
                ad[i] = -1
            else:
                # 補正ビットを含めた計算
                ad[i] = ((av * 4) + (er & 0x3)) * 4
            er >>= 2
        return ad

    def upload_values(self):
        self.upload_digital_values()
        self.analog_values = self.read_analog_values_from_hex(self.hex_data)

    def listen(self):
        line = self.serial_port.readline().rstrip()
        if len(line) > 0 and line[0] == ':':
            True
            #print "\n%s" % line
        else:
            return False
        lst = map(ord, line[1:].decode('hex')) # HEX文字列を文字列にデコード後、各々 ord() したリストに変換
        csum = sum(lst) & 0xff # チェックサムは 8bit 計算で全部足して　0 なら OK
        lst.pop() # チェックサムをリストから削除
        if csum == 0 and lst[1] == 0x81:
            self.hex_data = lst
            self.upload_values()
            if recomended_to_print:
                self.printPayload()
                print self.digital_on_at
                print self.digital_values
                print self.analog_values
            return True
        else:
            return False

    def printPayload(self):
        l = self.hex_data
        if len(l) != 23: return False # データサイズのチェック

        ladr = l[5] << 24 | l[6] << 16 | l[7] << 8 | l[8]
        print "  src       = 0x%02x" % l[0]
        print "  src long  = 0x%08x" % ladr
        print "  dst       = 0x%02x" % l[9]
        print "  pktid     = 0x%02x" % l[2]
        print "  prtcl ver = 0x%02x" % l[3]
        print "  LQI       = %d / %.2f [dbm]" % (l[4], (7*l[4]-1970)/20.)
        ts = l[10] << 8 | l[11]
        print "  time stmp = %.3f [s]" % (ts / 64.0)
        print "  relay flg = %d" % l[12]
        vlt = l[13] << 8 | l[14]
        print "  volt      = %04d [mV]" % vlt

        return True

    def switch(self, digitals = {}, analogs = {}):
        pins_hex_int   = 0
        values_hex_int = 0
        for pin_number in [1, 2, 3, 4]:
            # pinが設定対象でなければスキップ
            if (not str(pin_number) in digitals.keys()):
                continue
            target_pin_hex_int = 2 ** (pin_number - 1)
            pins_hex_int += target_pin_hex_int
            if (digitals[str(pin_number)] == 1):
                values_hex_int += target_pin_hex_int
        # 0-255の16進数を2桁で取得
        pins_hex_2digit   = hex(pins_hex_int + 256)[-2:]
        values_hex_2digit = hex(values_hex_int + 256)[-2:]
        command = '788001' + values_hex_2digit + pins_hex_2digit + '0000000000000000'
        check_sum = self.check_sum_of(command)
        self.serial_port.write(":" + command + check_sum + "\r\n")

        'needed to make process for analogs'

    def check_sum_of(self, command):
        byte_list = {}
        byte_list = map(ord, command[0:].decode('hex'))
        byte_sum = sum(byte_list)
        check_sum_hex = 0x100 - (byte_sum & 0xff)
        check_sum_2digit = "{:02x}".format(check_sum_hex)
        return check_sum_2digit.upper()

    def analog_value(self, index):
        if index in self.analog_values.keys():
            return self.analog_values[index]
        else:
            return -1

#
# set up
#
myTocostick = Twelite()

#
# main loop
#
while True:
    if myTocostick.listen():
        #print myTocostick.digital_values
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((HOST, PORT))
        sending_data = {
            'twelite_data': {
                'digitals': myTocostick.digital_values,
                'analogs': myTocostick.analog_values
            }
        }
        soc.send( json.dumps(sending_data) )
        #print 'Sended', sending_data
        received_data = yaml.load( soc.recv(1024) )
        #print 'Received', received_data
        if 'new_values' in received_data.keys() and 'digitals' in received_data['new_values'].keys():
            myTocostick.switch(received_data['new_values']['digitals'])
        soc.close()
