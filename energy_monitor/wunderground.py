__author__ = 'rkuipers'
import urllib2
import json
import logging




class Connection():

    def __init__(self, api_key, iso_country, city):

        self.api_key = api_key
        self.iso_country = iso_country
        self.city = city

        self.logger = logging.getLogger(__name__)

    def get_weather(self):

        url = "http://api.wunderground.com/api/" + self.api_key +\
              "/geolookup/conditions/q/" + self.iso_country + "/" + \
              self.city + ".json"

        self.logger.debug('Fetching weather data: {0}'.format(url))
        try:
            f = urllib2.urlopen(url)
            json_string = f.read()
            parsed_json = json.loads(json_string)
            #response = parsed_json['response']

            self.logger.debug(parsed_json)

            if 'error' in parsed_json:
                if parsed_json['response']['error']['type'] == "keynotfound":
                    self.logger.error(
                        "We got a keynotfound error "
                        "from wunderground, please check your api key")
                return

            location = parsed_json['location']['city']
            temp_f = parsed_json['current_observation']['temp_f']
            temp_c = parsed_json['current_observation']['temp_c']
            self.logger.info(
                "Current temperature in %s is: %s F "
                "/ %s C" % (location, temp_f, temp_c))
            f.close()

            return parsed_json



        except (urllib2.HTTPError, urllib2.URLError) as e:
            self.logger.error(e)

            return None
