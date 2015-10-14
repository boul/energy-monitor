import random
import time
import base64
import json
import urllib2
import logging
from hashlib import sha1 as _sha, md5 as _md5

__author__ = 'rkuipers'


class Connection():

    def __init__(self, api_key, username, app_key, app_secret):

        self.api_key = api_key
        self.username = username
        self.app_key = app_key
        self.app_secret = app_secret
        self.usertoken = api_key + '.' + username
        self.passtoken = app_key + '.' + app_secret
        self.api_host= 'enelogic.com'
        self.api_url= 'https://enelogic.com/api'

        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _cnonce():
        dig = _md5("%s:%s" % (time.ctime(),
                              ["0123456789"[random.randrange(0, 9)]
                               for i in range(20)])).hexdigest()
        return dig[:16]

    @staticmethod
    def _wsse_username_token(cnonce, iso_now, password):

        return base64.b64encode(_sha("%s%s%s" % (cnonce,
                                                 iso_now,
                                                 password)).digest()).strip()

    def _get_wsse_header(self):

        nonce = self._cnonce()
        iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        password_digest = self._wsse_username_token(nonce, iso_now,
                                                    self.passtoken)
        base64_nonce = base64.b64encode(nonce)

        wsse_header = 'UsernameToken Username="%s",' \
                      ' PasswordDigest="%s", Nonce="%s",' \
                      ' Created="%s"' % (self.usertoken,
                                         password_digest,
                                         base64_nonce,
                                         iso_now)

        return wsse_header

    def get_request(self, path):

        url = self.api_url + "/" + path + "/"
        wsse_header = self._get_wsse_header()
        headers = {'Content-type': 'application/json',
                   'X-WSSE': wsse_header
                   }

        request = urllib2.Request(url=url, headers=headers)
        response_body = urllib2.urlopen(request).read()
        response = json.loads(response_body)

        return response


    # def get_measuringdevices(self):
    #
    #     response = self.make_request("GET", "/api/measuringdevices/")
    #
    #
    #
    #     return response
    #
    # def get_measuringpoints(self):
    #
    #     response = self.make_request("GET", "/api/measuringpoints/")
    #
    #
    #
    #     return response

    def create_measuringpoint(self, building_id, label, type=0,
                              active=True, generation=False):

        values = json.dumps({
        "buildingId": building_id,
        "label": label,
        "unitType": type,
        "active": active,
        "generation": generation

        })


        url = self.api_url + "/measuringpoints/"
        wsse_header = self._get_wsse_header()
        headers = {'Content-type': 'application/json',
                   'X-WSSE': wsse_header
                   }

        request = urllib2.Request(url=url, data=values, headers=headers)
        response_body = urllib2.urlopen(request).read()
        response = json.loads(response_body)

        return response

    def update_measuringpoint(self, building_id, label, type=0,
                              active=True, generation=False):

        values = json.dumps({
        "buildingId": building_id,
        "label": label,
        "active": active,
        "generation": generation
        })


        url = self.api_url + "/measuringpoints/"
        wsse_header = self._get_wsse_header()
        headers = {'Content-type': 'application/json',
                   'X-WSSE': wsse_header
                   }

        request = urllib2.Request(url=url, data=values, headers=headers)
        request.get_method = lambda: 'PUT'
        response_body = urllib2.urlopen(request).read()
        response = json.loads(response_body)

        return response

    def create_datapoint(self, quantity, rate, datetime, measuringpoint_id):

        # Datapoints
        # Rates:
        # 180 = total consumption (low tariff + normal tariff)
        # 280 = total returned energy (e.g. solar panels)
        #
        # 181 = total consumption (low tariff)
        # 182 = total consumption (normal tariff)
        # 281 = total returned energy (low tariff)
        # 282 = total returned energy (normal tariff)

        values = json.dumps({
        "quantity": quantity,
        "rate": rate,
        "datetime": datetime
        })

        url = self.api_url + "/measuringpoints/" + str(measuringpoint_id) +\
              "/datapoints/"
        wsse_header = self._get_wsse_header()
        headers = {'Content-type': 'application/json',
                   'X-WSSE': wsse_header
                   }

        self.logger.debug("Data: {0} URL: {1} Headers: {2}".
                          format(url, values, headers))

        try:
            request = urllib2.Request(url=url, data=values, headers=headers)
            response_body = urllib2.urlopen(request).read()
            response = json.loads(response_body)
            self.logger.debug("Response: {0}".format(response))

        except Exception as e:
            self.logger.error(e)
            return

        return response

#
#
# def main():
#
#     now = datetime.datetime.now()
#     date_now = now.strftime('%Y%m%d')
#     time_now = now.strftime('%H:%M')
#     current_datetime = now.strftime('%Y-%m-%d %H:%M:%S')
#     print current_datetime
#     bla = Connection(api_key,username,app_key,app_secret)
#
#     # blaat = bla.get_request('buildings')
#     #
#     # for k in blaat:
#     #     print k
#
#     devices = bla.get_request('measuringdevices')
#
#     for k in devices:
#
#         print k
#
#     points = bla.get_request('measuringpoints')
#
#     for k in points:
#
#         print "output key: {0}".format(k)
#
#     print
#     #create_point = bla.create_datapoint(14.00, 180, current_datetime, 90542)
#     #print create_point
#
#
#
#     # bla = bla.create_measuringpoint(39024,'YouLess', 0,True, False)
#     # bla = bla.update_measuringpoint(39024, 'Test_Elektra2', 0, True, True)
#
#     # bla = bla.create_measuringpoint()
#     # print bla
#
#     #for k,v in device.iter
#
#
# if __name__ == "__main__":
#
#     try:
#         main()
#     except KeyboardInterrupt:
#         # quit
#         print "...Ctrl-C received!... exiting"
#         sys.exit()
