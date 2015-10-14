import logging
import threading
import dsmr4_p1
import carbon
import abb_vsn300
import pvoutput
import argparse
import os
import datetime
import time
import sys
import wunderground
import enelogic

default_cfg = "~/.energy-monitor.cfg"

parser = argparse.ArgumentParser(description="Energy Monitor help")
parser.add_argument('-c', '--config', nargs='?', const=default_cfg,
                    help='Config file location')
parser.add_argument('-d', '--daemon', help='Run as Daemon ',
                    action="store_true", default=False)
parser.add_argument('-s', '--simulate', help='Run in simulate mode',
                    action="store_true", default=False)
parser.add_argument('--create-config', nargs='?',
                    const=default_cfg,
                    help="Create a config file, defaults to "
                         "~/.energy-monitor.cfg or specify an "
                         "alternative location",
                    metavar="path")
parser.add_argument('-v', '--verbose', help='Verbose logging ',
                    action="store_true", default=False)
parser.add_argument('--debug', help='Debug logging ',
                    action="store_true", default=False)
# parser.add_argument('-l', '--logfile', help='Send output to logfile  ',
#                     action="store_true", default=False)

args = parser.parse_args()

# Set logging
logger = logging.getLogger()

if args.verbose:
    logger.setLevel(logging.INFO)

elif args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

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

lock = threading.RLock()

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


def thread_get_p1_data(config, daemon=False, simulate=False):

    p1_device = config.get('P1', 'p1_device')
    p1_interval = config.getint('P1', 'interval')

    global glob_p1_data

    logger.debug("Release Lock - get_pv_data")
    lock.acquire()

    logger.info('GETTING Data From DSMR v4 Meter')
    p1_meter = dsmr4_p1.Meter(p1_device, simulate=simulate)
    glob_p1_data = p1_meter.get_telegram()

    for k, v in glob_p1_data.iteritems():
        logger.info("P1 DATA: key: {0} - value: {1}".format(k, v))

    logger.debug("Release Lock - get_pv_data")
    lock.release()

    if daemon:
        t = threading.Timer(p1_interval, thread_get_p1_data,
                            [config, daemon, simulate])
        t.daemon = daemon
        t.start()


def thread_get_pv_data(config, daemon=False, simulate=False):

    pv_host = config.get('VSN300', 'host')
    pv_interval = config.getint('VSN300', 'interval')
    pv_inverter_serial = config.get('VSN300', 'inverter_serial')
    pv_user = config.get('VSN300', 'username')
    pv_password = config.get('VSN300', 'password')

    global glob_pv_data

    logger.debug("Acquire Lock - get_pv_data")
    lock.acquire()

    logger.info('GETTING data from ABB VSN300 logger')
    pv_meter = abb_vsn300.Vsn300Reader(pv_host, pv_user, pv_password,
                                       pv_inverter_serial, simulate)

    return_data = pv_meter.get_last_stats()


    if not return_data is None:
        glob_pv_data = return_data
        #send_data_to_carbon(config, return_data, "pv.")

    else:
        glob_pv_data = None
        logger.warning('No data received from VSN300 logger')

    logger.debug("Release Lock - get_pv_data")
    lock.release()

    if daemon:
        t = threading.Timer(pv_interval, thread_get_pv_data,
                            [config, daemon, simulate])
        t.daemon = daemon
        t.start()


def thread_send_to_carbon(interval, config, data_type, daemon=False):

    host = config.get('CARBON', 'host')
    port = config.get('CARBON', 'port')
    base_path = config.get('CARBON', 'base_path')

    logger.info('SENDING metrics to Carbon / Graphite')
    logger.debug('host: {0} port: {1} path: {2}'.
                 format(host, port, base_path))

    server = carbon.CarbonClient(host, int(port))

    logger.debug("Acquire Lock - send_carbon")
    lock.acquire()

    if data_type == 'p1' and 'glob_p1_data' in globals():
        if glob_p1_data is not None:

            for k, v in glob_p1_data.iteritems():

                current_time = int(time.time())
                path = base_path + "p1." + k
                server.send_metric(path, v, current_time)

    if data_type == 'pv' and 'glob_pv_data' in globals():
        if glob_pv_data is not None:

            for k, v in glob_pv_data.iteritems():

                current_time = int(time.time())
                path = base_path + "pv." + k
                server.send_metric(path, v, current_time)

    logger.debug("Release Lock - send_carbon")
    lock.release()

    if daemon:
        t = threading.Timer(interval, thread_send_to_carbon,
                            [interval, config, data_type, daemon])
        t.daemon = daemon
        t.start()


