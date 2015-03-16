#import RPi.GPIO as GPIO

#print GPIO.RPI_INFO
#print GPIO.VERSION

import time
from webiopi.devices.analog.mcp3x0x import MCP3002

mcp = MCP3002()

while 1:
    ch0 = mcp.analogRead(0)
    ch1 = mcp.analogRead(1)
    print ch0, ch1
    time.sleep(1)
