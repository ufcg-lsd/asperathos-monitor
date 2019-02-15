#  REST API Endpoints
This section provides a detailed list of avaliable endpoints in Monitor REST API.

## Start monitoring
  Start monitoring an application.

* **URL**: `/monitoring/:app_id`
* **Method:** `POST`

* **JSON Request:**
	* ```javascript
	  {
	     plugin: [string],
	     plugin_info : {
	         [...]
	     }
	  }
	  ```
* **Success Response:**
  * **Code:** `204` <br />
		
* **Error Response:**
  * **Code:** `400 BAD REQUEST` <br />

## Stop submission
  Stop monitoring of an application.

* **URL**: `/monitoring/:app_id/stop`
* **Method:** `PUT`

* **Success Response:**
  * **Code:** `204` <br />
		
* **Error Response:**
  * **Code:** `400 BAD REQUEST` <br />

## Add cluster
  Add a new cluster reference into the Asperathos Monitor section

* **URL**: `/monitoring/cluster`
* **Method:** `POST`
* **JSON Request:**
	* ```javascript
		{
			"user" : [string],
			"password" : [string],
			"cluster_name" : [string],
			"cluster_config" : [string]
		}
* **Success Response:**
  * **Code:** `220` <br /> **Content:** 
	  * ```javascript
	    {
			"cluster_name" : [string],
			"status": [string],
			"reason": [string]
	    }
		```

## Add certificate
  Add a certificate in the a cluster reference into the Asperathos Monitor section

* **URL**: `/monitoring/cluster/:cluster_name`
* **Method:** `POST`
* **JSON Request:**
	* ```javascript
		{
			"user" : [string],
			"password" : [string],
			"certificate_name" : [string],
			"certificate_content" : [string]
		}
* **Success Response:**
  * **Code:** `220` <br /> **Content:** 
	  * ```javascript
	    {
			"cluster_name" : [string],
			"certificate_name" : [string],
			"status": [string],
			"reason": [string]
	    }
		```

## Delete cluster
  Delete a cluster reference of the Asperathos Monitor section

* **URL**: `/monitoring/cluster/:app_id/delete`
* **Method:** `POST`
* **JSON Request:**
	* ```javascript
		{
			"user" : [string],
			"password" : [string]
		}
* **Success Response:**
  * **Code:** `220` <br /> **Content:** 
	  * ```javascript
	    {
			"cluster_name" : [string],
			"status": [string],
			"reason": [string]
	    }
		```

## Delete certificate
  Delete a certificate of a cluster reference in the Asperathos Monitor section

* **URL**: `/monitoring/cluster/:cluster_name/certificate/:certificate_name/delete`
* **Method:** `POST`
* **JSON Request:**
	* ```javascript
		{
			"user" : [string],
			"password" : [string]
		}
* **Success Response:**
  * **Code:** `220` <br /> **Content:** 
	  * ```javascript
	    {
			"cluster_name" : [string],
			"certificate_name" : [string],
			"status": [string],
			"reason": [string]
	    }
		```

## Active cluster
  Start to use the informed cluster as active cluster in the Asperathos Monitor section.

* **URL**: `/monitoring/cluster/:app_id`
* **Method:** `POST`
* **JSON Request:**
	* ```javascript
		{
			"user" : [string],
			"password" : [string]
		}
* **Success Response:**
  * **Code:** `220` <br /> **Content:** 
	  * ```javascript
	    {
			"cluster_name" : [string],
			"status": [string],
			"reason": [string]
	    }
		```