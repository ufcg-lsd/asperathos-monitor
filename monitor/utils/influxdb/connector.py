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


# TODO: We need to think in a better design solution
# for this
class InfluxConnector:
    def __init__(self, database_url, database_port, database_name,
                 database_user='root', database_password='root'):

        self.database_url = database_url
        self.database_port = database_port
        self.database_name = database_name
        self.database_user = database_user
        self.database_password = database_password

    def get_measurements(self):

        out = {}

        for i in self.get_job_progress():
            out[i['time']] = {'job_progress': i['value']}

        for i in self.get_time_progress():
            out[i['time']].update({'time_progress': i['value']})

        for i in self.get_replicas():
            out[i['time']].update({'replicas': i['value']})

        for i in self.get_error():
            out[i['time']].update({'error': i['value']})

        return out

    def get_cost_measurements(self):

        out = {}

        for i in self.get_current_spent():
            out[i['time']] = {'current_spent': i['value']}

        for i in self.get_desired_cost():
            out[i['time']].update({'desired_cost': i['value']})

        for i in self.get_replicas():
            out[i['time']].update({'replicas': i['value']})

        for i in self.get_application_cost_error():
            out[i['time']].update({'application_cost_error': i['value']})

        return out

    def get_stream_measurements(self):

        out = {}

        for i in self.get_real_output_flux():
            out[i['time']] = {'real_output_flux': i['value']}

        for i in self.get_expected_output_flux():
            out[i['time']].update({'expected_output_flux': i['value']})

        for i in self.get_input_flux():
            out[i['time']].update({'input_flux': i['value']})

        for i in self.get_replicas():
            out[i['time']].update({'replicas': i['value']})

        for i in self.get_error():
            out[i['time']].update({'error': i['value']})

        for i in self.get_queue_size():
            out[i['time']].update({'queue_size': i['value']})

        for i in self.get_lease_expired_count():
            out[i['time']].update({'lease_expired_count': i['value']})

        return out

    def get_queue_size(self):
        result = self._get_influx_client().\
            query('select value from queue_size;')
        return list(result.get_points(measurement='queue_size'))

    def get_current_spent(self):
        result = self._get_influx_client().\
            query('select value from current_spent;')
        return list(result.get_points(measurement='current_spent'))

    def get_desired_cost(self):
        result = self._get_influx_client().\
            query('select value from desired_cost;')
        return list(result.get_points(measurement='desired_cost'))

    def get_application_cost_error(self):
        result = self._get_influx_client().\
            query('select value from application_cost_error;')
        return list(result.get_points(measurement='application_cost_error'))

    def get_job_progress(self):
        result = self._get_influx_client().\
            query('select value from job_progress;')
        return list(result.get_points(measurement='job_progress'))

    def get_time_progress(self):
        result = self._get_influx_client().\
            query('select value from time_progress;')
        return list(result.get_points(measurement='time_progress'))

    def get_replicas(self):
        result = self._get_influx_client().\
            query('select value from job_parallelism;')
        return list(result.get_points(measurement='job_parallelism'))

    def get_real_output_flux(self):
        result = self._get_influx_client().\
            query('select value from real_output_flux;')
        return list(result.get_points(measurement='real_output_flux'))

    def get_expected_output_flux(self):
        result = self._get_influx_client().\
            query('select value from expected_output_flux;')
        return list(result.get_points(measurement='expected_output_flux'))

    def get_input_flux(self):
        result = self._get_influx_client().\
            query('select value from input_flux;')
        return list(result.get_points(measurement='input_flux'))

    def get_lease_expired_count(self):
        result = self._get_influx_client().\
            query('select value from lease_expired_count;')
        return list(result.get_points(measurement='lease_expired_count'))

    def get_error(self):
        result = self._get_influx_client().\
            query('select value from application_progress_error;')
        return \
            list(result.
                 get_points(measurement='application_progress_error'))

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
