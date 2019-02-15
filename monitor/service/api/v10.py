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
import filecmp
import shutil
import sys

from monitor.service import api
from monitor import exceptions as ex
from monitor.utils.logger import Log
from monitor.plugins.builder import MonitorBuilder


API_LOG = Log("APIv10", "APIv10.log")

monitored_apps = {}
builder = MonitorBuilder()


def start_monitoring(data, app_id):
    """ These conditional cases choose the class executor's constructor of the 
    application submitted
    Note: some executors need the keypair to access remotely some machine and
    execute the monitoring logic, but this attribute is not mandatory for all
    the executors."""
 
    if 'plugin' not in data or 'plugin_info' not in data:
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    plugin = data['plugin']
    plugin_info = data['plugin_info']
   
    if app_id not in monitored_apps:
        executor = builder.get_monitor(plugin, app_id, plugin_info)
        monitored_apps[app_id] = executor
        executor.start()

    else:
        API_LOG.log("The application is already being monitored")
        raise ex.BadRequestException()


def stop_monitoring(app_id):
    if app_id not in monitored_apps:
        API_LOG.log("App doesn't exist")
        raise ex.BadRequestException()

    # Stop the plugin and remove from the data structure
    monitored_apps.pop(app_id, None).stop()

""" Add a new cluster that can be choose to be the active
   cluster in the Asperathos section in execution time.

Raises:
    ex.BadRequestException -- Missing cluster and authentication fields in request
    ex.UnauthorizedException -- Wrong authentication variables informed

Returns:
    dict -- Returns a dict with the cluster_name, 
    the status of the addition (success or failed) and a
    reason in case of 'failed' status
"""

def add_cluster(data):
    if ('cluster_name' not in data or 'cluster_config' not in data):
        API_LOG.log("Missing cluster fields in request")
        raise ex.BadRequestException("Missing cluster fields in request")

    if ('enable_auth' not in data):
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    enable_auth = data['enable_auth'] 

    if enable_auth:
        if 'username' not in data or 'password' not in data:
            API_LOG.log("Missing parameters in request")
            raise ex.BadRequestException()

        username = data['username']
        password = data['password']

        authorization = authorizer.get_authorization(api.authorization_url,
                                                 username, password)
                                            
        if not authorization['success']:
            API_LOG.log("Unauthorized request")
            raise ex.UnauthorizedException()

    conf_name = data['cluster_name']
    conf_content = data['cluster_config']

    if(os.path.isfile("./data/clusters/%s/%s" % (conf_name, conf_name))):
        status = "failed"
        reason = "cluster already exists"
    else:
        os.makedirs("./data/clusters/%s" % (conf_name))
        conf_file = open("./data/clusters/%s/%s" % (conf_name, conf_name), "w")
        conf_file.write(conf_content)
        conf_file.close()
        status = "success"
        reason = ""

    return {"cluster_name": conf_name, "status": status, "reason": reason}

""" Add a certificate to a cluster that can be choose to be the active
   cluster in the Asperathos section in execution time.

Raises:
    ex.BadRequestException -- Missing cluster and authentication fields in request
    ex.UnauthorizedException -- Wrong authentication variables informed

Returns:
    dict -- Returns a dict with the cluster_name, certificate_name, 
    the status of the addition (success or failed) and a
    reason in case of 'failed' status
"""

def add_certificate(cluster_name, data):
    if ('certificate_name' not in data or 'certificate_content' not in data):
        API_LOG.log("Missing fields in request")
        raise ex.BadRequestException("Missing fields in request")

    if ('enable_auth' not in data):
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    enable_auth = data['enable_auth'] 

    if enable_auth:
        if 'username' not in data or 'password' not in data:
            API_LOG.log("Missing parameters in request")
            raise ex.BadRequestException()

        username = data['username']
        password = data['password']

        authorization = authorizer.get_authorization(api.authorization_url,
                                                 username, password)
                                            
        if not authorization['success']:
            API_LOG.log("Unauthorized request")
            raise ex.UnauthorizedException()

    certificate_name = data['certificate_name']
    certificate_content = data['certificate_content']

    if(os.path.isdir("./data/clusters/%s" % (cluster_name))):
        if(os.path.isfile("./data/clusters/%s/%s" % (cluster_name, certificate_name))):
            status = "failed"
            reason = "certificate already exists"
        else:
            certificate_file = open("./data/clusters/%s/%s" % (cluster_name, certificate_name), "w")
            certificate_file.write(certificate_content)
            certificate_file.close()
            status = "success"
            reason = ""
    else:
        status = "failed"
        reason = "cluster does not exists"

    return {"cluster_name": cluster_name, "certificate_name": certificate_name, "status": status, "reason": reason}


