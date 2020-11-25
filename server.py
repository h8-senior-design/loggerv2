import socketserver
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
        # self.request is the TCP socket connected to the client
        self.data.extend(list(self.request.recv(128)))
        while len(self.data) >= 60:
          end_index = 0
          while struct.unpack_from('I', bytes(self.data), offset=end_index)[0] != 0xDEADBEEF:
            end_index += 1
            if end_index == len(self.data) - 4:
              break
          if end_index < 56:
            print(f'discarding {end_index} bytes from partial struct')
            del self.data[0:end_index + 4]
            break
          print(f'found data struct ending at byte offset {end_index}')
          if end_index > 56:
            print(f'removing first {end_index - 56} bytes')
            del self.data[0:end_index - 56]
          
          data = bytes(self.data[0:60])
          del self.data[0:60]
          
          parsed_data = {
          'accel': list(struct.unpack_from('fff', data)),
          'gyro': list(struct.unpack_from('fff', data, offset=12)),
          'magneto': list(struct.unpack_from('fff', data, offset=24)),
          'yaw': struct.unpack_from('f', data, offset=36)[0],
          'pitch': struct.unpack_from('f', data, offset=40)[0],
          'roll': struct.unpack_from('f', data, offset=44)[0],
          'time': struct.unpack_from('Q', data, offset=48)[0],
          'verify': struct.unpack_from('I', data, offset=56)[0],
          }
          last_time = parsed_data['time']
          accel_magnitude = math.sqrt(sum(map(lambda accel_val : accel_val ** 2, parsed_data['accel'])))
          parsed_data['accelMagnitude'] = accel_magnitude

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
              current_log.append(parsed_data)
          else:
            if still_count > 4:
              current_log.clear()
            still_count = 0
            current_log.append(parsed_data)

        count += 1
        if count % 10 == 0:
          # print(f'delta-t: {(parsed_data["time"] - last_time) / 1000}')
          # print("{} wrote {}".format(self.client_address[0], parsed_data))
          pass


if __name__ == '__main__':
  server = socketserver.TCPServer(('0.0.0.0', 3000), MyTCPHandler)
  server.serve_forever()
