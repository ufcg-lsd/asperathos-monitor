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
from monitor.utils.logger import Log
from monitor.service import plugin_service

API_LOG = Log("APIv10", "APIv10.log")

monitored_apps = {}


def start_monitoring(data, app_id):
    """ These conditional cases choose the class executor's constructor of the
    application submitted
    Note: some executors need the keypair to access remotely some machine and
    execute the monitoring logic, but this attribute is not mandatory for all
    the executors."""

    if 'plugin_info' not in data:
        API_LOG.log("Missing parameters in request")
        raise ex.BadRequestException()

    for plugin_key in data['plugin_info']:
        API_LOG.log("Creating plugin: %s" % plugin_key)
        API_LOG.log(data)
        plugin = data['plugin_info'][plugin_key]['plugin']
        plugin_info = data['plugin_info'][plugin_key]

    # if app_id not in monitored_apps:
        executor = plugin_service.get_plugin(plugin)(app_id, plugin_info)

        if app_id not in monitored_apps:
            monitored_apps[app_id] = {}
        monitored_apps[app_id][plugin_key] = executor
        executor.start()

    # else:
    #    API_LOG.log("The application is already being monitored")
    #    raise ex.BadRequestException()


def stop_monitoring(app_id):
    if app_id not in monitored_apps:
        API_LOG.log("App doesn't exist")
        raise ex.BadRequestException()

    for plugin_key in monitored_apps[app_id]:
        API_LOG.log("Stopping plugin: %s" % plugin_key)
        monitored_apps[app_id][plugin_key].stop()

    # Stop the plugin and remove from the data structure
    monitored_apps.pop(app_id, None)


def get_job_report(app_id, detailed):
    if app_id not in monitored_apps:
        API_LOG.log("App doesn't exist")
        raise ex.BadRequestException()

    for plugin in monitored_apps[app_id]:
        if monitored_apps[app_id][plugin].report_flag:
            API_LOG.log("Plugin still running:%s" % plugin)
            return {'message': 'Job is running yet!'}, 202

    merged_report = {}

    if detailed:
        for plugin in monitored_apps[app_id]:
            API_LOG.log("Getting detailed report for plugin:%s" % plugin)
            merged_report[plugin] = monitored_apps[app_id][plugin].get_detailed_report()
    else:
        for plugin in monitored_apps[app_id]:
            API_LOG.log("Getting report for plugin:%s" % plugin)
            merged_report[plugin] = monitored_apps[app_id][plugin].job_report.to_dict()

    return merged_report, 200


def install_plugin(source, plugin):
    status = plugin_service.install_plugin(source, plugin)
    if status:
        return {"message": "Plugin installed successfully"}, 200
    return {"message": "Error installing plugin"}, 400
