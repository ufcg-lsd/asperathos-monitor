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
from monitor.utils.logger import Log

LOG_FILE = "progress.log"
LOG_NAME = "kubejobs-progress"
LOG = Log(LOG_NAME, LOG_FILE)

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

    # Setting default value
    k8s_manifest = CONFIG_PATH
    if 'kubejobs' in plugins:
        # If explicitly stated in the cfg file, overwrite the variable
        if(config.has_section('kubejobs')):
            if(config.has_option('kubejobs', 'k8s_manifest')):
                k8s_manifest = config.get('kubejobs', 'k8s_manifest')

    """ Monasca parameters """
    monasca_endpoint = config.get('monasca', 'monasca_endpoint')
    monasca_username = config.get('monasca', 'username')
    monasca_password = config.get('monasca', 'password')
    monasca_auth_url = config.get('monasca', 'auth_url')
    monasca_project_name = config.get('monasca', 'project_name')
    monasca_api_version = config.get('monasca', 'api_version')

except Exception as e:
    LOG.log("Error: %s" % e.message)
    quit()
