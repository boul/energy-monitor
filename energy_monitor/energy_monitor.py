#!/usr/bin/python
import logging
import threading
import dsmr4_p1
import carbon
import abb_vsn300
import pvoutput
import argparse
import os
import sys



# pv_host = '10.0.3.54'
# pv_inverter_serial = '135541-3G96-3712'
# pv_user = "admin"
# pv_password = "SnowmaN6"
# pv_interval = 60
#
# p1_interval = 10
# p1_device = "/dev/ttyUSB0"
# p1_simulate = True
#
# pvoutput_api_key = 'c5475f9b694e00c4b1e649a871448603b3051c4d'
# pvoutput_system_id = '39538'
# pvoutput_interval = 300
# carbon_host = 'admin.boul.nl'
# carbon_port = '2003'
# carbon_base_path = 'power.'

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


def thread_get_p1_data(config, daemon=False, simulate=True):

    lock = Lock()

    p1_device = config.get('P1', 'p1_device')
    p1_interval = config.getint('P1', 'interval')

    global glob_p1_data

    logger.info('GETTING Data From DSMR v4 Meter')
    p1_meter = dsmr4_p1.Meter(p1_device, simulate=simulate)
    glob_p1_data = p1_meter.get_telegram()

    send_data_to_carbon(config, glob_p1_data, "p1.")

    if daemon:
        threading.Timer(p1_interval, thread_get_p1_data, [config]).start()
    return


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
    glob_pv_data = pv_meter.get_last_stats()

    send_data_to_carbon(config, glob_pv_data, "pv.")

    if daemon:
        threading.Timer(pv_interval, thread_get_pv_data, [config]).start()
    return


def send_data_to_carbon(config, data, path):

    host = config.get('CARBON', 'host')
    port = config.get('CARBON', 'port')
    base_path = config.get('CARBON', 'base_path')
    # interval = config.getint('P1', 'interval')

    logger.info('SENDING metrics to Carbon / Graphite')
    logger.debug('host: {0} port: {1} path: {2}'.
                 format(host, port, base_path))

    server = carbon.CarbonClient(host, int(port))

    for k, v in glob_p1_data.iteritems():

        path = base_path + path + k
        server.send_metric(path, v)
    #
    # if daemon:
    #     threading.Timer(interval, thread_send_p1_data_to_carbon,
    #                     [config]).start()
    return


# def thread_send_pv_data_to_carbon(config, daemon=False):
#
#     host = config.get('CARBON', 'host')
#     port = config.get('CARBON', 'port')
#     base_path = config.get('CARBON', 'base_path')
#     interval = config.getint('VSN300', 'interval')
#
#     logger.info('SENDING PV metrics to Carbon / Graphite')
#     logger.debug('host: {0} port: {1} path: {2} interval: {3}'.
#                  format(host, port, base_path, interval))
#
#     server = carbon.CarbonClient(host, int(port))
#
#     for k, v in glob_pv_data.iteritems():
#
#         path = base_path + "pv." + k
#         server.send_metric(path, v)
#
#     if daemon:
#         threading.Timer(interval, thread_send_pv_data_to_carbon).start()
#
#     return True


def thread_send_data_to_pvoutput(config, daemon=False):

    pvoutput_api_key = config.get('PVOUTPUT', 'api_key')
    pvoutput_system_id = config.get('PVOUTPUT', 'system_id')
    pvoutput_interval = config.getint('PVOUTPUT', 'interval')

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

    if daemon:
        threading.Timer(pvoutput_interval, thread_send_data_to_pvoutput)\
            .start()

    return True

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
    # pv_host = config.get('VSN300', 'host')
    pv_interval = config.getint('VSN300', 'interval')
    # pv_inverter_serial = config.get('VSN300', 'inverter_serial')
    # pv_user = config.get('VSN300', 'username')
    pv_pass = config.get('VSN300', 'password')


    p1_enable = config.getboolean('P1', 'enable')
    p1_device = config.get('P1', 'p1_device')
    p1_interval = config.getint('P1', 'interval')

    pvoutput_enable = config.getboolean('PVOUTPUT', 'enable')
    pvoutput_api_key = config.get('PVOUTPUT', 'api_key')
    pvoutput_system_id = config.get('PVOUTPUT', 'system_id')
    pvoutput_interval = config.getint('PVOUTPUT', 'interval')



    # carbon_host = config.getboolean('CARBON', 'host')
    # carbon_port = config.getboolean('CARBON', 'base_path')
    # carbon_base_path = config.getboolean('CARBON', 'base_path')


    if p1_enable:
        print args.daemon
        logger.info("Getting P1 data Timer thread starting...")
        thread_get_p1_data(config, args.daemon, args.simulate)
        #
        # logger.info("Starting P1 data to carbon Thread with interval: {0} secs".
        #         format(p1_interval))
        # thread_send_p1_data_to_carbon(config, args.daemon)

    if pv_enable:

        logger.info("Getting PV/VSN300 data Timer thread starting...")
        thread_get_pv_data(config, args.daemon)

        # logger.info("Starting PV data to carbon Thread with interval: {0} secs".
        #             format(pv_interval))
        # thread_send_pv_data_to_carbon(config, args.daemon)

    if pvoutput_enable:

        logger.info("Sending PV Output data Timer Thread Starting")
        thread_send_data_to_pvoutput(config, args.daemon)


if __name__ == "__main__":

    main()