def thread_send_data_to_pvoutput(config, daemon=False):

    api_key = config.get('PVOUTPUT', 'api_key')
    system_id = config.get('PVOUTPUT', 'system_id')
    interval = config.getint('PVOUTPUT', 'interval')

    now = datetime.datetime.now()
    date_now = now.strftime('%Y%m%d')
    time_now = now.strftime('%H:%M')
    day_wh_generated = None
    total_wh_generated = None
    watt_generated = None
    total_wh_import = None
    #total_wh_export = None
    kwh_out_high = None
    kwh_out_low = None
    kwh_high = None
    kwh_low = None
    watt_export = None
    watt_import = None
    temp_c = None
    vdc = None
    gas_m3 = None
    inverter_temp = None
    watt_net = None
    cons_net = None

    logger.info('SENDING metrics to pvoutput.org')
    pv_connection = pvoutput.Connection(api_key, system_id)

    logger.debug("Acquire Lock - send pvoutput")
    lock.acquire()

    if 'glob_pv_data' in globals():
        if glob_pv_data is not None:

            #watt_generated = None
            if 'm101_1_W' in glob_pv_data:
                watt_generated = float(glob_pv_data['m101_1_W']) * 1000
                logger.info('Watt generated: {0}'.format(watt_generated))

            # day_wh_generated = None
            if 'm64061_1_DayWH' in glob_pv_data:
                day_wh_generated = float(glob_pv_data['m64061_1_DayWH']) * 1000
                logger.info('Day wH generated: {0}'.format(day_wh_generated))

            # total_wh_generated = None
            if 'm64061_1_TotalWH' in glob_pv_data:
                total_wh_generated = float(glob_pv_data[
                    'm64061_1_TotalWH']) * 1000
                logger.info('Total (Lifetime) wH generated: {0}'
                            .format(total_wh_generated))

            # vdc = None
            if 'm101_1_DCV' in glob_pv_data:
                vdc = glob_pv_data['m101_1_DCV']
                logger.info('Volt DC: {0}'.format(vdc))

            # inverter_temp = None
            if 'm101_1_TmpCab' in glob_pv_data:
                inverter_temp = glob_pv_data['m101_1_TmpCab']
                logger.info('Inverter Temperature: {0}'.format(inverter_temp))

    else:

        logger.warning('No PV Data! Sun down? or Logger Down?')

    if 'glob_p1_data' in globals():
        if glob_p1_data is not None:

            # watt_import = None
            if 'kW-in' in glob_p1_data:
                watt_import = float(glob_p1_data['kW-in']) * 1000

                logger.info('Total kW Import: {0}'.format(watt_import))

            # watt_export = None
            if 'kW-out' in glob_p1_data:
                watt_export = float(glob_p1_data['kW-out']) * 1000

                logger.info('Total kW Export: {0}'.format(watt_export))

            # gas_m3 = None
            if 'gas-m3' in glob_p1_data:
                gas_m3 = float(glob_p1_data['gas-m3'])
                logger.info('Total gas M3: {0}'.format(gas_m3))

            # total_wh_import = None
            if ('kWh-high' and 'kWh-low') in glob_p1_data:

                kwh_low = glob_p1_data['kWh-low'] * 1000
                kwh_high = glob_p1_data['kWh-high'] * 1000
                total_wh_import = float(kwh_high +
                                        kwh_low)

                logger.info('Total Wh Import: {0}'.format(total_wh_import))

            # total_wh_export = None
            if ('kWh-out-high' and 'kWh-out-low') in glob_p1_data:
                kwh_out_low = glob_p1_data['kWh-out-low'] * 1000
                kwh_out_high = glob_p1_data['kWh-out-high'] * 1000
                total_wh_export = float(kwh_out_low +
                                        kwh_out_high)

                logger.info('Total Wh Export: {0}'.format(total_wh_export))

            # watt_net = None
            # Calculate netto power import (neg is export)
            if (watt_import, watt_export) is not None:
                watt_net = float(watt_import) - float(watt_export)
                logger.info('Netto Wh Import/Export: {0}'.format(watt_net))

            if watt_generated is not None:
                cons_net = watt_generated + watt_net
                logger.info('Consumed Wh: {0}'.format(cons_net))
            else:

                logger.error('Cannot calculate net consumption, '
                             'we do not have generation numbers: {0}')

    else:
        logger.error('No P1 Data! Problem with serial connection?')

    if (glob_p1_data, glob_p1_data) is None:
        logger.critial('No PV & P1 Data... returning...')
        return

    # temp_c = None
    if 'glob_weather_data' in globals():
        if glob_weather_data is not None:

            temp_c = glob_weather_data['current_observation'].get('temp_c', None)

    # Sending generation data (gross), separate from import/export (net).
    # See also: http://pvoutput.org/help.html#api-addstatus (net data)
    # we need to send gross before net so they will be merged correctly

    logger.info("Sending (gross) pv generation data to pvoutput")
    pv_connection.add_status(date=date_now,
                             time=time_now,
                             energy_exp=day_wh_generated,
                             power_exp=watt_generated,
                             energy_imp=None,
                             power_imp=None,
                             temp=temp_c,
                             vdc=vdc,
                             cumulative=False,
                             net=False,
                             v8=gas_m3,
                             v7=inverter_temp,
                             v9=kwh_out_high,
                             v10=kwh_out_low,
                             v11=kwh_high,
                             v12=kwh_low)

    logger.info("Sending (net) import/export data to pvoutput")
    pv_connection.add_status(date=date_now,
                             time=time_now,
                             energy_exp=day_wh_generated,
                             power_exp=watt_export,
                             energy_imp=None,
                             power_imp=watt_import,
                             temp=None,
                             vdc=None,
                             cumulative=False,
                             net=True)

    # eod_start = datetime.time(10,55,0)
    # eod_stop =  datetime.time(12,10,0)
    # eod_now = datetime.datetime.now().time()
    # eod_cm = "EOD generated at: {0} {1}".format(date_now, time_now)
    # eod_run = 0
    #
    # print datetime.datetime.now().time()
    # print time_in_range(eod_start,eod_stop,eod_now)
    #
    # if time_in_range(eod_start,eod_stop,eod_now):
    #     logger.info("Time to send EOD to pvoutput")
    #     pv_connection.add_output(date=date_now,
    #                              exported=total_wh_export,
    #                              import_peak=kwh_high,
    #                              import_offpeak=kwh_low,
    #                              comments=eod_cm)

    logger.debug("Release Lock - send pvoutput")
    lock.release()

    if daemon:
        t = threading.Timer(interval, thread_send_data_to_pvoutput,
                            [config, daemon])
        t.daemon = daemon
        t.start()


