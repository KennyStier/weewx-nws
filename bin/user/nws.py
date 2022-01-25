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
import subprocess as sp

import weewx.drivers
import weeutil.weeutil

DRIVER_NAME = 'NWS'
DRIVER_VERSION = "2022.01.24"


def loader(config_dict, engine):

    station = NWS(**config_dict[DRIVER_NAME])

    return station


class NWS(weewx.drivers.AbstractDevice):
    
    def __init__(self, **stn_dict):
        
        self.observations = {
            'outTemp'    : get_observation('temperature'),
            'barometer'  : get_observation('barometricPressure'),
            'pressure'  : get_observation('seaLevelPressure'),
            'windSpeed'  : get_observation('windSpeed'),
            'windDir'    : get_observation('windDirection'),
            'windGust'   : get_observation('windGust'),
            'outHumidity': get_observation('relativeHumidity'),
            'dewpoint'   : get_observation('dewpoint'),
            'windchill'  : get_observation('windChill'),
            'heatindex'  : get_observation('heatIndex'),
            'rain'       : get_observation('precipitationLastHour')
        }

    def genLoopPackets(self):

        while True:

            _packet = {'dateTime': int(time.time()),
                       'usUnits' : weewx.METRIC }
            for obs_type in self.observations:
                _packet[obs_type] = self.observations[obs_type]
            yield _packet

            # Poll for updates
            lastUpdated = get_observation('timestamp')
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
        'temperature':           data['properties']['temperature']['value'],
        'barometricPressure':    data['properties']['barometricPressure']['value']/100 if isinstance(data['properties']['barometricPressure']['value'],(int,float)) else None,
        'seaLevelPressure':      data['properties']['seaLevelPressure']['value']/100 if isinstance(data['properties']['seaLevelPressure']['value'],(int,float)) else None,
        'windSpeed':             data['properties']['windSpeed']['value'],
        'windDirection':         data['properties']['windDirection']['value'],
        'windGust':              data['properties']['windGust']['value'],
        'relativeHumidity':      data['properties']['relativeHumidity']['value'],
        'dewpoint':              data['properties']['dewpoint']['value'],
        'windChill':             data['properties']['windChill']['value'],
        'heatIndex':             data['properties']['heatIndex']['value'],
        'precipitationLastHour': data['properties']['precipitationLastHour']['value']*100 if isinstance(data['properties']['precipitationLastHour']['value'],(int,float)) else None,
        'timestamp':             time.mktime(dateutil.parser.parse(data['properties']['timestamp']).timetuple())

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
