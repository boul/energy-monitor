import json
import urllib2
import urllib
import logging

__author__ = 'rkuipers'


class Connection():

    def __init__(self, api_key):

        # self.url = url
        # self.username = username
        # self.password = password
        self.api_key = api_key

        self.logger = logging.getLogger(__name__)

    def add_input(self, node, value):

        self.logger.debug("Adding input: {0}".format(value))
        value = urllib.quote(value)

        url = "https://emoncms.org/input/post?" + "&node=" + node + "&json=" + value + "&apikey="\
              + self.api_key
        self.logger.debug("Adding input on URL: {0}".format(url))

        try:

            request = urllib2.Request(url=url)
            response_body = urllib2.urlopen(request).read()
            # response = json.loads(response_body)

            self.logger.debug("Response: {0}".format(response_body))

        except Exception as e:
            self.logger.error("Error on on adding input: {0}".format(e))
            return

        return response_body
