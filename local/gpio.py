#import RPi.GPIO as GPIO

#print GPIO.RPI_INFO
#print GPIO.VERSION

import time
from webiopi.devices.analog.mcp3x0x import MCP3002

HOST = '0.0.0.0'
PORT = 50007

mcp = MCP3002()

while 1:
    ch0 = mcp.analogRead(0)
    ch1 = mcp.analogRead(1)
    soc.connect((HOST, PORT))
    print ch0, ch1
    time.sleep(1)
    air_conditioner_status = true if ch0 > 100 else false
    sending_data = {
        'uploading_data': {
            'air_conditioner_status': air_conditioner_status
            #'face_height_temperature': ch1
        }
    }
    soc.send( json.dumps(sending_data) )
    soc.close()
