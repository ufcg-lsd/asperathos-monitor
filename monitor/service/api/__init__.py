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

import ConfigParser
import os
import sys

CONFIG_PATH = "./data/conf"

try:
    # Conf reading
    config = ConfigParser.RawConfigParser()
    config.read('./monitor.cfg')
    
    """ General configuration """
    address = config.get('general', 'host')
    port = config.getint('general', 'port')
    plugins = config.get('general', 'plugins').split(',')
    use_debug = config.get('general', 'debug')
    retries = config.getint('general', 'retries')

    """ Validate if really exists a section to listed plugins """
    for plugin in plugins:
        if plugin != '' and plugin not in config.sections():
            raise Exception("plugin '%s' section missing" % plugin)
    
    if 'openstack_generic' in plugins:
        os_keypair = config.get('openstack_generic', 'key_pair')
    
    if 'spark_mesos' in plugins:
        mesos_cluster_addr = config.get('spark_mesos', 'mesos_cluster_addr')
        mesos_password = config.get('spark_mesos', 'mesos_password')
        mesos_username = config.get('spark_mesos', 'mesos_username')

    if 'kubejobs' in  plugins:

        # Setting default value
        k8s_manifest = CONFIG_PATH

        # If explicitly stated in the cfg file, overwrite the variable
        if(config.has_section('kubejobs')):
            if(config.has_option('kubejobs', 'k8s_manifest')):
                k8s_manifest = config.get('kubejobs', 'k8s_manifest')

    if 'external_api' in plugins:

        # Setting default value
        k8s_manifest = CONFIG_PATH

        # If explicitly stated in the cfg file, overwrite the variable
        if(config.has_section('external_api')):
            if(config.has_option('external_api', 'k8s_manifest')):
                k8s_manifest = config.get('external_api', 'k8s_manifest')

        metric_source = config.get('external_api', 'metric_source')
        get_metric_endpoint = config.get('external_api', 'get_metric_endpoint')
        threshold = config.get('external_api', 'threshold')
    
    """ Monasca parameters """
    monasca_endpoint = config.get('monasca', 'monasca_endpoint')
    monasca_username = config.get('monasca', 'username')
    monasca_password = config.get('monasca', 'password')
    monasca_auth_url = config.get('monasca', 'auth_url')
    monasca_project_name = config.get('monasca', 'project_name')
    monasca_api_version = config.get('monasca', 'api_version')

except Exception as e:
    print "Error: %s" % e.message
    quit()
