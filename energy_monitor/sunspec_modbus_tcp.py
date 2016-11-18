from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import logging


class SunSpecModBusTcpClient():

    def __init__(self, host, port):

        self.port = 502
        self.host = 'abb-135541-3g96-3712.local'

        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)

    def get_sunspec_data(self):

        client = ModbusClient(self.host, self.port)

        self.logger.info("Created ModbusClient, now trying to fetch data")

        try:

            result = client.read_holding_registers(0, 70, unit=0x2)

            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, endian=Endian.Big)
            decoded_info = {
                'C_SunSpec_ID': decoder.decode_32bit_uint(),
                'C_SunSpec_DID': decoder.decode_16bit_uint(),
                'C_SunSpec_Length': decoder.decode_16bit_uint(),
                'C_Manufacturer': decoder.decode_string(32),
                'C_Model': decoder.decode_string(32),
                'C_Version': decoder.decode_string(16),
                'C_Serial': decoder.decode_string(32),
                'C_DeviceAddress': decoder.decode_16bit_uint(),
            }

            result = client.read_holding_registers(70, 120, unit=0x2)

            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, endian=Endian.Big)
            decoded_stats = {
                'I_SunSpec_DID': decoder.decode_16bit_uint(),
                'I_SunSpec_Length': decoder.decode_16bit_uint(),
                'I_AC_Current':decoder.decode_16bit_uint(),
                'I_AC_CurrentA': decoder.decode_16bit_uint(),
                'I_AC_CurrentB': decoder.decode_16bit_uint(),
                'I_AC_CurrentC': decoder.decode_16bit_uint(),
                'I_AC_Current_SF': decoder.decode_16bit_int(),
                'I_AC_VoltageAB': decoder.decode_16bit_uint(),
                'I_AC_VoltageBC': decoder.decode_16bit_uint(),
                'I_AC_VoltageCA': decoder.decode_16bit_uint(),
                'I_AC_VoltageAN': decoder.decode_16bit_uint(),
                'I_AC_VoltageBN': decoder.decode_16bit_uint(),
                'I_AC_VoltageCN': decoder.decode_16bit_uint(),
                'I_AC_Voltage_SF': decoder.decode_16bit_int(),
                'I_AC_Power': decoder.decode_16bit_int(),
                'I_AC_Power_SF': decoder.decode_16bit_int(),
                'I_AC_Frequency': decoder.decode_16bit_uint(),
                'I_AC_Frequency_SF': decoder.decode_16bit_int(),
                'I_AC_VA': decoder.decode_16bit_int(),
                'I_AC_VA_SF': decoder.decode_16bit_int(),
                'I_AC_VAR': decoder.decode_16bit_int(),
                'I_AC_VAR_SF': decoder.decode_16bit_int(),
                'I_AC_PF': decoder.decode_16bit_int(),
                'I_AC_PF_SF': decoder.decode_16bit_int(),
                'I_AC_Energy_WH': decoder.decode_32bit_int(),
                'I_AC_Energy_WH_SF': decoder.decode_16bit_uint,
                'I_DC_Current': decoder.decode_16bit_uint(),
                'I_DC_Current_SF': decoder.decode_16bit_int(),
                'I_DC_Voltage': decoder.decode_16bit_uint(),
                'I_DC_Voltage_SF': decoder.decode_16bit_int(),
                'I_DC_Power': decoder.decode_16bit_int(),
                'I_DC_Power_SF': decoder.decode_16bit_int(),
                'I_Temp_Sink': decoder.decode_16bit_int(),
                'I_Temp_SF': decoder.decode_16bit_int(),
                'I_Status': decoder.decode_16bit_uint(),
                'I_Status_Vendor': decoder.decode_16bit_uint(),
                'I_Event_1': decoder.decode_32bit_uint(),
                'I_Event_2' : decoder.decode_32bit_uint(),
                'I_Event_1_Vendor': decoder.decode_32bit_uint(),
                'I_Event_2_Vendor': decoder.decode_32bit_uint(),
                'I_Event_3_Vendor': decoder.decode_32bit_uint(),
                'I_Event_4_Vendor': decoder.decode_32bit_uint(),
            }

            self.logger.info("Modbus data fetched closing client")
            client.close()

            self.logger.debug("-" * 60)
            self.logger.debug("Decoded SunSpec Data")
            self.logger.debug("-" * 60)

            merged_stats = decoded_info.copy()
            merged_stats.update(decoded_stats)

            for name, value in merged_stats.iteritems():
                self.logger.debug(name + " : " + str(value))

            return decoded_stats

        except Exception as e:
            self.logger.error(e)
            pass

