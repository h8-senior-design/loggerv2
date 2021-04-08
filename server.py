import socketserver
import socket
import struct
import math
import uuid
import json

last_time = 0
count = 0
still_count = 0
current_log = list()

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def setup(self):
      self.data = list()

    def handle(self):
      global count, last_time, still_count, current_log
      print('connected to new host')
      while True:
        bundled_data = []

        # self.request is the TCP socket connected to the client
        data = self.request.recv(4)
        find_start = struct.unpack_from('I', data)[0]

        while find_start != 0x00000000:
          data = self.request.recv(4)
          if len(data) != 4:
            continue
          find_start = struct.unpack_from('I', data)[0]

        print('found data bundle')
        for _ in range(50):
          data = self.request.recv(56, socket.MSG_WAITALL)
          parsed_data = {
          'accel': list(struct.unpack_from('fff', data)),
          'gyro': list(struct.unpack_from('fff', data, offset=12)),
          'magneto': list(struct.unpack_from('fff', data, offset=24)),
          'yaw': struct.unpack_from('f', data, offset=36)[0],
          'pitch': struct.unpack_from('f', data, offset=40)[0],
          'roll': struct.unpack_from('f', data, offset=44)[0],
          'time': struct.unpack_from('Q', data, offset=48)[0],
          }
          bundled_data.append(parsed_data)

        data = self.request.recv(4, socket.MSG_WAITALL)
        find_end = struct.unpack_from('I', data)[0]
        if find_end != 0xFFFFFFFF:
          print(f'data bundle was corrupted, {find_end}')
          bundled_data.clear()

        print('found end of data bundle')

        if len(bundled_data):
          current_log = []
          for data in bundled_data:
            accel_magnitude = math.sqrt(sum(map(lambda accel_val : accel_val ** 2, data['accel'])))
            data['accelMagnitude'] = accel_magnitude

            if abs(accel_magnitude - 1) < .1:
              if still_count > 4 and len(current_log) > 20:
                fname = uuid.uuid4()
                fd = open(f'data/{fname}.txt', 'w')
                fd.write(json.dumps(current_log))
                fd.close()
                print(f'Writing {len(current_log)} data points to {fname}.txt')
                current_log.clear()

              still_count += 1
              if still_count < 4:
                current_log.append(data)
            else:
              if still_count > 4:
                current_log.clear()
              still_count = 0
              current_log.append(data)


if __name__ == '__main__':
  server = socketserver.TCPServer(('0.0.0.0', 3000), MyTCPHandler)
  server.serve_forever()