def thread_get_weather(config, daemon):

    global glob_weather_data

    logger.debug("Acquire Lock - get_weather")
    lock.acquire()

    api_key = config.get('WUNDERGROUND', 'api_key')
    iso_country = config.get('WUNDERGROUND', 'iso_country')
    city = config.get('WUNDERGROUND', 'city')
    interval = config.getint('WUNDERGROUND', 'interval')

    connection = wunderground.Connection(api_key, iso_country, city)

    glob_weather_data = connection.get_weather()

    logger.debug("Release Lock - get_weather")

    lock.release()

    if daemon:
        t = threading.Timer(interval, thread_get_weather,
                            [config, daemon])
        t.daemon = daemon
        t.start()


def thread_send_to_enelogic(config, daemon):

    logger.debug("Acquire Lock - send_to_enelogic")
    lock.acquire()

    now = datetime.datetime.now()
    api_key = config.get('ENELOGIC', 'api_key')
    app_key = config.get('ENELOGIC', 'app_key')
    app_secret = config.get('ENELOGIC', 'app_secret')
    username = config.get('ENELOGIC', 'username')
    interval = config.getint('ENELOGIC', 'interval')
    datetime_now = now.strftime('%Y%m%d %H:%M:%S')

    # total_wh_generated = None
    # time_now = now.strftime('%H:%M')

    connection = enelogic.Connection(api_key, username, app_key, app_secret)

    if 'glob_pv_data' in globals():
        if glob_pv_data is not None:

           # total_wh_generated = None
            if 'm64061_1_TotalWH' in glob_pv_data:
                total_wh_generated = float(glob_pv_data[
                    'm64061_1_TotalWH'])
                logger.info('Total (Lifetime) wH generated: {0}'
                            .format(total_wh_generated))
                connection.create_datapoint(total_wh_generated,
                                            280, datetime_now, 90634)

    else:
        logger.warning('No PV Data! Sun down? or Logger Down?')

    if 'glob_p1_data' in globals():
        if glob_p1_data is not None:

            # gas_m3 = None
            if 'gas-m3' in glob_p1_data:
                gas_m3 = float(glob_p1_data['gas-m3'])
                logger.info('Total gas M3: {0}'.format(gas_m3))

                connection.create_datapoint(gas_m3,
                                            180, datetime_now, 90633)

            # total_wh_import = None
            if ('kWh-high' and 'kWh-low') in glob_p1_data:

                kwh_low = glob_p1_data['kWh-low']
                kwh_high = glob_p1_data['kWh-high']

                connection.create_datapoint(kwh_low,
                                            181, datetime_now, 90632)
                connection.create_datapoint(kwh_high,
                                            182, datetime_now, 90632)

                logger.info('kWh-low: {0}'.format(kwh_low))
                logger.info('kWh-high: {0}'.format(kwh_high))

            # total_wh_export = None
            if ('kWh-out-high' and 'kWh-out-low') in glob_p1_data:
                kwh_out_low = glob_p1_data['kWh-out-low'] * 1000
                kwh_out_high = glob_p1_data['kWh-out-high'] * 1000

                connection.create_datapoint(kwh_out_low,
                                            281, datetime_now, 90632)
                connection.create_datapoint(kwh_out_high,
                                            282, datetime_now, 90632)

                logger.info('kWh-out-low: {0}'.format(kwh_out_low))
                logger.info('kWh-out-high: {0}'.format(kwh_out_high))

            else:
                logger.error('No P1 Data! Problem with serial connection?')

    if (glob_p1_data, glob_p1_data) is None:
        logger.critical('No PV & P1 Data... returning...')
        return

    logger.debug("Release Lock - send_to_enelogic")

    lock.release()

    if daemon:
        t = threading.Timer(interval, thread_get_weather,
                            [config, daemon])
        t.daemon = daemon
        t.start()


