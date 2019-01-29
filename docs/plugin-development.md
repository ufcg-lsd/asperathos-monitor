# Plugin development
This is an important step to enjoy all flexibility and features that this framework provides.

## Steps

1. In *monitor.cfg* add the plugin to the list of desired plugins:

### Example:

```
[general]
host = 0.0.0.0
port = 6001
plugins = my_new_monitor
debug = True
retries = 5

[my_new_monitor]
var1 = 
var2 = 
var3 = 
```
In this tutorial, we will use MyNewMonitor to represent a new monitor plugin.

2. Create a new if statement condition in the file *monitor/service/api/__init__.py* that will recognize if the new plugin added is informed in the configuration file (*monitor.cfg*). If this condition is true, then the necessary variables to execute the plugin needs to be informed in the *monitor.cfg* file and computed in the *monitor/service/api/__init__.py*.

### Example:

```
import ConfigParser

try:

[...]

if 'my_new_monitor' in plugins:
    var1 = config.get('my_new_monitor', 'var1')
    var2 = config.get('my_new_monitor', 'var2')
    var3 = config.get('my_new_monitor', 'var3')

[...].
```

3. Create a new folder under *monitor/plugins* with the desired plugin name and add *__init__.py*.
 
4. Write a new python class under *monitor/plugins/mynewmonitor*. This class must extend *monitor.plugins.base* and implement only two methods: __init__ and  monitoring_application.

* **__init__(self, app_id, plugin_info, collect_period, retries=60)**
	* **app_id**: it is the application id. It is the only mandatory information about the metric identity, although there may be others.
	* **collect_period**: the time interval to execute monitoring_application.
	* **retries**: the number of retries when some problem any problem occurs during the any of the steps to gather metrics and publish into the metric store service. When all the retries are consumed, the monitoring service for this application will stop. If the problem disappears before the end of the retries, the retries number reload the initial value. (e.g. the connection is failing with the host where I’m accessing remotely but I don’t wanna give up to monitor this host because this problem can be for a little lapse of time).
	* **plugin_info**: it is a dictionary that contains all the information needed specifically for the plugin (e.g.: reference value for an application execution, the url for the service that will provide me the metrics or the path to the log file I need to read to capture the metrics and the host ip where this log is located).

* **monitoring_application(self)**
	* This method does every necessary step to calculate or capture the metric that must be published. For example, if you will use monasca to gather and publish your metrics, you must create an object monitor.utils.monasca.MonascaClient and use send_metrics([metrics]) to publish the metrics, where [metrics] is a list with the metrics you want to push into monasca and each metric is a dictionary with this following structure: 
		* ```
			metric = {'name':  'application-name.metric-namer'
			   'value': value
			   'timestamp': time.time() * 1000
			   'dimensions': self.dimensions
		  ```
		   
* **Example**:

	* ```
		class MyNewMonitor:

    		def __init__(self, app_id, plugin_info, collect_period, retries=100):
        	# set things up
			pass
        
    		def monitoring_application(self):
        	# monitoring logic
        	pass
	  ```

5. Edit the MonitorBuilder class adding a new condition to check the plugin name in the start_monitor. Instantiate the plugin in the conditional case.
* **Example**:
	* ```
		...
		elif plugin_name == "mynewmonitor":
	            plugin = MyNewMonitor(app_id, plugin_info, collect_period, retries=retries)
		...
		```
