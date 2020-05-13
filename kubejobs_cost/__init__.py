# Copyright (c) 2020 UFCG-LSD.
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


from kubejobs import KubeJobProgress
from monitor.utils.plugin import k8s
from monitor.utils.logger import Log
from monitor.utils.job_report.job_report import JobReport
from datetime import datetime

import requests
import json
import time

LOG_FILE = "progress.log"
LOG_NAME = "kubejobs-progress"


class KubeJobCost(KubeJobProgress):

    def __init__(self, app_id, info_plugin):

        KubeJobProgress.__init__(self, app_id, info_plugin,
                                 retries=20)
        self.cluster_info_url = info_plugin.get('cluster_info_url')
        self.desired_cost = info_plugin.get('desired_cost')
        self.last_error = None
        self.last_rep = None
        self.last_cost = None
        self.metric_queue = "%s:metrics:cost" % self.app_id
        self.LOG = Log(LOG_NAME, LOG_FILE)
        self.job_report = JobReport(info_plugin)

    def monitoring_application(self):
        try:
            if self.report_flag:

                self.calculate_error()
                self.LOG.log("Calculated error")
                timestamp = time.time() * 1000
                err_manifest = \
                    self.get_application_cost_error_manifest(self.last_error,
                                                             timestamp)
                self.LOG.log(err_manifest)
                self.LOG.log("Publishing error")
                self.rds.rpush(self.metric_queue,
                               str(err_manifest))

                self.LOG.log("Getting replicas")
                replicas_manifest = \
                    self.get_parallelism_manifest(self.last_replicas,
                                                  timestamp)
                self.LOG.log(replicas_manifest)

                reference_manifest = self.get_reference_manifest(timestamp)

                self.LOG.log("Getting cost")
                current_cost_manifest = \
                    self.get_current_cost_manifest(timestamp)
                self.LOG.log(current_cost_manifest)

                self.publish_persistent_measurement(err_manifest,
                                                    reference_manifest,
                                                    current_cost_manifest,
                                                    replicas_manifest)

                self.report_job(timestamp)

        except Exception as ex:
            self.LOG.log(ex)

    def report_job(self, timestamp):
        if self.report_flag:
            self.LOG.log("report_flag-cost")
            self.job_report.set_start_timestamp(timestamp)
            current_time = datetime.fromtimestamp(timestamp/1000)\
                                   .strftime('%Y-%m-%dT%H:%M:%SZ')
            if self.last_progress == 1:
                self.job_report.calculate_execution_time(timestamp)
            self.job_report.\
                verify_and_set_max_error(self.last_error, current_time)
            self.job_report.\
                verify_and_set_min_error(self.last_error, current_time)

            if self.job_is_completed():
                self.report_flag = False
                self.job_report.calculate_execution_time(timestamp)
                self.generate_report(current_time)

    # TODO: We need to think in a better design solution
    # for this
    def get_detailed_report(self):
        if not self.report_flag:
            return self.datasource.get_cost_measurements()
        return {'message': 'Job is still running...'}

    def get_reference_manifest(self, timestamp):
        reference_manifest = {'name': 'desired_cost',
                              'value': self.desired_cost,
                              'timestamp': timestamp,
                              'dimensions': self.dimensions
                              }
        return reference_manifest

    def get_current_cost_manifest(self, timestamp):
        current_cost_manifest = {'name': 'current_spent',
                                 'value': self.last_cost,
                                 'timestamp': timestamp,
                                 'dimensions': self.dimensions
                                 }
        return current_cost_manifest

    def get_parallelism_manifest(self, replicas, timestamp):
        parallelism = {'name': 'job_parallelism_cost',
                       'value': replicas,
                       'timestamp': timestamp,
                       'dimensions': self.dimensions
                       }
        return parallelism

    def calculate_error(self):
        rep = self._get_num_replicas()
        cpu_cost, memory_cost = self.get_current_cost()
        cpu_usage, memory_usage = \
            k8s.get_current_job_resources_usage(self.app_id)
        job_cpu_cost = cpu_cost * cpu_usage
        job_memory_cost = memory_cost * memory_usage
        job_total_cost = job_cpu_cost + job_memory_cost

        err = job_total_cost - self.desired_cost

        self.pretty_print(cpu_cost, memory_cost, cpu_usage,
                          memory_usage, job_total_cost, err)
        self.last_error = err
        self.last_cost = job_total_cost
        self.last_rep = rep
        return err

    def pretty_print(self, cpu_cost, memory_cost, cpu_usage,
                     memory_usage, job_total_cost, err):

        self.LOG.log('Cpu usage: {}\nCpu cost: {}\nMemory usage:'
                     ' {}\nMemory cost: {}\nJob cost: {}\nError: {}'.
                     format(cpu_usage, cpu_cost, memory_usage,
                            memory_cost, job_total_cost, err))

    def get_application_cost_error_manifest(self, error, timestamp):
        application_progress_error = {'name': 'application_cost_error',
                                      'value': error,
                                      'timestamp': timestamp,
                                      'dimensions': self.dimensions
                                      }
        return application_progress_error

    def get_current_cost(self):

        cost = json.loads(requests.get(self.cluster_info_url.strip()).text)
        total_cost = float(cost.get('cpu_price')),\
            float(cost.get('memory_price'))

        return total_cost

    def get_dimensions(self):
        return {'application_id': self.app_id,
                'service': 'kubejobs_cost'}


PLUGIN = KubeJobCost
