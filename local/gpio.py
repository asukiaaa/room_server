#import RPi.GPIO as GPIO

#print GPIO.RPI_INFO
#print GPIO.VERSION

import webiopi
from webiopi.devices.analog.mcp3x0x import MCP3X0X

class MCP3002(MCP3X0X):
    def __init__(self, chip, channelCount, name):
        MCP3X0X.__init__(self, chip, channelCount, 10, name)

        def __command__(self, channel, diff):
            d = [0x00, 0x00]
            d[0] |= 1 << 6		    # start
            d[0] |= (not diff) << 5	    # SGL
            d[0] |= (channel & 0x01) << 4   # Ch
            d[0] |= (1) << 3                # MBSF
            return d

        def __analogRead__(self, channel, diff):
            data = self.__command__(channel, diff)
            r = self.xfer(data)
            return ((r[0] & self.MSB_MASK) << 8) | r[1]

webiopi.setDebug()

mcp = MCP3002( 0, 2, "MCP3002" )

while 1:
    ch0 = mcp.analogRead(0)
    webiopi.debug( "Ch0 : " + str(ch0) )
    ch1 = mcp.analogRead(1)
    webiopi.debug( "Ch1 : " + str(ch1) )

    webiopi.sleep( 1.0 )
