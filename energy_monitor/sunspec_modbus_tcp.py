import sunspec.core.client as client
import logging


class SunSpecModBusTcpClient():

    def __init__(self, host, port, device_id):

        self.port = port
        self.host = host
        self.device_id = device_id

        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)

    def get_sunspec_data(self):

        self.logger.info('Creating SunSpec modbus TCP client,'
                         ' Host: {0} - Port: {1} - DeviceID: {2}'
                         .format(self.host, self.port, self.device_id))

        try:
            d = client.SunSpecClientDevice(client.TCP,
                                           slave_id= self.device_id,
                                           ipaddr=self.host,
                                           ipport=self.port,
                                           timeout=5)

            self.logger.info('Trying to fetch SunSpec data from ModBus')

            self.logger.debug('Fetching Models: {0}'.format(d.models))
            d.common.read()
            self.logger.debug('Reading SunSpec Common Model_1:'
                              ' {0}'.format(d.common))

            d.inverter.read()
            self.logger.debug('Reading SunSpec Inverter Model_101:'
                              ' {0}'.format(d.inverter))

            d.mppt.read()
            self.logger.debug('Reading SunSpec MPPT Model_106:'
                              ' {0}'.format(d.mppt))

            d.nameplate.read()
            self.logger.debug('Reading SunSpec NamePlate Model_120:'
                              ' {0}'.format(d.nameplate))

            d.settings.read()
            self.logger.debug('Reading SunSpec Settings Model_121:'
                              ' {0}'.format(d.settings))

            d.controls.read()
            self.logger.debug('Reading SunSpec Controls Model_123:'
                              ' {0}'.format(d.controls))

            # Only return relevant data
            suns_data = {
                'A': d.inverter.A,
                'PhVphA': d.inverter.PhVphA,
                'W': d.inverter.W,
                'Hz': d.inverter.Hz,
                'WH': d.inverter.WH,
                'DCW': d.inverter.DCW,
                'TmpOt': d.inverter.TmpOt,
                'St': d.inverter.St,
                'StVnd': d.inverter.StVnd,
                'DCA_1': d.mppt.module[1].DCA,
                'DCV_1': d.mppt.module[1].DCV,
                'DCW_1': d.mppt.module[1].DCW,
                'DCA_2': d.mppt.module[2].DCA,
                'DCV_2': d.mppt.module[2].DCV,
                'DCW_2': d.mppt.module[2].DCW,
                           }
            # Filter none
            suns_data2 = {k: v for k, v in suns_data.items() if v is not None}

            self.logger.info('Fetched SunSpec data points: {0}'.
                             format(suns_data2))

            return suns_data2

        except Exception as e:
            self.logger.error(e)
            return None


