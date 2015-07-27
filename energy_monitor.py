import logging
import time
from input import dsmr4_p1, abb_vsn300
from output import pvoutput
from output import carbon


host = 'abb-135541-3g96-3712.local'
inverter_serial = '135541-3G96-3712'
pvoutput_api_key = 'c5475f9b694e00c4b1e649a871448603b3051c4d'
pvoutput_system_id = '39538'
carbon_host = 'admin.boul.nl'
carbon_port = '2003'
carbon_base_path = 'power.'
log_interval = 10       # seconds
pvoutput_interval = 30  # is x times carbon interval

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
logger.setLevel(logging.DEBUG)

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


# Sent
counter = pvoutput_interval

while True:

    logger.debug("COUNTER: {0}".format(counter))

    logger.info('GETTING Data From DSMR v4 Meter')
    p1_meter = dsmr4_p1.Meter("/dev/ttyUSB0", debug=3, simulate=True)
    p1_data = p1_meter.get_telegram()

    logger.info('GETTING data from ABB VSN300 logger')
    pv_meter = abb_vsn300.Vsn300Reader(host, headers, inverter_serial)
    pv_data = pv_meter.get_last_stats()

    if counter == pvoutput_interval:
        logger.info('SENDING metrics to pvoutput.org')
        pv_output = pvoutput.PvStatus(pvoutput_api_key, pvoutput_system_id)
        total_kwh = float(p1_data['kWh-high'] + p1_data['kWh-low']) * 1000
        watt_in = float(p1_data['W-in']) * 1000
        watt_gen = float(pv_data['m101_1_W']) * 1000
        day_wh = float(pv_data['m64061_1_TotalWH']) * 1000
        pvout_result = pv_output.send_metric(day_wh,
                                             watt_gen,
                                             total_kwh,
                                             watt_in,
                                             pv_data['m101_1_DCV'],
                                             totals=1)
        # Reset counter
        counter = 1

    else:

        logger.info("SKIPPING pvoutput, only excepts data every 5 minutes "
                    "counter: {0}".format(counter))

        # Increment Counter
        counter += 1

    logger.info('SENDING metrics to Carbon / Graphite')

    server = carbon.CarbonServer(carbon_host, int(carbon_port))

    for k, v in pv_data.iteritems():

        path = carbon_base_path + "pv." + k
        server.send_metric(path, v)

    for k, v in p1_data.iteritems():

        path = carbon_base_path + "p1." + k
        server.send_metric(path, v)

    # TODO bit of a hack, need to do some better filtering on P1
    server.send_metric("energy.test.p1.gas-m3", p1_data['gas'][1])

    logger.debug('Sleep for {0} seconds'.format(log_interval))

    time.sleep(log_interval)

