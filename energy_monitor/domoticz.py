import json
import urllib2
import logging

__author__ = 'rkuipers'


class Connection():

    def __init__(self, username, password, url):

        self.url = url
        self.username = username
        self.password = password

        self.logger = logging.getLogger(__name__)

    def update_sensor(self, idx, value):

        url = self.url + "/json.htm?type=command&param=udevice&idx=" \
              + idx + "&nvalue=0&svalue=" + value

        request = urllib2.Request(url=url)
        response_body = urllib2.urlopen(request).read()
        response = json.loads(response_body)

        return response
