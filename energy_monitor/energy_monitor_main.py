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


def thread_get_p1_data(config, daemon=False, simulate=False):

    p1_device = config.get('P1', 'p1_device')
    p1_interval = config.getint('P1', 'interval')

    global glob_p1_data

    logger.info('GETTING Data From DSMR v4 Meter')
    p1_meter = dsmr4_p1.Meter(p1_device, simulate=simulate)
    glob_p1_data = p1_meter.get_telegram()

    print glob_p1_data
    send_data_to_carbon(config, glob_p1_data, "p1.")

    if daemon:
        t = threading.Timer(p1_interval, thread_get_p1_data,
                            [config, daemon, simulate])
        t.daemon = daemon
        t.start()


def thread_get_pv_data(config, daemon=False):

    pv_host = config.get('VSN300', 'host')
    pv_interval = config.getint('VSN300', 'interval')
    pv_inverter_serial = config.get('VSN300', 'inverter_serial')
    pv_user = config.get('VSN300', 'username')
    pv_password = config.get('VSN300', 'password')

    global glob_pv_data

    logger.info('GETTING data from ABB VSN300 logger')
    pv_meter = abb_vsn300.Vsn300Reader(pv_host, pv_user, pv_password,
                                       pv_inverter_serial)

    return_data = pv_meter.get_last_stats()

    if not return_data is None:
        glob_pv_data = return_data
        send_data_to_carbon(config, return_data, "pv.")

    else:
        glob_pv_data = None
        logger.warning('No data received from VSN300 logger')

    if daemon:
        t = threading.Timer(pv_interval, thread_get_pv_data,
                            [config, daemon])
        t.daemon = daemon
        t.start()


def send_data_to_carbon(config, data, type_path):

    host = config.get('CARBON', 'host')
    port = config.get('CARBON', 'port')
    base_path = config.get('CARBON', 'base_path')
    current_time = int(time.time())

    logger.info('SENDING metrics to Carbon / Graphite')
    logger.debug('host: {0} port: {1} path: {2}'.
                 format(host, port, base_path))

    server = carbon.CarbonClient(host, int(port))

    for k, v in data.iteritems():

        path = base_path + type_path + k
        server.send_metric(path, v, current_time)


def thread_send_data_to_pvoutput(config, daemon=False):

    api_key = config.get('PVOUTPUT', 'api_key')
    system_id = config.get('PVOUTPUT', 'system_id')
    interval = config.getint('PVOUTPUT', 'interval')

    now = datetime.datetime.now()
    date_now = now.strftime('%Y%m%d')
    time_now = now.strftime('%H:%M')
    total_wh_generated = None
    watt_generated = None
    total_wh_import = None
    watt_import = None
    temp_c = None
    vdc = None
    cum = 1

    logger.info('SENDING metrics to pvoutput.org')
    pv_connection = pvoutput.Connection(api_key, system_id)

    if glob_pv_data is not None:

        if 'm101_1_W' in glob_pv_data:
            watt_generated = float(glob_pv_data['m101_1_W']) * 1000
        else:
            watt_generated = None

        if 'm64061_1_TotalWH' in glob_pv_data:
            total_wh_generated = float(glob_pv_data['m64061_1_TotalWH']) * 1000
        else:
            total_wh_generated = None

        if 'm101_1_DCV' in glob_pv_data:
            vdc = glob_pv_data['m101_1_DCV']
        else:
            vdc = None

    else:

        logger.warning('No PV Data! Sun down? or Logger Down?')

    if glob_p1_data is not None:

        if 'W-in' in glob_p1_data:
            watt_import = float(glob_p1_data['W-in']) * 1000
        else:
            watt_import = None

        if 'kWh-high' in glob_p1_data:
            total_wh_import = float(glob_p1_data['kWh-high'] +
                                    glob_p1_data['kWh-low']) * 1000
        else:
            total_wh_import = None

    else:
        logger.error('No P1 Data! Problem with serial connection?')

    if (glob_p1_data, glob_p1_data) is None:
        logger.critial('No PV & P1 Data... returning...')
        return

    logger.debug("PVOUTPUT add_status: date: {0} time: {1} wh_gen: {2} "
                 "watt-gen: {3} wh_import {4} watt_import: {5} temp: {6} "
                 "vdc: {7} cum: {8}".
                 format(date_now, time_now, total_wh_generated, watt_generated,
                        total_wh_import, watt_import, temp_c,
                        vdc, cum))

    pv_connection.add_status(date_now,
                             time_now,
                             total_wh_generated,
                             watt_generated,
                             total_wh_import,
                             watt_import,
                             temp_c,
                             vdc,
                             cum)

    if daemon:
        t = threading.Timer(interval, thread_send_data_to_pvoutput,
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
    config.set('CARBON', 'host', 'host.tld')
    config.set('CARBON', 'port', '2003')
    config.set('CARBON', 'base_path', 'power.')

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

    default_cfg = "~/.energy-monitor.cfg"

    parser = argparse.ArgumentParser(description="Energy Monitor help")
    parser.add_argument('-c', '--config', nargs='?', const=default_cfg,
                        help='Config file location')
    parser.add_argument('-l', '--level', help='Log Level, eg: INFO/DEBUG')
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

    args = parser.parse_args()

    if args.create_config:
        write_config(args.create_config)
        exit()

    if args.config is None:
        path = default_cfg
    else:
        path = args.config

    path = os.path.expanduser(path)

    print path

    config = read_config(path)

    pv_enable = config.getboolean('VSN300', 'enable')
    p1_enable = config.getboolean('P1', 'enable')
    pvoutput_enable = config.getboolean('PVOUTPUT', 'enable')

    if p1_enable:

            logger.info("Getting P1 data Timer thread starting...")
            thread_get_p1_data(config, args.daemon, args.simulate)

    if pv_enable:

        logger.info("Getting PV/VSN300 data Timer thread starting...")
        thread_get_pv_data(config, args.daemon)

    if pvoutput_enable:

        logger.info("Sending PV Output data Timer Thread Starting")
        thread_send_data_to_pvoutput(config, args.daemon)

    if args.daemon:

        # keep main alive since we are launching daemon threads!
        while True:
            time.sleep(100)

if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        # quit
        print "Ctrl-c received!... exiting"
        sys.exit()