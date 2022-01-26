#
#    National Weather Service Weewx Driver
#    Copyright (c) 2022 Kenny Stier <4749568+KennyStier@users.noreply.github.com>
#
#    Derived from the Weewx Simulator driver
#    Copyright (c) 2009-2015 Tom Keffer <tkeffer@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function
from urllib import response
import requests
import json
import time
import dateutil.parser
import pytz

import weewx.drivers
import weeutil.weeutil

DRIVER_NAME = 'NWS'
DRIVER_VERSION = "2022.01.24"


def loader(config_dict, engine):

    station = NWS(**config_dict[DRIVER_NAME])

    return station


class NWS(weewx.drivers.AbstractDevice):
    
    def __init__(self, **stn_dict):

        self.observations = ['outTemp','barometer','pressure','windSpeed','windDir','windGust','outHumidity','dewpoint','windchill','heatindex','rain']

    def genLoopPackets(self):

        while True:

            _packet = {'dateTime': get_observation('timestamp'),
                       'usUnits' : weewx.METRIC }
            for obs_type in self.observations:
                _packet[obs_type] = get_observation(obs_type)
            yield _packet

            # Poll for updates
            lastUpdated = _packet['dateTime']
            time.sleep(60)

            while lastUpdated == get_observation('timestamp'):
                time.sleep(60)

    @property
    def hardware_name(self):
        return "National Weather Service"

def get_observation(obs):

    url = "https://api.weather.gov/stations/KLAF/observations/latest"
    r = requests.get(url, timeout=30)

    data = r.json()
    obsmap={
        'outTemp':           data['properties']['temperature']['value'],
        'barometer':    data['properties']['barometricPressure']['value']/100 if isinstance(data['properties']['barometricPressure']['value'],(int,float)) else None,
        'pressure':      data['properties']['seaLevelPressure']['value']/100 if isinstance(data['properties']['seaLevelPressure']['value'],(int,float)) else None,
        'windSpeed':             data['properties']['windSpeed']['value'],
        'windDir':         data['properties']['windDirection']['value'],
        'windGust':              data['properties']['windGust']['value'],
        'outHumidity':      data['properties']['relativeHumidity']['value'],
        'dewpoint':              data['properties']['dewpoint']['value'],
        'windchill':             data['properties']['windChill']['value'],
        'heatindex':             data['properties']['heatIndex']['value'],
        'rain': data['properties']['precipitationLastHour']['value']*100 if isinstance(data['properties']['precipitationLastHour']['value'],(int,float)) else None,
        'timestamp':             int(time.mktime(dateutil.parser.parse(data['properties']['timestamp']).astimezone(pytz.timezone('America/Indianapolis')).timetuple()))

    }
    return(obsmap.get(obs))


def confeditor_loader():
    return NWSConfEditor()


class NWSConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[NWS]
    # Airport code of station to collect from
    icao = KLAF

    # The driver to use:
    driver = weewx.drivers.nws
"""


if __name__ == "__main__":
    station = NWS()
    for packet in station.genLoopPackets():
        print(weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet)
