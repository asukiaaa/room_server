import socket
import json

def index(req):
  return _socket_send( json.dumps({'request': 'status'}) )

def touch(req):
  sending_data = {'twelite_data': { 'digitals': {'1': 1 } } }
  return _socket_send( json.dumps(sending_data) )

def _socket_send(data_to_send):
  soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  soc.connect(('0.0.0.0', 50007))
  soc.send(data_to_send)
  received_data = soc.recv(1024)
  soc.close()
  return received_data

