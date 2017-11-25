import urllib2
import json
import logging

bla = '{"retrieve_message":{"seqnr":0,"account_auth":{"user_account":"","mac_address":"energy-monitor"},"info":127}}'
# data = urllib.urlencode(bla)
url = "http://10.0.3.125:10000/retrieve/"


class AtagOneReader():
    def __init__(self, host, timeout=10, simulate=False):
        self.url = "http://"+host+":10000/retrieve/"
        self.login_request = '{"retrieve_message":{"seqnr":0,"account_auth":' \
                             '{"user_account":"","mac_address":"energy-monitor"},"info":127}}'
        self.simulate = simulate
        self.timeout = timeout

        self.logger = logging.getLogger(__name__)

    def get_data(self):

        self.logger.info("Getting Atag One stats from: {0}".format(self.url))

        try:

            json_response = urllib2.urlopen(url=self.url, data=self.login_request, timeout=self.timeout)
            parsed_json = json.load(json_response)
            self.logger.debug("Raw Response {0}".format(parsed_json))

        except Exception as e:
            self.logger.error(e)
            return

        return parsed_json

        # parsed_json = json.load(json_response)
        # print "json"
        # print parsed_json
        #
        # print type(parsed_json)
        # status = parsed_json['retrieve_reply']['status']
        # print status
        # report = parsed_json['retrieve_reply']['report']
        # print report
        # control = parsed_json['retrieve_reply']['control']
        # print control
        # config = parsed_json['retrieve_reply']['configuration']