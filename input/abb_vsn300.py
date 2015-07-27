import requests
import json
import logging

__author__ = 'rkuipers'


class Vsn300Reader():

    def __init__(self, host, auth_header, inverter_id):
        
        self.host = host
        self.auth_header = auth_header
        self.inverter_id = inverter_id

        self.logger = logging.getLogger(__name__)

    def get_last_stats(self):

        url = "http://" + self.host + "/v1/feeds/"
        device_path = "ser4:" + self.inverter_id
        stats = dict()
        header = self.auth_header

        self.logger.info("Getting statistics from URL: {0}".format(url))

        try:
            r = requests.get(url, headers=header)
        except requests.exceptions.RequestException as e:
            self.logger.error(e)
            pass

        parsed_json = json.loads(r.text)
        path = parsed_json['feeds'][device_path]['datastreams']

        for k, v in path.iteritems():

            # print str(k) + " - " + str(v['description']) + " - " + str(
            #     v['data'][9]['value'])

            stats[k] = v['data'][9]['value']

        self.logger.debug(stats)

        return stats

