import json
import urllib2
import logging

__author__ = 'rkuipers'


class Connection():

    def __init__(self, url, username, password):

        self.url = url
        self.username = username
        self.password = password

        self.logger = logging.getLogger(__name__)

    def update_sensor(self, idx, value):

        url = self.url + "/json.htm?type=command&param=udevice&idx=" \
              + str(idx) + "&nvalue=0&svalue=" + str(value)

        self.logger.debug("Updating sensor: {0}".format(url))

        try:

            request = urllib2.Request(url=url)
            response_body = urllib2.urlopen(request).read()
            response = json.loads(response_body)
        except Exception as e:
            self.logger.error("Error on updating sensors: {0}".format(e))
            return

        return response