def write_config(path):

    import ConfigParser

    config = ConfigParser.ConfigParser(allow_no_value=True)

    config.add_section('VSN300')
    config.set('VSN300', '# enable: turn data retrieval on or off')
    config.set('VSN300', '# hostname:  or IP of the logger')
    config.set('VSN300', '# inverter_serial: serial can be found in the'
                         ' webui: data -> '  'system info ->'
                         ' inverter info -> serial ')
    config.set('VSN300', '# interval: interval to read data from logger, '
                         'logger does only refresh data every 60 seconds, '
                         'polling more often is useless ')
    config.set('VSN300', '# username: is either guest or admin')
    config.set('VSN300', '# password: as set on webui')
    config.set('VSN300', '# ')

    config.set('VSN300', 'enable', 'true')
    config.set('VSN300', 'host', '192.168.1.12')
    config.set('VSN300', 'inverter_serial', 'XXXXXX-XXXX-XXXX')
    config.set('VSN300', 'interval', '60')
    config.set('VSN300', 'username', 'guest')
    config.set('VSN300', 'password', 'password')

    config.add_section('P1')
    config.set('P1', 'enable', 'true')
    config.set('P1', 'p1_device', '/dev/ttyUSB0')
    config.set('P1', 'interval', '10')

    config.add_section('PVOUTPUT')
    config.set('PVOUTPUT', 'enable', 'true')
    config.set('PVOUTPUT', 'api_key', '')
    config.set('PVOUTPUT', 'system_id', '')
    config.set('PVOUTPUT', 'interval', '300')

    config.add_section('CARBON')
    config.set('CARBON', 'enable', 'true')
    config.set('CARBON', 'host', 'host.tld')
    config.set('CARBON', 'port', '2003')
    config.set('CARBON', 'base_path', 'power.')

    config.add_section('WUNDERGROUND')
    config.set('WUNDERGROUND', 'enable', 'true')
    config.set('WUNDERGROUND', 'api_key', '')
    config.set('WUNDERGROUND', 'iso_country', 'NL')
    config.set('WUNDERGROUND', 'city', 'de_bilt')
    config.set('WUNDERGROUND', 'interval', '300')

    config.add_section('ENELOGIC')
    config.set('ENELOGIC', 'enable', 'true')
    config.set('ENELOGIC', 'username', '')
    config.set('ENELOGIC', 'app_key', '')
    config.set('ENELOGIC', 'app_secret', '')
    config.set('ENELOGIC', 'api_key', '')
    config.set('ENELOGIC', 'interval', '60')
    config.set('ENELOGIC', 'solar_point_id', '90634')
    config.set('ENELOGIC', 'electricity_point_id', '90632')
    config.set('ENELOGIC', 'gas_point_id', '90633')

    path = os.path.expanduser(path)

    if os.path.isfile(path):
        if not query_yes_no("File already exists! continue?", default="no"):
            print "OK! won't touch it!"
            return

    with open(path, 'wb') \
            as configfile:
        config.write(configfile)

        print "Config has been written to: {0}".\
            format(os.path.expanduser(path))


