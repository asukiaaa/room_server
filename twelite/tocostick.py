#!/usr/bin/python
# coding: UTF-8

###########################################################################
#  (C) Tokyo Cosmos Electric, Inc. (TOCOS) - all rights reserved.
# 利用条件:
#   - 本ソースコードは、別途ソースコードライセンス記述が無い限り東京コスモス電機が著作権を
#     保有しています。
#   - 本ソースコードは、無保証・無サポートです。本ソースコードや生成物を用いたいかなる損害
#     についても東京コスモス電機は保証致しません。不具合等の報告は歓迎いたします。
#   - 本ソースコードは、東京コスモス電機が販売する TWE シリーズと共に実行する前提で公開
#     しています。
###########################################################################

### TWE-Lite 標準アプリケーションを読み出すスクリプト
# ※ 本スクリプトは読み出し専用で、読み書き双方を行うには複数スレッドによる処理が必要になります。
import socket
import json
import yaml
from serial import *
from sys import stdout, stdin, stderr, exit
from datetime import datetime, timedelta

recomended_to_print = False

class Twelite:
    def __init__(self, serial_port_name):
        # シリアルポートを開く
        try:
            self.serial_port = Serial(serial_port_name, 115200)
            print "open serial port: %s" % sys.argv[1]
        except:
            print "cannot open serial port: %s" % sys.argv[1]
            exit(1)

        # 値の初期化
        self.digital_values = { 1: 0, 2: 0, 3: 0, 4: 0 }
        self.digital_on_at = { 1: 0, 2: 0, 3: 0, 4: 0 }
        self.analog_values = { 1: 0, 2: 0, 3: 0, 4: 0 }
        self.analog_reload_at = { 1: 0, 2: 0, 3: 0, 4: 0 }
        
    def read_digital_values_from_hex(self, hex_data):
        # DI1..4 のデータ
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
        # AD1..4 のデータ
        ad = {}
        er = hex_data[22]
        for i in range(1,5):
            av = hex_data[i + 18 - 1]
            if av == 0xFF:
                # ADポートが未使用扱い(おおむね2V以下)なら -1
                ad[i] = -1
            else:
                # 補正ビットを含めた計算
                ad[i] = ((av * 4) + (er & 0x3)) * 4
            er >>= 2
        return ad

    def upload_digital_values(self):
        new_digital_values = self.read_digital_values_from_hex(self.hex_data)
        for index, digital_value in new_digital_values.items():
            if digital_value == 1:
                self.digital_on_at[index] = datetime.now()
            if self.digital_on_at[index] != 0 and datetime.now() - self.digital_on_at[index] < timedelta(microseconds = 500000): #0.5sec
                self.digital_values[index] = 1
            else:
                self.digital_values[index] = 0

    def upload_analog_values(self):
        new_analog_values = self.read_analog_values_from_hex(self.hex_data)
        for index, analog_value in new_analog_values.items():
            if analog_value != -1:
                self.analog_values[index] = analog_value

    def upload_self_values(self):
        self.upload_digital_values()
        self.upload_analog_values()

    def upload(self):
        line = self.serial_port.readline().rstrip() # １ライン単位で読み出し、末尾の改行コードを削除（ブロッキング読み出し）
    
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
            self.upload_self_values()
            if recomended_to_print:
                self.printPayload()
                print self.digital_on_at
                print self.digital_values
                print self.analog_values
            return True
        else:
            return False

    # 0x81 メッセージの解釈と表示
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

    def digital_switch(self, pin_number, value):
        pin_hex_2digit = "{:02x}".format(pin_number)
        value_hex_2digit = '00'
        if value > 0:
            value_hex_2digit = pin_hex_2digit
        command = '788001' + value_hex_2digit + pin_hex_2digit + '0000000000000000'
        check_sum = self.check_sum_of(command)
        self.serial_port.write(":" + command + check_sum + "\r\n")

    def switch(self, digitals, analogs):
        'needed to make'
        #pin_hex_2digit = "{:02x}".format(pin_number)
        #value_hex_2digit = '00'
        #if value > 0:
        #    value_hex_2digit = pin_hex_2digit
        #command = '788001' + value_hex_2digit + pin_hex_2digit + '0000000000000000'
        #check_sum = self.check_sum_of(command)
        #self.serial_port.write(":" + command + check_sum + "\r\n")

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
# メインの処理
#
        
# パラメータの確認
#   第一引数: シリアルポート名
if len(sys.argv) < 2:
    print "%s {serial port name}" % sys.argv[0]
    exit(1)
#TODO 自動的に探したい

myTocostick = Twelite(sys.argv[1])
if '-p' in sys.argv:
    print 'set recomended_to_print True'
    global recomended_to_print
    recomended_to_print = True


while True:
    if myTocostick.upload():
        #print myTocostick.digital_values
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect(('0.0.0.0', 50007))
        sent_data = {
            'twelite_data': {
                'digitals': myTocostick.digital_values,
                'analogs': myTocostick.analog_values
            }
        }
        soc.send( json.dumps(sent_data) )
        #print 'Sended', sent_data
        string_data = soc.recv(1024)
        received_data = yaml.load(string_data)
        #print 'Received', received_data
        if 'new_values' in received_data.keys() and 'digitals' in received_data['new_values'].keys():
            for key, value in received_data['new_values']['digitals'].items():
                myTocostick.digital_switch(int(key), value)
        soc.close()
