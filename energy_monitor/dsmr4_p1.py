import serial
import logging


_tst = lambda x: (2000+int(x[0:2]),
                  int(x[2:4]),
                  int(x[4:6]),
                  int(x[6:8]),
                  int(x[8:10]))
_gas = lambda tst, m3: (_unit(m3))
_unit = lambda x: float(x.split('*', 1)[0])
_tariff = lambda x: 'low' if x == '0002' else ('high' if x == '0001' else x)
_id = lambda x: x
_int = lambda x: int(x)
_blackhole = lambda x: None

module_logger = logging.getLogger(__name__)


OBIS = {
    '0-0:96.1.1': ('serial_id', _blackhole),
    '0-0:1.0.0': ('timestamp', _blackhole),
    '1-3:0.2.8': ('DSMR', _int),
    '1-0:1.8.1': ('kWh-low', _unit),
    '1-0:1.8.2': ('kWh-high', _unit),
    '1-0:2.8.1': ('kWh-out-low', _unit),
    '1-0:2.8.2': ('kWh-out-high', _unit),
    '0-0:17.0.0': ('kWh-limit', _unit),
    '0-0:96.14.0': ('tariff', _unit),
    '1-0:1.7.0': ('kW-in', _unit),
    '1-0:2.7.0': ('kW-out', _unit),
    '0-0:96.3.10': ('switch', _id),
    '0-0:96.13.1': ('msg-numeric', _blackhole),
    '0-0:96.13.0': ('msg-txt', _blackhole),
    '0-0:96.7.21': ('failures', _int),
    '0-0:96.7.9': ('extended-failures', _int),
    '1-0:32.32.0': ('V-sags-l1', _int),
    '1-0:52.32.0': ('V-sags-l2', _int),
    '1-0:72.32.0': ('V-sags-l3', _int),
    '1-0:32.36.0': ('V-swells-l1', _int),
    '1-0:52.36.0': ('V-swells-l2', _int),
    '1-0:72.36.0': ('V-swells-l3', _int),
    '1-0:31.7.0': ('A-l1', _unit),
    '1-0:51.7.0': ('A-l2', _unit),
    '1-0:71.7.0': ('A-l3', _unit),
    '1-0:21.7.0': ('kW-l1-in', _unit),
    '1-0:41.7.0': ('kW-l2-in', _unit),
    '1-0:61.7.0': ('kW-l3-in', _unit),
    '1-0:22.7.0': ('kW-l1-out', _unit),
    '1-0:42.7.0': ('kW-l2-out', _unit),
    '1-0:62.7.0': ('kW-l3-out', _unit),
    '0-1:24.1.0': ('type', _int),
    '0-1:96.1.0': ('id-gas', _blackhole),
    '0-1:24.2.1': ('gas', _gas),
    '0-1:24.4.0': ('gas-switch', _id),
    }


class Meter():

    def __init__(self, device_port, simulate=False):

        self.device_port = device_port
        self.simulate = simulate

        self.logger = logging.getLogger(__name__)

    def _get_connection(self):

        if not self.simulate:

            #Serial port configuration
            ser = serial.Serial()
            ser.baudrate = 115200
            ser.bytesize = serial.EIGHTBITS
            ser.parity = serial.PARITY_NONE
            ser.stopbits = serial.STOPBITS_ONE
            ser.xonxoff = 1
            ser.rtscts = 0
            ser.timeout = 12
            ser.port = self.device_port

            self.logger.debug("Configuring Serial port comms")

            ser.open()

            return ser

        if self.simulate:

            self.logger.warning("SIMULATION!!! "
                             "Opening a file to simulate serial output")

            ser = open("/energy-monitor/test/p1.raw", 'rb')

            return ser

    def get_telegram(self):

        telegram = {}

        ser = self._get_connection()

        # Wait for first line of telegram
        while True:
            line = ser.readline().strip().strip('\0')
            if not line.startswith('/'):
                self.logger.debug('skipping line: {0}'.format(line))
                continue
            break

        if not len(line) >= 5:
            self.logger.error("P1 Message Header line too short")
        #telegram['header-marker'] = line[0:6]
        #telegram['header-id'] = line[6:]

        # Read second (blank) line
        if ser.readline().strip() != '':
            self.logger.error("Second line should be blank")

        # Read data
        raw_lines = []
        self.logger.debug("***** P1 Message Start ******")
        while True:
            line = ser.readline().strip()

            self.logger.debug(line)
            if line.startswith('!'):
                break
            raw_lines.append(line)

        self.logger.debug("***** P1 Message End ******")

        ser.close()

        # Remove superfluous linebreaks
        lines = []
        for raw_line in raw_lines:
            if raw_line.startswith('(') and lines:
                lines[-1] += raw_line
                continue
            lines.append(raw_line)

        for line in lines:
            bits = line.split('(')
            obis = bits[0]
            args = []
            for bit in bits[1:]:
                if not bit.endswith(')'):
                    self.logger.error('Malformed argument')
                args.append(bit[:-1])
            if not obis in OBIS:
                self.logger.debug('Unknown data object with OBIS: {0})'
                                    .format(obis))
                continue
            name, data_func = OBIS[obis]
            data = data_func(*args)

            telegram[name] = data

        telegram['gas-m3'] = telegram['gas']

        self.logger.debug("***** Processed Message Start *****")
        self.logger.debug(telegram)
        self.logger.debug("\n***** Processed Message End *****")

        return telegram
