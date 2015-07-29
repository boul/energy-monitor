import urllib2
import logging
import untangle

class WeatherData():

    def __init__(self, station_id):

        global glob_weather_data

        self.station_name = station_id
        self.url = "http://xml.buienradar.nl/"

        self.logger = logging.getLogger(__name__)

    def get_station_data(self):

        try:
            response = urllib2.urlopen(self.url)
            xml = response.read()
        except (urllib2.HTTPError, urllib2.URLError) as e:
            self.logger.error(e)
            pass
