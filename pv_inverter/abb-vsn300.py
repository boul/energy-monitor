import requests
import json

__author__ = 'rkuipers'


class Vsn300Reader():

    def __init__(self, host, auth_header, inverter_id):
        
        self.host = host
        self.auth_header = auth_header
        self.inverter_id = inverter_id

    def get_last_stats(self):

        url = "http://" + self.host + "/v1/feeds/"
        device_path = "ser4:" + self.inverter_id
        stats = dict()
        header = self.auth_header

        print "Getting statistics from URL: {0}".format(url)

        r = requests.get(url, headers=header)
        parsed_json = json.loads(r.text)
        path = parsed_json['feeds'][device_path]['datastreams']

        for k, v in path.iteritems():

            print str(k) + " - " + str(v['description']) + " - " + str(
                v['data'][9]['value'])

            stats[k] = v

        return stats

