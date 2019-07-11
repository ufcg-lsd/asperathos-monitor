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
from monitor.utils.job_report.job_report import JobReport

import kubernetes

LOG_FILE = "progress.log"
LOG_NAME = "kubejobs-progress"

MONITORING_INTERVAL = 2


class KubeJobProgress(Plugin):

    def __init__(self, app_id, info_plugin, collect_period=2,
                 retries=10, last_replicas=None):

        Plugin.__init__(self, app_id, info_plugin,
                        collect_period, retries=retries)
        self.validate(info_plugin)
        self.LOG = Log(LOG_NAME, LOG_FILE)
        self.enable_visualizer = info_plugin['enable_visualizer']
        self.expected_time = int(info_plugin['expected_time'])
        self.number_of_jobs = int(info_plugin['number_of_jobs'])
        self.submission_time = self.get_submission_time(info_plugin)
        self.dimensions = self.get_dimensions()
        self.rds = self.setup_redis(info_plugin)
        self.metric_queue = "%s:metrics" % self.app_id
        self.current_job_id = 0
        self.job_report = JobReport(info_plugin)
        self.report_flag = True
        self.last_replicas = last_replicas
        self.last_error = None
        self.last_progress = None
        kubernetes.config.load_kube_config(api.k8s_manifest)
        self.b_v1 = kubernetes.client.BatchV1Api()
        self.datasource = self.setup_datasource(info_plugin)
    
    def get_dimensions(self):
        return {'application_id': self.app_id,
                'service': 'kubejobs'}
    
    def get_submission_time(self, info_plugin):
        return datetime.strptime(info_plugin['submission_time'],
                                 '%Y-%m-%dT%H:%M:%S.%fGMT')
        
    def setup_redis(self, info_plugin):
        return redis.StrictRedis(host=info_plugin['redis_ip'],
                                 port=info_plugin['redis_port'])

    def setup_datasource(self, info_plugin):
        if self.enable_visualizer:
            datasource_type = info_plugin['datasource_type']
            if datasource_type == "monasca":
                return MonascaConnector()
            elif datasource_type == "influxdb":
                influx_url = info_plugin['database_data']['url']
                influx_port = info_plugin['database_data']['port']
                database_name = info_plugin['database_data']['name']
                return InfluxConnector(influx_url,
                                       influx_port,
                                       database_name)
            else:
                raise ex.BadRequestException("Unknown datasource type...!")

    def calculate_measurement(self, jobs_completed):
        job_progress = self.get_job_progress(jobs_completed)
        ref_value = self.get_ref_value()
        replicas = self._get_num_replicas()       
        error = self.get_error(job_progress, ref_value)
        
        return job_progress, ref_value, replicas, error

    def get_error(self, job_progress, ref_value):
        error = job_progress - ref_value
        self.last_error = error
        return error

    def get_ref_value(self):
        elapsed_time = float(self._get_elapsed_time())
        ref_value = (elapsed_time / self.expected_time)
        return ref_value
        
    def get_job_progress(self, jobs_completed):
        job_progress = min(1.0, (float(jobs_completed) / self.number_of_jobs))
        return job_progress

    def get_parallelism_manifest(self, replicas, timestamp):
        parallelism = {'name': 'job-parallelism',
                       'value': replicas,
                       'timestamp': timestamp,
                       'dimensions': self.dimensions
                      }
        return parallelism

    def get_time_progress_error_manifest(self, ref_value, timestamp):
        time_progress_error = {'name': 'time-progress',
                              'value': ref_value,
                              'timestamp': timestamp,
                              'dimensions': self.dimensions
                              }

        return time_progress_error

    def get_job_progress_error_manifest(self, job_progress, timestamp):
        job_progress_error = {'name': 'job-progress',
                              'value': job_progress,
                              'timestamp': timestamp,
                              'dimensions': self.dimensions
                             }
        return job_progress_error
    def get_application_progress_error_manifest(self, error, timestamp):
        application_progress_error = {'name': 'application-progress.error',
                                      'value': error,
                                      'timestamp': timestamp,
                                      'dimensions': self.dimensions
                                     }
        return application_progress_error

    def _publish_measurement(self, jobs_completed):

        self.LOG.log("Jobs Completed: %i" % jobs_completed)
        job_progress, ref_value, replicas, error = \
            self.calculate_measurement(jobs_completed)
        
        self.last_progress = job_progress
        timestamp = time.time() * 1000
        application_progress_error = \
            self.get_application_progress_error_manifest(error, timestamp)
        
        self.rds.rpush(self.metric_queue,
                       str(application_progress_error))
        
        if self.enable_visualizer:
            job_progress_error = \
                self.get_job_progress_error_manifest(job_progress, timestamp)
            time_progress_error = \
                self.get_time_progress_error_manifest(ref_value, timestamp)
            parallelism = \
                self.get_parallelism_manifest(replicas, timestamp)
        
            self.LOG.log("Error: %s " % application_progress_error['value'])
        
            self.publish_visualizer_measurement(application_progress_error,
                                                job_progress_error,
                                                time_progress_error,
                                                parallelism)   
        self.report_job()
        time.sleep(MONITORING_INTERVAL)

    def publish_visualizer_measurement(self, application_progress_error,
                                       job_progress_error,
                                       time_progress_error,
                                       parallelism):
        
        self.datasource.send_metrics([application_progress_error])
        self.datasource.send_metrics([job_progress_error])
        self.datasource.send_metrics([time_progress_error])
        self.datasource.send_metrics([parallelism])

    def report_job(self):
        if self.report_flag:
            current_time = str(datetime.now())
            self.job_report.verify_and_set_max_error(self.last_error, current_time)
            self.job_report.verify_and_set_min_error(self.last_error, current_time)

            if self.last_progress == 1 or self.job_is_completed():
                self.report_flag = False
                self.generate_report()

    def generate_report(self, current_time=str(datetime.now())):
            self.job_report.set_final_error(self.last_error, current_time)
            self.job_report.set_final_replicas(self.last_replicas)
            self.job_report.generate_report(self.app_id)

    def _get_num_replicas(self):
        job = self.b_v1.read_namespaced_job(
            name=self.app_id, namespace="default")
        replicas = job.status.active
        if replicas is not None: self.last_replicas = replicas
        return replicas
    
    def job_is_completed(self):

        job = self.b_v1.read_namespaced_job(
            name=self.app_id, namespace="default")

        if job.status.active is None:
            return True
        return False

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
            self.report_job()
            self.generate_report()
            self.LOG.log(ex.message)
            raise

    def validate(self, data):
        data_model = {
            "enable_visualizer": bool,
            "expected_time": int,
            "number_of_jobs": int,
            "redis_ip": six.string_types,
            "redis_port": int,
            "submission_time": six.string_types,
            "scaling_strategy": six.string_types
        }

        if 'enable_visualizer' in data and data['enable_visualizer']:
            data_model.update({"datasource_type": six.string_types,
                               "database_data": dict
                              })

        if 'scaling_strategy' in data and data['scaling_strategy'] == 'pid':
            data_model.update({"heuristic_options": dict})

        for key in data_model:
            if (key not in data):
                raise ex.BadRequestException(
                    "Variable \"{}\" is missing".format(key))

            if (not isinstance(data[key], data_model[key])):
                raise ex.BadRequestException(
                    "\"{}\" has unexpected variable type: {}. Was expecting {}"
                    .format(key, type(data[key]), data_model[key]))

PLUGIN = KubeJobProgress
