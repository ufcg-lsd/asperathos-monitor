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
