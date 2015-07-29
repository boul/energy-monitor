import urllib
import urllib2
import datetime
import logging
import httplib


class Connection():
    def __init__(self, api_key, system_id, host='pvoutput.org'):
        self.host = host
        self.api_key = api_key
        self.system_id = system_id

    def add_output(self, date, generated, exported=None, peak_power=None, peak_time=None, condition=None,
            min_temp=None, max_temp=None, comments=None, import_peak=None, import_offpeak=None, import_shoulder=None):
        """
        Uploads end of day output information
        """
        path = '/service/r1/addoutput.jsp'
        params = {
                'd': date,
                'g': generated
                }
        if exported:
            params['e'] = exported
        if peak_power:
            params['pp'] = peak_power
        if peak_time:
            params['pt'] = peak_time
        if condition:
            params['cd'] = condition
        if min_temp:
            params['tm'] = min_temp
        if max_temp:
            params['tx'] = max_temp
        if comments:
            params['cm'] = comments
        if import_peak:
            params['ip'] = import_peak
        if import_offpeak:
            params['op'] = import_offpeak
        if import_shoulder:
            params['is'] = import_shoulder

        response = self.make_request('POST', path, params)

        # if response.status == 400:
        #     raise ValueError(response.read())
        # if response.status != 200:
        #     raise StandardError(response.read())

        return response.read()

    def add_status(self, date, time, energy_exp=None, power_exp=None, energy_imp=None, power_imp=None, temp=None, vdc=None, cumulative=False):
        """
        Uploads live output data
        """
        path = '/service/r2/addstatus.jsp'
        params = {
                'd': date,
                't': time
                }
        if energy_exp:
            params['v1'] = energy_exp
        if power_exp:
            params['v2'] = power_exp
        if energy_imp:
            params['v3'] = energy_imp
        if power_imp:
            params['v4'] = power_imp
        if temp:
            params['v5'] = temp
        if vdc:
            params['v6'] = vdc
        if cumulative:
            params['c1'] = 1
        params = urllib.urlencode(params)

        response = self.make_request('POST', path, params)

        # if response.status == 400:
        #     raise ValueError(response.read())
        # if response.status != 200:
        #     raise StandardError(response.read())

        return response

    def get_status(self, date=None, time=None):
        """
        Retrieves status information
        """
        path = '/service/r1/getstatus.jsp'
        params = {}
        if date:
            params['d'] = date
        if time:
            params['t'] = time
        params = urllib.urlencode(params)

        response = self.make_request("GET", path, params)

        if response.status == 400:
            raise ValueError(response.read())
        if response.status != 200:
            raise StandardError(response.read())

        return response.read()

    def delete_status(self, date, time):
        """
        Removes an existing status
        """
        path = '/service/r1/deletestatus.jsp'
        params = {
                'd': date,
                't': time
                }
        params = urllib.urlencode(params)

        response = self.make_request("POST", path, params)

        if response.status == 400:
            raise ValueError(response.read())
        if response.status != 200:
            raise StandardError(response.read())

        return response.read()

    def make_request(self, method, path, params=None):
        conn = httplib.HTTPConnection(self.host)
        headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'X-Pvoutput-Apikey': self.api_key,
                'X-Pvoutput-SystemId': self.system_id
                }
        conn.request(method, path, params, headers)

        return conn.getresponse()


# class PvStatus():
#
#     def __init__(self, api_key, sid):
#         self.api_key = api_key
#         self.sid = sid
#         self.url = "http://pvoutput.org/service/r2/addstatus.jsp"
#
#         self.logger = logging.getLogger(__name__)
#
#     def send_metric(self, kwh_generated="", watt_ac_generated="",
#                     kwh_consumed="",
#                     watt_ac_consumed="", volt_dc="", temp_c="", totals=0):
#
#         now = datetime.datetime.now()
#
#         pvoutput_data = {'key': self.api_key,            # API Key
#                          'sid': self.sid,                # (PV-)System ID
#                          'd': now.strftime('%Y%m%d'),    # date
#                          't': now.strftime('%H:%M'),     # time (now)
#                          'c1': totals,  # 1 when upload cumulative kwh
#                          'v1': kwh_generated,     # total kWh generation today
#                          'v2': watt_ac_generated,        # current output power
#                          'v3': kwh_consumed,
#                          'v4': watt_ac_consumed,
#                          'v5': temp_c,
#                          'v6': volt_dc  # current PV voltage
#                         }
#
#         encoded_pvoutput_data = urllib.urlencode(pvoutput_data)
#         self.logger.debug("Sending data to pvoutput.org {0}"\
#             .format(encoded_pvoutput_data))
#
#         result = ''
#         try:
#             request_obj = urllib2.Request(self.url + '?' +
#                                           encoded_pvoutput_data)
#             response = urllib2.urlopen(request_obj)
#
#             self.logger.debug(pvoutput_data)
#             self.logger.info(response)
#
#             result = response
#
#         except (urllib2.HTTPError, urllib2.URLError) as e:
#             self.logger.error(e)
#             pass
#
#
#
#         return result
