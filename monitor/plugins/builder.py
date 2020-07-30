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

from monitor import exceptions as ex
from monitor.service import api
import kubejobs_cost
import kubejobs
import kubejobs_replica_cost


class MonitorBuilder:
    def __init__(self):
        pass

    def get_monitor(self, plugin, app_id, plugin_info):
        executor = None

        if plugin == "kubejobs":
            executor = kubejobs.PLUGIN(
                app_id, plugin_info, retries=api.retries)

        elif plugin == "kubejobs_cost":
            executor = kubejobs_cost.PLUGIN(
                app_id, plugin_info)

        elif plugin == "kubejobs_replica_cost":
            executor = kubejobs_replica_cost.PLUGIN(
                app_id, plugin_info)

        else:
            raise ex.BadRequestException()

        return executor
