import urllib
import urllib2
import datetime
import logging


class PvStatus():

    def __init__(self, api_key, sid):
        self.api_key = api_key
        self.sid = sid
        self.url = "http://pvoutput.org/service/r2/addstatus.jsp"

        self.logger = logging.getLogger(__name__)

    def send_metric(self, kwh_generated, watt_ac_generated, kwh_consumed=None,
                    watt_ac_consumed=None, volt_dc=None, temp_c=None):

        now = datetime.datetime.now()

        pvoutput_data = {'key': self.api_key,            # API Key
                         'sid': self.sid,                # (PV-)System ID
                         'd': now.strftime('%Y%m%d'),    # date
                         't': now.strftime('%H:%M'),     # time (now)
                         'c1': 0,
                         'v1': kwh_generated,     # total kWh generation today
                         'v2': watt_ac_generated,        # current output power
                         'v3': kwh_consumed,
                         'v4': watt_ac_consumed,
                         'v5': temp_c,
                         'v6': volt_dc  # current PV voltage
                        }

        encoded_pvoutput_data = urllib.urlencode(pvoutput_data)
        print encoded_pvoutput_data
        # self.logger.debug("Sending data to pvoutput.org {0}")\
        #     .format(encoded_pvoutput_data)

        response = ""
        try:
            request_obj = urllib2.Request(self.url + '?' +
                                          encoded_pvoutput_data)
            response = urllib2.urlopen(request_obj)

        except urllib2.HTTPError as e:
            self.logger.error(e)
            pass

        self.logger.debug(pvoutput_data)
        self.logger.debug(response.read())

        return response.read()