""" Delete a cluster that could be choose to be the active
    cluster in the Asperathos section in execution time.

Raises:
    ex.BadRequestException -- Missing parameters in request
    ex.UnauthorizedException -- Authetication problem

Returns:
    dict -- Returns a dict with the cluster_name, 
    the status of the activation (success or failed) and a
    reason in case of 'failed' status
"""
def delete_cluster(cluster_name, data):

    if ('enable_auth' not in data):
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    enable_auth = data['enable_auth']

    if enable_auth:
        if 'username' not in data or 'password' not in data:
            API_LOG.log("Missing parameters in request")
            raise ex.BadRequestException()

        username = data['username']
        password = data['password']

        authorization = authorizer.get_authorization(api.authorization_url,
                                                 username, password)
                                            
        if not authorization['success']:
            API_LOG.log("Unauthorized request")
            raise ex.UnauthorizedException()
    
    conf_name = cluster_name

    if(not os.path.isfile("./data/clusters/%s/%s" % (conf_name, conf_name))):
        status = "failed"
        reason = "cluster does not exists in this Asperathos section"
    else:

        # Check if the cluster to be deleted is the currently active
        # if True, empty the config file currently being used.
        if('external_api' in api.plugins and
            filecmp.cmp("./data/clusters/%s/%s" % (conf_name, conf_name), api.k8s_manifest)):
            open(api.k8s_manifest, 'w').close()

        shutil.rmtree("./data/clusters/%s/" % (conf_name))

        status = "success"
        reason = ""

    return {"cluster_name": conf_name, "status": status, "reason": reason}

""" Delete a certificate to a cluster that can be choose to be the active
   cluster in the Asperathos section in execution time.

Raises:
    ex.BadRequestException -- Missing parameters in request
    ex.UnauthorizedException -- Authetication problem

Returns:
    dict -- Returns a dict with the cluster_name, certificate_name, 
    the status of the deletion (success or failed) and a
    reason in case of 'failed' status
"""
def delete_certificate(cluster_name, certificate_name, data):

    if ('enable_auth' not in data):
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    enable_auth = data['enable_auth']

    if enable_auth:
        if 'username' not in data or 'password' not in data:
            API_LOG.log("Missing parameters in request")
            raise ex.BadRequestException()

        username = data['username']
        password = data['password']

        authorization = authorizer.get_authorization(api.authorization_url,
                                                 username, password)
                                            
        if not authorization['success']:
            API_LOG.log("Unauthorized request")
            raise ex.UnauthorizedException()
    
    if(os.path.isdir("./data/clusters/%s" % (cluster_name))):
        if(os.path.isfile("./data/clusters/%s/%s" % (cluster_name, certificate_name))):
            os.remove("./data/clusters/%s/%s" % (cluster_name, certificate_name))
            status = "success"
            reason = ""
        else:
            status = "failed"
            reason = "certificate does not exists."
    else:
        status = "failed"
        reason = "cluster does not exists."

    return {"cluster_name": cluster_name, "certificate_name": certificate_name, "status": status, "reason": reason}


""" Activate a cluster to be used in a Asperathos section

Raises:
    ex.BadRequestException -- Missing parameters in request
    ex.UnauthorizedException -- Authetication problem

Returns:
    dict -- Returns a dict with the cluster_name, 
    the status of the activation (success or failed) and a
    reason in case of 'failed' status
"""

def active_cluster(cluster_name, data):

    if ('enable_auth' not in data):
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    enable_auth = data['enable_auth'] 

    if enable_auth:
        if 'username' not in data or 'password' not in data:
            API_LOG.log("Missing parameters in request")
            raise ex.BadRequestException()

        username = data['username']
        password = data['password']

        authorization = authorizer.get_authorization(api.authorization_url,
                                                 username, password)
                                            
        if not authorization['success']:
            API_LOG.log("Unauthorized request")
            raise ex.UnauthorizedException()

    conf_name = cluster_name

    if(not os.path.isfile("./data/clusters/%s/%s" % (conf_name, conf_name))):
        status = "failed"
        reason = "cluster does not exists in this Asperathos section"
    else:

        with open("./data/clusters/%s/%s" % (conf_name, conf_name), 'r') as f:
            with open(api.k8s_manifest, 'w') as f1:
                for line in f:
                    f1.write(line) 
        
        status = "success"
        reason = ""

    return {"cluster_name": conf_name, "status": status, "reason": reason}
