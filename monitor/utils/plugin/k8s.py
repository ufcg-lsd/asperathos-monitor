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

from monitor.service import api

import kubernetes as kube


kube.config.load_kube_config(api.k8s_manifest)


def get_running_pods_from_a_job(job_id, namespace='default'):
    api_instance = kube.client.CoreV1Api()

    pod_names = []
    for pod in api_instance.list_namespaced_pod(namespace).items:
        if pod.metadata.labels.get('job-name') == job_id.strip() \
                and pod.status.phase == 'Running':
            pod_names.append(pod.metadata.name)
    return pod_names


def convert_cpu_memory_unity(resources):
    '''
    Convert cpu unity from Nanocpu to Milicpu
    and memory unity from Kibibyte to Gigabyte
    '''

    cpu = resources.get('cpu')
    memory = resources.get('memory')

    vcpu = cpu / (10.0 ** 6) / 1000
    gb_memory = (memory * (2 ** 10)) / 10 ** 9

    return {
        'cpu': vcpu,
        'memory': gb_memory
    }


def get_current_job_resources_usage(job_id):
    list_pods = get_running_pods_from_a_job(job_id)

    total_cpu = 0
    total_memory = 0
    cust = kube.client.CustomObjectsApi()
    for pod in cust.list_cluster_custom_object('metrics.k8s.io',
                                               'v1beta1', 'pods').\
            get('items'):
        if pod.get('metadata').get('name') in list_pods:
            for container in pod.get('containers'):
                cpu = container.get('usage').get('cpu')[:-1]
                memory = container.get('usage').get('memory')[:-2]

                total_cpu += int(cpu)
                total_memory += int(memory)

    converted_usage = convert_cpu_memory_unity({
        'cpu': total_cpu,
        'memory': total_memory
    })

    return converted_usage.get('cpu'), converted_usage.get('memory')
