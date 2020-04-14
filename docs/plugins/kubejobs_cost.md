# KubeJobs Cost Plugin

The Kubejobs Cost Plugin provides information on how a running application is performing regarding compliance to 
a cost reference given by the user. The cost is calculated based on resources usage and resources price. The later is 
acquired from a price information service, required for this plugin to run properly. Compliance to the cost reference is expressed as 
a cost error, which is published on a Redis queue. This information is, then, consumed by other components and services.

## How does it work?

The following steps describe the basic flow of an execution using KubeJobs Cost:

* Step 1: The client sends a POST request to the Asperathos Manager with a JSON body describing the execution.
* Step 2: The Manager creates a Redis service in the cluster, enqueues the items described in the input file in Redis through the queue auxiliary service.
* Step 3: The application execution is triggered on the cluster.
* Step 4: The application running on Kubernetes cluster starts to consume items from the Redis storage.
* Step 5: The Monitor is triggered by the Manager when application starts to run.
* Step 6: The Monitor periodically gets CPU and memory prices from a price information service.
* Step 7: As soon as metrics are being published, the Manager starts the Controller, which consumes metrics from Redis to take decisions about scaling based on the predefined control logic.


## Configuration

In order to correctly configure the Monitor to execute the KubeJobs Cost plugin, modifications in the *monitor.cfg* file are necessary. Following you can check an example of a configuration file that can be used to execute the KubeJobs Cost plugin.

### Configuration file example:

```
[general]
host = 0.0.0.0
port = 5001
plugins = kubejobs
debug = True
retries = 5

[kubejobs]
# No variables are needed
```

## Execute plugin

In order to execute the plugin, a JSON needs to be correctly configured with all necessary variables that will be used by Asperathos components. Following you can check an example of this JSON file that will be used to sends a POST request to the Asperathos Manager.

### JSON file example:

```javascript
{  
   "plugin":"kubejobs",
   "plugin_info":{  
      "username":"usr",
      "password":"psswrd",
      "cmd":[  
         [...]
      ],
      "img":"img",
      "init_size":1,
      "redis_workload":"workload",
      "config_id":"id",
      "control_plugin":"kubejobs",
      "control_parameters":{  
         [...]
      },
      "monitor_plugin":"kubejobs_cost",
      "monitor_info":{
         "cluster_info_url": "http://0.0.0.0:20000/price",
         "desired_cost": 1
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

## Request example
`POST /monitoring/:id`

Request body:
```javascript
{
	"plugin": "kubejobs_cost",
	"plugin_info": {
		 "cluster_info_url": "http://0.0.0.0:20000/price",
         "desired_cost": 1
	}
}
```

### Request parameters

#### cluster_info_url
Url accessed by the monitor to retrieve information on CPU and memory prices. The plugin expects a 
response with the format 
```javascript
{
    'cpu_price':<cpu_price>, 
    'memory_price':<memory_price>
}.
```

#### desired_cost
Reference cost used by the monitor to calculate cost error

## Requirements

### Cost service
The Kubejobs cost plugin requires access to a service which provides information on CPU and memory prices. An example of 
implementation of such service is presented as follows.

```python
from flask import Flask
app = Flask(__name__)

@app.route('/price', methods=['GET'])
def price():
    return {'cpu_price':1, 'memory_price':2}
```

### Metrics server
Installation of Metrics server (https://github.com/kubernetes-sigs/metrics-server) in the used kubernetes cluster is 
required before using this plugin. Metrics server is used to retrieve application resources usage data.