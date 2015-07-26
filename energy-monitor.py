from abb_vsn300.logger import Vsn300Reader
from dsmr_p1.logger import P1Telegram

host = 'abb-135541-3g96-3712.local'
inverter_serial = '135541-3G96-3712'

# Dirty hack as lighttp does not handle digest correctly.
# so we are actually doing a replay attack :/
# TODO write custom auth-handler to do proper digest auth on X-Digest header
headers = {'Authorization': 'X-Digest username="guest", realm="registered_user@power-one.com", nonce="2c55c37e71d667022d5dcdf3765296cd", uri="/v1/feeds/ser4:135541-3G96-3712/datastreams/m64061_1_DayWH?_=1437577885199", response="50400ad5e362a1a42d241bd31c9641e8", qop=auth, nc=00000002, cnonce="ddf4bfcaf87acba9"'}

stats = Vsn300Reader(host, headers, inverter_serial)

print stats.get_last_stats()

p1_telegram = P1Telegram("/dev/ttyUSB0")

print p1_telegram.get_telegram()