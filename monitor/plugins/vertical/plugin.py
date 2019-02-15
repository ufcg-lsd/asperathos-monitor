# Copyright (c) 2018 UFCG-LSD.
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

import os

import redis
import requests
import time
import subprocess
from subprocess import PIPE

from datetime import datetime
from monitor.utils.monasca.connector import MonascaConnector
from monitor.utils.influxdb.connector import InfluxConnector
from monitor.plugins.base import Plugin
from influxdb import InfluxDBClient

import kubernetes

LOG_FILE = "progress.log"
TIME_PROGRESS_FILE = "time_progress.log"
MONITORING_INTERVAL = 2


class VerticalProgress(Plugin):

    def __init__(self, app_id, info_plugin, collect_period=2, retries=10):
        Plugin.__init__(self, app_id, info_plugin,
                        collect_period, retries=retries)
        self.cpu_threshold = info_plugin['threshold']
        self.metric_source = info_plugin['metric_source']
        self.get_metric_endpoint = info_plugin['get_metric_endpoint']
        self.k8s_manifest = info_plugin['k8s_manifest']
        self.enable_visualizer = info_plugin['enable_visualizer']
        self.submission_url = info_plugin['count_jobs_url']
        self.expected_time = int(info_plugin['expected_time'])
        self.number_of_jobs = int(info_plugin['number_of_jobs'])
        self.submission_time = datetime.strptime(info_plugin['submission_time'],
                                                 '%Y-%m-%dT%H:%M:%S.%fGMT')
        self.dimensions = {'application_id': self.app_id,
                           'service': 'kubejobs'}
        self.rds = redis.StrictRedis(host=info_plugin['redis_ip'],
                                     port=info_plugin['redis_port'])
        self.metric_queue = "%s:metrics" % self.app_id
        self.current_job_id = 0
        if self.enable_visualizer:
            datasource_type = info_plugin['datasource_type']
            if datasource_type == "monasca":
                self.datasource = MonascaConnector()
            
            elif datasource_type == "influxdb":
                influx_url = info_plugin['database_data']['url']
                influx_port = info_plugin['database_data']['port']
                database_name = info_plugin['database_data']['name']
                self.datasource = InfluxConnector(influx_url, influx_port, database_name)
            else:
                print("Unknown datasource type...!")
        

    def _publish_measurement(self, cpu_usage):

        application_progress_error = {}
        cpu_usage_metric = {}
        cpu_quota_metric = {}

        # Reference Value
        ref_value = float(self.cpu_threshold)
        
        # Error
        
        print("CPU_USAGE: " + str(cpu_usage))
        print("REF_VALUE: " + str(ref_value))

        error = (float(cpu_usage)/100) - ref_value

        application_progress_error['name'] = ('application-progress'
                                              '.error')
        application_progress_error['value'] = error
        application_progress_error['timestamp'] = time.time() * 1000
        application_progress_error['dimensions'] = self.dimensions

        cpu_usage_metric['name'] = 'cpu-usage'
        cpu_usage_metric['value'] = float(cpu_usage)
        cpu_usage_metric['timestamp'] = time.time() * 1000
        cpu_usage_metric['dimensions'] = self.dimensions

        cpu_quota = self.get_cpu_quota()

        cpu_quota_metric['name'] = 'cpu-quota'
        cpu_quota_metric['value'] = float(cpu_quota)
        cpu_quota_metric['timestamp'] = time.time() * 1000
        cpu_quota_metric['dimensions'] = self.dimensions

        print "Error: %s " % application_progress_error['value']

        self.rds.rpush(self.metric_queue,
                       str(application_progress_error))

        if self.enable_visualizer:
            self.datasource.send_metrics([application_progress_error])
            self.datasource.send_metrics([cpu_usage_metric])
            self.datasource.send_metrics([cpu_quota_metric])
            
        time.sleep(MONITORING_INTERVAL)

    def _get_elapsed_time(self):
        datetime_now = datetime.now()
        elapsed_time = datetime_now - self.submission_time
        print "Elapsed Time: %.2f" % elapsed_time.seconds

        return elapsed_time.seconds

    def monitoring_application(self):
        try:
            cpu_usage = requests.get('http://%s:5000' % (self.get_api_address())).text
            
            print("Publishing metric %s value %s: " % (self.metric_source, cpu_usage))

            self._publish_measurement(cpu_usage=cpu_usage)

        except Exception as ex:
            print ("Error: No application found for %s. %s remaining attempts"
                   % (self.app_id, self.attempts))

            print ex.message
            raise

    def get_cpu_quota(self):
        try:
            cpu_quota = requests.get('http://%s:5000/%s' % (self.get_api_address(), self.get_metric_endpoint)).text
            return cpu_quota

        except Exception as ex:
            print("Error while getting %s metric" % (self.metric_source))
            print ex.message
            raise

    def get_api_address(self):

        kube.config.load_kube_config(self.k8s_manifest)
        CoreV1Api = kube.client.CoreV1Api()

        node_info = CoreV1Api.list_node().items[0]
        api_address = node_info.status.addresses[0].address

        return api_address
        