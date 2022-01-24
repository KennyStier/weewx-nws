#
#    National Weather Service Weewx Driver
#    Copyright (c) 2022 Kenny Stier <4749568+KennyStier@users.noreply.github.com>
#
#    Derived from the Weewx Simulator driver
#    Copyright (c) 2009-2015 Tom Keffer <tkeffer@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""Console simulator for the weewx weather system"""

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function
from urllib import response
import requests
import json
import time

import weewx.drivers
import weeutil.weeutil

DRIVER_NAME = 'NWS'
DRIVER_VERSION = "2022.01.24"


def loader(config_dict, engine):

    station = NWS(**config_dict[DRIVER_NAME])

    return station


class NWS(weewx.drivers.AbstractDevice):
    """Station simulator"""
    
    def __init__(self, **stn_dict):
        """Initialize the simulator
        
        NAMED ARGUMENTS:
        
        loop_interval: The time (in seconds) between emitting LOOP packets.
        [Optional. Default is 2.5]
        
        start_time: The start (seed) time for the generator in unix epoch time
        [Optional. If 'None', or not present, then present time will be used.]

        resume_time: The start time for the loop.
        [Optional. If 'None', or not present, then start_time will be used.]
        
        mode: Controls the frequency of packets.  One of either:
            'simulator': Real-time simulator - sleep between LOOP packets
            'generator': Emit packets as fast as possible (useful for testing)
        [Required. Default is simulator.]

        observations: Comma-separated list of observations that should be
                      generated.  If nothing is specified, then all
                      observations will be generated.
        [Optional. Default is not defined.]
        """

        self.observations = {
            'outTemp'    : get_observation('temperature'),
            'barometer'  : get_observation('barometricPressure'),
            'windSpeed'  : get_observation('windSpeed'),
            'windDir'    : get_observation('windDirection'),
            'windGust'   : get_observation('windGust'),
            'outHumidity': get_observation('relativeHumidity'),
            'dewpoint'   : get_observation('dewpoint'),
            'windchill'  : get_observation('windChill'),
            'heatindex'  : get_observation('headIndex')
        }

    def genLoopPackets(self):

        while True:

            _packet = {'dateTime': int(time.time()),
                       'usUnits' : weewx.METRIC }
            for obs_type in self.observations:
                _packet[obs_type] = self.observations[obs_type]
            yield _packet

        time.sleep(60)

    @property
    def hardware_name(self):
        return "National Weather Service"

def get_observation(obs):

    url = "https://api.weather.gov/stations/KLAF/observations/latest"
    r = requests.get(url)

    data = r.json()
    dict={
        'temperature':         data['properties']['temperature']['value'],
        'barometricPressure':  data['properties']['barometricPressure']['value']/100,
        'windSpeed':           data['properties']['windSpeed']['value'],
        'windDirection':       data['properties']['windDirection']['value'],
        'windGust':            data['properties']['windGust']['value'],
        'outHumidity':         data['properties']['relativeHumidity']['value'],
        'dewpoint':            data['properties']['dewpoint']['value'],
        'windChill':           data['properties']['windChill']['value'],
        'heatIndex':           data['properties']['heatIndex']['value']
    }
    return(dict.get(obs))


def confeditor_loader():
    return SimulatorConfEditor()


class SimulatorConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[NWS]
    # This section is for the weewx weather station simulator

    # The time (in seconds) between LOOP packets.
    loop_interval = 2.5

    # The simulator mode can be either 'simulator' or 'generator'.
    # Real-time simulator. Sleep between each LOOP packet.
    mode = simulator
    # Generator.  Emit LOOP packets as fast as possible (useful for testing).
    #mode = generator

    # The start time. Format is YYYY-mm-ddTHH:MM. If not specified, the default 
    # is to use the present time.
    #start = 2011-01-01T00:00

    # The driver to use:
    driver = weewx.drivers.nws
"""


if __name__ == "__main__":
    station = NWS(mode='simulator',loop_interval=2.0)
    for packet in station.genLoopPackets():
        print(weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet)