def read_config(path):

    import ConfigParser

    if not os.path.isfile(path):
        print "Config file not found: {0}".format(path)
        exit()

    else:

        config = ConfigParser.RawConfigParser()
        config.read(path)

        return config


def main():

    if args.create_config:
        write_config(args.create_config)
        exit()

    if args.config is None:
        path = default_cfg
    else:
        path = args.config

    path = os.path.expanduser(path)

    config = read_config(path)
    pv_enable = config.getboolean('VSN300', 'enable')
    pv_interval = config.getint('VSN300', 'interval')
    p1_enable = config.getboolean('P1', 'enable')
    p1_interval = config.getint('P1', 'interval')
    pvoutput_enable = config.getboolean('PVOUTPUT', 'enable')
    carbon_enable = config.get('CARBON', 'enable')
    wunderground_enable = config.get('WUNDERGROUND', 'enable')
    enelogic_enable = config.get('ENELOGIC', 'enable')

    if p1_enable:

            logger.info("STARTING P1 data Timer thread starting...")
            thread_get_p1_data(config, args.daemon, args.simulate)

    if pv_enable:

        logger.info("STARTING PV/VSN300 data Timer thread")
        thread_get_pv_data(config, args.daemon, args.simulate)

    if wunderground_enable:

        logger.info("STARTING Wunderground Weather data Timer Thread")
        thread_get_weather(config, args.daemon)

    if pvoutput_enable:

        logger.info("STARTING PV Output data Timer Thread")
        thread_send_data_to_pvoutput(config, args.daemon)

    if enelogic_enable:

        logger.info("STARTING Enelogic Output data Timer Thread")
        thread_send_to_enelogic(config, args.daemon)

    if carbon_enable:

        logger.info("STARTING P1 metrics to CarbonTimer Thread")
        thread_send_to_carbon(p1_interval, config, 'p1', args.daemon)

        logger.info("STARTING PV metrics to CarbonTimer Thread")
        thread_send_to_carbon(pv_interval, config, 'pv', args.daemon)

    if args.daemon:

        # keep main alive since we are launching daemon threads!
        while True:
            time.sleep(100)

if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        # quit
        print "...Ctrl-C received!... exiting"
        sys.exit()