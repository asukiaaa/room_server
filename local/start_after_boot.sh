# set path for your device
tocostick='/dev/serial/by-id/usb-TOCOS_TWE-Lite-USB_AHXFIN65-if00-port0'
if [ -e "$tocostick" ]
then
  python /home/pi/room_server/local/socket_server.py &
  python /home/pi/room_server/local/tocostick.py $tocostick &
  echo 'tocostick start'
else
  echo "tocostick $tocostick does not exist"
fi

