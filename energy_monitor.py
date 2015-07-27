import logging

from dsmr_meter import dsmr4_p1


host = 'abb-135541-3g96-3712.local'
inverter_serial = '135541-3G96-3712'

# Dirty hack as lighttp does not handle digest correctly.
# so we are actually doing a replay attack :/
# TODO write custom auth-handler to do proper digest auth on X-Digest header
headers = {'Authorization': 'X-Digest username="guest", realm="registered_user@power-one.com", nonce="2c55c37e71d667022d5dcdf3765296cd", uri="/v1/feeds/ser4:135541-3G96-3712/datastreams/m64061_1_DayWH?_=1437577885199", response="50400ad5e362a1a42d241bd31c9641e8", qop=auth, nc=00000002, cnonce="ddf4bfcaf87acba9"'}

#stats = Vsn300Reader(host, headers, inverter_serial)

#print stats.get_last_stats()

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


logger.info('calling instance')
p1_telegram = dsmr4_p1.Meter("/dev/ttyUSB0", debug=3, simulate=True)
logger.info('returned')

p1_telegram.get_telegram()






# for code, value in sorted(vals.items()):
#     if code in p1_telegram.list_of_interesting_codes:
#         # Cleanup value
#         value = float(value.lstrip(b'\(').rstrip(b'\)*kWhA'))
#         # Print nicely formatted string
#     print("{0:<63}{1:>8}".format(p1_telegram.list_of_interesting_codes[code], value))