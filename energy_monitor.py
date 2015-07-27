import logging

from input import dsmr4_p1, abb_vsn300
from output import pvoutput


host = 'abb-135541-3g96-3712.local'
inverter_serial = '135541-3G96-3712'
pvoutput_api_key = 'c5475f9b694e00c4b1e649a871448603b3051c4d'
pvoutput_system_id = '39538'

# Dirty hack as lighttp does not handle digest correctly.
# so we are actually doing a replay attack :/
# TODO write custom auth-handler to do proper digest auth on X-Digest header
headers = {'Authorization': 'X-Digest username="guest", realm="registered_user@power-one.com", nonce="2c55c37e71d667022d5dcdf3765296cd", uri="/v1/feeds/ser4:135541-3G96-3712/datastreams/m64061_1_DayWH?_=1437577885199", response="50400ad5e362a1a42d241bd31c9641e8", qop=auth, nc=00000002, cnonce="ddf4bfcaf87acba9"'}

# Set logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


logger.info('Getting Data From DSMR v4 Meter')
p1_meter = dsmr4_p1.Meter("/dev/ttyUSB0", debug=3, simulate=True)
p1_data = p1_meter.get_telegram()
print p1_data

logger.info('Getting data from ABB VSN300 logger')
pv_meter = abb_vsn300.Vsn300Reader(host, headers, inverter_serial)
pv_data = pv_meter.get_last_stats()

logger.info('Sending output to pvoutput.org')
pv_output = pvoutput.PvStatus(pvoutput_api_key, pvoutput_system_id)
total_kwh = float(p1_data['kWh-high'] + p1_data['kWh-low']) * 1000
watt_in = float(p1_data['W-in']) * 1000
watt_gen = float(pv_data['m101_1_W']) * 1000
day_wh = float(pv_data['m64061_1_DayWH']) * 1000
pv_data = pv_output.send_metric(day_wh,
                                watt_gen,
                                total_kwh,
                                watt_in,
                                pv_data['m101_1_DCV'])



# for code, value in sorted(vals.items()):
#     if code in p1_telegram.list_of_interesting_codes:pv
#         # Cleanup value
#         value = float(value.lstrip(b'\(').rstrip(b'\)*kWhA'))
#         # Print nicely formatted string
#     print("{0:<63}{1:>8}".format(p1_telegram.list_of_interesting_codes[code], value))