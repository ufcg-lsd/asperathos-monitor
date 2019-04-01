# Copyright (c) 2017 UFCG-LSD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from influxdb import InfluxDBClient


class InfluxConnector:
    def __init__(self, database_url, database_port, database_name,
                 database_user='root', database_password='root'):

        self.database_url = database_url
        self.database_port = database_port
        self.database_name = database_name
        self.database_user = database_user
        self.database_password = database_password
        self._get_influx_client()

    def get_measurements(self, metric_name, dimensions,
                         start_time='2014-01-01T00:00:00Z'):
        pass

    def first_measurement(self, name, dimensions):
        pass

    def last_measurement(self, name, dimensions):
        pass

    def _get_influx_client(self):

        client = InfluxDBClient(self.database_url, self.database_port,
                                self.database_user, self.database_password,
                                self.database_name)

        return client

    def send_metrics(self, measurements):

        measurements = measurements[0]
        metrics = {}

        metrics['measurement'] = measurements['name']
        metrics['time'] = datetime.\
            fromtimestamp(measurements['timestamp'] /
                          1000).strftime('%Y-%m-%dT%H:%M:%SZ')
        metrics['tags'] = {"host": "server01", "region": "sa-east-1",
                           "job": measurements['dimensions']['application_id']}
        metrics['fields'] = {'value': measurements['value']}

        self._get_influx_client().write_points([metrics])
