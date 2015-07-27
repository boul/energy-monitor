import logging
import threading

from input import dsmr4_p1, abb_vsn300
from output import pvoutput
from output import carbon

host = 'abb-135541-3g96-3712.local'
inverter_serial = '135541-3G96-3712'
pvoutput_api_key = 'c5475f9b694e00c4b1e649a871448603b3051c4d'
pvoutput_system_id = '39538'
pvoutput_interval = 300
carbon_host = 'admin.boul.nl'
carbon_port = '2003'
carbon_base_path = 'power.'
pv_interval = 60
p1_interval = 10

# Dirty hack as lighttp does not handle digest correctly.
# so we are actually doing a replay attack :/
# TODO write custom auth-handler to do proper digest auth on X-Digest header
headers = {'Authorization': 'X-Digest username="guest",'
                            ' realm="registered_user@power-one.com",'
                            ' nonce="2c55c37e71d667022d5dcdf3765296cd",'
                            ' uri="/v1/feeds/ser4:135541-3G96-3712/'
                            'datastreams/m64061_1_DayWH?_=1437577885199",'
                            ' response="50400ad5e362a1a42d241bd31c9641e8",'
                            ' qop=auth, nc=00000002,'
                            ' cnonce="ddf4bfcaf87acba9"'}

# Set logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - '
                              '%(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class CustomTimer(threading._Timer):
    def __init__(self, interval, function, args=[], kwargs={}):
        self._original_function = function
        super(CustomTimer, self).__init__(
            interval, self._do_execute, args, kwargs)

    def _do_execute(self, *a, **kw):
        self.result = self._original_function(*a, **kw)

    def join(self):
        super(CustomTimer, self).join()
        return self.result


def thread_get_p1_data():

    global glob_p1_data

    logger.info('GETTING Data From DSMR v4 Meter')
    p1_meter = dsmr4_p1.Meter("/dev/ttyUSB0", debug=3, simulate=True)
    glob_p1_data = p1_meter.get_telegram()

    threading.Timer(p1_interval, get_p1_data).start()
    return True


def thread_get_pv_data():

    global glob_pv_data

    logger.info('GETTING data from ABB VSN300 logger')
    pv_meter = abb_vsn300.Vsn300Reader(host, headers, inverter_serial)
    glob_pv_data = pv_meter.get_last_stats()

    threading.Timer(pv_interval, get_pv_data).start()

    return True


def thread_send_p1_data_to_carbon():

    logger.info('SENDING P1 metrics to Carbon / Graphite')

    server = carbon.CarbonServer(carbon_host, int(carbon_port))

    for k, v in glob_p1_data.iteritems():

        path = carbon_base_path + "p1." + k
        server.send_metric(path, v)

    threading.Timer(p1_interval, send_p1_data_to_carbon).start()

    return True


def thread_send_pv_data_to_carbon():

    logger.info('SENDING PV metrics to Carbon / Graphite')

    server = carbon.CarbonServer(carbon_host, int(carbon_port))

    for k, v in glob_p1_data.iteritems():

        path = carbon_base_path + "pv." + k
        server.send_metric(path, v)

    threading.Timer(pv_interval, send_pv_data_to_carbon).start()

    return True


def thread_send_data_to_pvoutput():

    logger.info('SENDING metrics to pvoutput.org')
    pv_output = pvoutput.PvStatus(pvoutput_api_key, pvoutput_system_id)

    if 'kWh-high' in glob_p1_data:
        total_kwh = float(glob_p1_data['kWh-high'] +
                          glob_p1_data['kWh-low']) * 1000
    else:
        total_kwh = 0

    if 'W-in' in glob_p1_data:
        watt_in = float(glob_p1_data['W-in']) * 1000
    else:
        watt_in = 0

    if 'm101_1_W' in glob_pv_data:
        watt_gen = float(glob_pv_data['m101_1_W']) * 1000

    else:
        watt_gen = 0

    if 'm64061_1_TotalWH' in glob_pv_data:
        day_wh = float(glob_pv_data['m64061_1_TotalWH']) * 1000

    else:
        day_wh = 0

    if 'm64061_1_TotalWH' in glob_pv_data:
        dcv = glob_pv_data['m101_1_DCV']

    else:
        dcv = 0

    pv_output.send_metric(day_wh,
                          watt_gen,
                          total_kwh,
                          watt_in,
                          dcv,
                          totals=1)

    threading.Timer(pvoutput_interval, send_data_to_pvoutput).start()

    return True


def main():

    logger.info("Starting P1 Thread with interval: {0} secs".
                format(p1_interval))
    thread_get_p1_data()

    logger.info("Startnig P1 data to carbon Thread with interval: {0} secs".
                format(p1_interval))
    thread_send_p1_data_to_carbon()

    logger.info("Starting PV Thread with interval: {0} secs".
                format(pv_interval))
    thread_get_pv_data()

    logger.info("Starting PV data to carbon Thread with interval: {0} secs".
                format(pv_interval))
    thread_send_pv_data_to_carbon()

    logger.info("Starting PV Outpyt Thread with interval: {0} secs".
                format(pvoutput_interval))
    thread_send_data_to_pvoutput()


if __name__ == "__main__":
    main()
