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

from datetime import datetime
import time

import redis
import six

from monitor import exceptions as ex
from monitor.plugins.base import Plugin
from monitor.service import api
from monitor.utils.influxdb.connector import InfluxConnector
from monitor.utils.logger import Log
from monitor.utils.monasca.connector import MonascaConnector

import kubernetes

LOG_FILE = "progress.log"
LOG_NAME = "kubejobs-progress"

MONITORING_INTERVAL = 2


class KubeJobProgress(Plugin):

    def __init__(self, app_id, info_plugin, collect_period=2, retries=10):
        Plugin.__init__(self, app_id, info_plugin,
                        collect_period, retries=retries)
        self.validate(info_plugin)
        self.LOG = Log(LOG_NAME, LOG_FILE)
        self.enable_visualizer = info_plugin['enable_visualizer']
        self.expected_time = int(info_plugin['expected_time'])
        self.number_of_jobs = int(info_plugin['number_of_jobs'])
        self.submission_time = datetime.\
            strptime(info_plugin['submission_time'],
                     '%Y-%m-%dT%H:%M:%S.%fGMT')
        self.dimensions = {'application_id': self.app_id,
                           'service': 'kubejobs'}
        self.rds = redis.StrictRedis(host=info_plugin['redis_ip'],
                                     port=info_plugin['redis_port'])
        self.metric_queue = "%s:metrics" % self.app_id
        self.current_job_id = 0

        kubernetes.config.load_kube_config(api.k8s_manifest)
        self.b_v1 = kubernetes.client.BatchV1Api()

        if self.enable_visualizer:
            datasource_type = info_plugin['datasource_type']
            if datasource_type == "monasca":
                self.datasource = MonascaConnector()
            elif datasource_type == "influxdb":
                influx_url = info_plugin['database_data']['url']
                influx_port = info_plugin['database_data']['port']
                database_name = info_plugin['database_data']['name']
                self.datasource = InfluxConnector(
                    influx_url, influx_port, database_name)
            else:
                self.LOG.log("Unknown datasource type...!")

    def _publish_measurement(self, jobs_completed):

        application_progress_error = {}
        job_progress_error = {}
        time_progress_error = {}
        parallelism = {}

        # Init
        self.LOG.log("Jobs Completed: %i" % jobs_completed)

        # Job Progress

        job_progress = min(1.0, (float(jobs_completed) / self.number_of_jobs))
        # Elapsed Time
        elapsed_time = float(self._get_elapsed_time())

        # Reference Value
        ref_value = (elapsed_time / self.expected_time)
        replicas = self._get_num_replicas()
        # Error
        self.LOG.log("Job progress: %s\nTime Progress: %s\nReplicas: %s"
                     "\n========================"
                     % (job_progress, ref_value, replicas))

        error = job_progress - ref_value

        application_progress_error['name'] = ('application-progress'
                                              '.error')

        application_progress_error['value'] = error
        application_progress_error['timestamp'] = time.time() * 1000
        application_progress_error['dimensions'] = self.dimensions

        job_progress_error['name'] = 'job-progress'
        job_progress_error['value'] = job_progress
        job_progress_error['timestamp'] = time.time() * 1000
        job_progress_error['dimensions'] = self.dimensions

        time_progress_error['name'] = 'time-progress'
        time_progress_error['value'] = ref_value
        time_progress_error['timestamp'] = time.time() * 1000
        time_progress_error['dimensions'] = self.dimensions

        parallelism['name'] = "job-parallelism"
        parallelism['value'] = replicas
        parallelism['timestamp'] = time.time() * 1000
        parallelism['dimensions'] = self.dimensions

        self.LOG.log("Error: %s " % application_progress_error['value'])

        self.rds.rpush(self.metric_queue,
                       str(application_progress_error))

        if self.enable_visualizer:
            self.datasource.send_metrics([application_progress_error])
            self.datasource.send_metrics([job_progress_error])
            self.datasource.send_metrics([time_progress_error])
            self.datasource.send_metrics([parallelism])

        time.sleep(MONITORING_INTERVAL)

    def _get_num_replicas(self):
        job = self.b_v1.read_namespaced_job(
            name=self.app_id, namespace="default")
        return job.status.active

    def _get_elapsed_time(self):
        datetime_now = datetime.now()
        elapsed_time = datetime_now - self.submission_time
        self.LOG.log("Elapsed Time: %.2f" % elapsed_time.seconds)

        return elapsed_time.seconds

    def monitoring_application(self):
        try:
            num_queued_jobs = self.rds.llen('job')
            num_processing_jobs = self.rds.llen('job:processing')

            job_progress = self.number_of_jobs - \
                (num_queued_jobs + num_processing_jobs)
            self._publish_measurement(jobs_completed=job_progress)
            return job_progress

        except Exception as ex:
            self.LOG.log(("Error: No application found for %s.\
                 %s remaining attempts")
                         % (self.app_id, self.attempts))

            self.LOG.log(ex.message)
            raise

    def validate(self, data):
        data_model = {
            "enable_visualizer": bool,
            "expected_time": int,
            "number_of_jobs": int,
            "redis_ip": six.string_types,
            "redis_port": int,
            "submission_time": six.string_types
        }

        if 'enable_visualizer' in data and data['enable_visualizer']:
            data_model.update({"datasource_type": six.string_types})

        for key in data_model:
            if (key not in data):
                raise ex.BadRequestException(
                    "Variable \"{}\" is missing".format(key))

            if (not isinstance(data[key], data_model[key])):
                raise ex.BadRequestException(
                    "\"{}\" has unexpected variable type: {}. Was expecting {}"
                    .format(key, type(data[key]), data_model[key]))
