__author__ = 'rkuipers'
import socket
import logging
import time

current_time = int(time.time())

class CarbonServer():

    def __init__(self, host, port):

        self.host = host
        self.port = port

        self.logger = logging.getLogger(__name__)

    def send_metric(self, path, value, timestamp=current_time):

        self.logger.debug('Opening Carbon Socket to send metrics')
        sock = socket.socket()

        try:
            sock.connect((self.host, self.port))
        except (socket.error, socket.gaierror) as e:
            self.logger.error(e)
            pass

        message = '%s %s %d\n' % (path, value, timestamp)

        self.logger.debug('Carbon Message: {0}'.format(message))

        sock.sendall(message)

