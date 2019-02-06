# External API Plugin

## How does it works?

The following steps describes the basic flow of an execution using External API:

* Step 1: The client sends a POST request to the Asperathos Manager with a JSON body describing the execution.
* Step 2: The application execution is triggered on the cluster.
* Step 3: The Monitor is triggered by the Manager when application starts to run.
* Step 4: The Monitor periodically gets the CPU information of the nodes contained in the cluster.
* Step 5: As soon as this metrics are being published, the Manager starts the Controller, which consumes metrics from the API to take decisions about scaling based on specific threshold.

## Configuration

In order to correctly configure the Monitor to execute the External API plugin, modifications in the *monitor.cfg* file are necessary. Following you can check an example of a configuration file that can be used to execute the Vertical plugin.

### Configuration file example:

```
[general]
host = 0.0.0.0
port = 6001
plugins = external_api
debug = True
retries = 5

[external_api]
# The specific metric that the actuator will modify
metric_source = cpu
# Endpoint of the get method of the external api
get_metric_endpoint = cpu-quota
# Threshold value used to trigger the scalling
threshold = 0.5
# The config file that gives permission to access the kubernetes cluster
k8s_manifest = /home/rafaelvf/.kube/config
```

## Execute plugin

In order to execute the plugin, a JSON needs to be correctly configurate with all necessary variables that will be used by Asperathos components. Following you can check an example of this JSON file that will be used to sends a POST request to the Asperathos Manager.

### JSON file example:

```javascript
{  
   "plugin":"plugin",
   "plugin_info":{  
      "username":"usr",
      "password":"pssword",
      "cmd":[  
         [...]
      ],
      "img":"img",
      "init_size":1,
      "redis_workload":"workload",
      "config_id":"id",
      "control_plugin":"vertical",
      "graphic_metrics": true,
      "control_parameters":{  
         [...]
      },
      "monitor_plugin":"external_api",
      "monitor_info":{  
         "expected_time":25
      },
      "enable_visualizer":true,
      "visualizer_plugin":"k8s-grafana",
      "visualizer_info":{  
         [...]
      },
      "env_vars":{  
         [...]
      }
   }
}
```