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

from flask import request
from monitor.service.api import v10 as api

from monitor.utils import api as u


rest = u.Rest('v10', __name__)


""" Start monitoring a running application.

    Normal response codes: 202
    Error response codes: 400
"""
@rest.post('/monitoring/<app_id>')
def start_monitoring(data, app_id):
    return u.render(api.start_monitoring(data, app_id))


""" Stop monitoring a running application.

    Normal response codes: 204
    Error response codes: 400
"""
@rest.put('/monitoring/<app_id>/stop')
def stop_monitoring(app_id, data):
    return u.render(api.stop_monitoring(app_id))

""" Add a new cluster reference in the Asperathos section.

    Normal response codes: 202
    Error response codes: 400, 401
"""
@rest.post('/monitoring/cluster')
def add_cluster(data):
    return u.render(api.add_cluster(data))

""" Add a certificate to a cluster reference in the Asperathos section.

    Normal response codes: 202
    Error response codes: 400, 401
"""
@rest.post('/monitoring/cluster/<cluster_name>/certificate')
def add_certificate(cluster_name, data):
    return u.render(api.add_certificate(cluster_name, data)) 

""" Delete a cluster reference in the Asperathos section.

    Normal response codes: 202
    Error response codes: 400, 401
"""
@rest.post('/monitoring/cluster/<cluster_name>/delete')
def delete_cluster(cluster_name, data):
    return u.render(api.delete_cluster(cluster_name, data)) 

""" Delete a certificate to a cluster reference in the Asperathos section.

    Normal response codes: 202
    Error response codes: 400, 401
"""
@rest.post('/monitoring/cluster/<cluster_name>/certificate/<certificate_name>/delete')
def delete_certificate(cluster_name, certificate_name, data):
    return u.render(api.delete_certificate(cluster_name, certificate_name, data)) 


""" Start to use the informed cluster as active cluster
    in the Asperathos section.
                                                                              
    Normal response codes: 200
    Error response codes: 400
"""
@rest.post('/monitoring/cluster/<cluster_name>')
def active_cluster(cluster_name, data):
    return u.render(api.active_cluster(cluster_name, data))
