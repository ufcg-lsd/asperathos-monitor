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

import requests
import json
import time

# Think about better metric to use
DIVISOR = 100


class KubeJobCost(KubeJobProgress):

    def __init__(self, app_id, info_plugin):

        KubeJobProgress.__init__(self, app_id, info_plugin,
                                 collect_period=2, retries=20)
        self.cluster_info_url = info_plugin.get('cluster_info_url')
        self.desired_cost = info_plugin.get('desired_cost')
        self.last_error = None
        self.last_rep = None
        self.last_cost = None

    def monitoring_application(self):
        
        if self.report_flag:
            
            self.calculate_error()
            timestamp = time.time() * 1000

            err_manifest = self.get_application_cost_error_manifest(self.last_error, timestamp)
            self.rds.rpush(self.metric_queue,
                        str(err_manifest))


            replicas_manifest = self.get_parallelism_manifest(self.last_replicas, timestamp)

            reference_manifest = self.get_reference_manifest(timestamp)

            current_cost_manifest = self.get_current_cost_manifest(timestamp)

            self.publish_persistent_measurement(err_manifest, reference_manifest,
                                                current_cost_manifest, replicas_manifest)

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

    def calculate_error(self):
        rep = self._get_num_replicas()
        cpu_cost, memory_cost = self.get_current_cost()
        cpu_usage, memory_usage = \
            k8s.get_current_job_resources_usage(self.app_id)
        job_cpu_cost = cpu_cost * cpu_usage
        job_memory_cost = memory_cost * memory_usage
        job_total_cost = job_cpu_cost + job_memory_cost
        current_cost_each_pod = job_total_cost / rep
        desired_num_of_replicas = self.desired_cost / current_cost_each_pod
        err = (rep - desired_num_of_replicas + 1) / DIVISOR
        self.pretty_print(rep, cpu_cost, memory_cost, cpu_usage,
                          memory_usage, job_total_cost,
                          desired_num_of_replicas, err)
        self.last_error = err
        self.last_cost = job_total_cost
        self.last_rep = rep
        return err

    def pretty_print(self, rep, cpu_cost, memory_cost,
                     cpu_usage, memory_usage, job_total_cost,
                     desired_rep, err):

        self.LOG.log('Current Replicas: {}\nDesired Replicas: {}\n'
                     'Cpu usage: {}\nCpu cost: {}\nMemory usage:'
                     ' {}\nMemory cost: {}\nJob cost: {}\nError: {}'.
                     format(rep, desired_rep, cpu_usage, cpu_cost,
                            memory_usage, memory_cost, job_total_cost, err))

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
