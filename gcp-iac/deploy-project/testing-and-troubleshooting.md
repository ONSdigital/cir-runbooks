[Deploy-Project Homepage](./README.md)

# Testing CIR application and troubleshooting

This page is to set up a test on the accessibility of a service account to the CIR application. This is to make sure an external service can connect to and use CIR.

The following items should be completed prior to testing CIR

* A GCP set up properly by Terraform in the `SDS-IAC` Git repository
* A CIR application deployed sucessfully by the *CloudBuild* pipeline in the `EQ-CIR-FASTAPI` Git repository

## Information required for running the testing script

To authenticate the call to the load balancer using Python script, one has to gather the following information:

* A service account key file that has IAP-secured Web App User role assigned to the backend service. By default, one can use the service account {PROJECT\_NAME}@[appspot.gserviceaccount.com](http://appspot.gserviceaccount.com/). To obtain the JSON key file for the service account:

  1. Go to *Service Accounts* page on the GCP project
  2. Find or add a service account that contains the IAP-secured Web App User role
  3. Click on the service account
  4. Go to the *Keys* tab
  5. Click *Add Key* and select *Create new key*, select *JSON* and click *Create*
  6. Rename the downloaded JSON file (Optional)
  7. Put the JSON file in the same folder with the Python script below
* **The URL of the load balancer**. To find it:

  1. Go to L*oad Balancing* page on the GCP project
  2. Click on the load balancer for CIR
  3. At the *Frontend* section, click on the Certificate
     The name of certificate is: {PROJECT\_NAME}-ssl-cert
  4. Find the URL from *DNS Hostnames*

## Testing CIR using a Python script

The following script will post a CI schema to CIR using the Publish Collection Instrument endpoint. Edit the script below accordingly and save it in the same folder with the service account key JSON file. Then install the required packages and run the script

* **Line 22** has to be replaced by the *service account key file name*.
* **Line 25** has to be replaced by the Project ID.
* **Line 29** has to be replaced by the *load balancer URL*.

```python
import logging

import subprocess

import google.auth.transport.requests
import requests
from google.oauth2 import service_account


def publish_schema_to_cir(schema):
    """
    Function to publish schema to CIR

    Parameters:
        schema: A dict of the schema being published that matches the agreed schema structure

    Returns:
        HTTP Response, includes status code and message. Refer to openapi.yaml for detail
    """

    # Service account key file, that has been granted required roles to connect CIR service
    key_file = "sandbox-key.json"

    # Obtain the Client ID of OAuth Client on CIR project. Require the CIR Project ID, request it from SDS/CIR team
    project_id = "ons-cir-project"
    audience = _get_client_id(project_id, key_file)

    # The URL to access the load balancer on CIR project. Request it from SDS/CIR team
    base_url = "https://0.0.0.0.nip.io"

    # Make request to IAP of CIR load balancer
    response = _make_iap_request(
        f"{base_url}/v1/publish_collection_instrument", audience, key_file, schema
    )

    return response


def _get_client_id(project_id, key_file) -> str:
    """
    Function to get Client ID of OAuth Client on CIR project
    Require the role OAuth Config Editor & Compute Viewer for the service account used

    Parameters:
        project_id(str): The CIR Project ID
        key_file(str): The Json key file of the service account

    Returns:
        OAuth Client ID
    """

    try:
        # Set to use the supplied SA as the default configuration to connect gcloud
        cmd_auth = "gcloud auth activate-service-account --key-file=" + key_file
        subprocess.run(cmd_auth, shell=True)
        # Fetch for the client ID of OAuth Client on CIR
        cmd_get_oauth_brand_name = (
            "gcloud iap oauth-brands list --format='value(name)' --limit=1 --project="
            + project_id
        )
        oauth_brand_name = subprocess.check_output(cmd_get_oauth_brand_name, shell=True)
        oauth_brand_name = oauth_brand_name.decode().strip()
        cmd_get_oauth_client_name = (
            "gcloud iap oauth-clients list "
            + oauth_brand_name
            + " --format='value(name)' --limit=1"
        )
        oauth_client_name = subprocess.check_output(
            cmd_get_oauth_client_name, shell=True
        )
        oauth_client_name = oauth_client_name.decode().strip()
        oauth_client_id = oauth_client_name[oauth_client_name.rfind("/") + 1 :]

        return oauth_client_id

    except subprocess.CalledProcessError as e:
        print(e.output)
        # Raise exception


def _generate_headers(audience, key_file) -> dict[str, str]:
    """
    Function to create headers for authentication with auth token.

    Parameters:
        audience(str): The Client ID of the OAuth client on CIR project
        key_file(str): The Json key file of the service account

    Returns:
        dict[str, str]: the headers required for remote authentication.
    """

    headers = {}

    auth_req = google.auth.transport.requests.Request()
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        key_file, target_audience=audience
    )
    credentials.refresh(auth_req)
    auth_token = credentials.token

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    return headers


def _make_iap_request(req_url, audience, key_file, data):
    """
    Function to make IAP request to CIR

    Parameters:
        req_url(str): The full path of the CIR endpoint
        audience(str): The Client ID of the OAuth client on CIR project
        key_file(str): The Json key file of the service account
        data(schema): The schema being published

    Returns:
        HTTP Response, includes status code and message. Refer to openapi.yaml for detail
    """
    # Set Headers

    headers = _generate_headers(audience, key_file)

    try:
        response = requests.request("POST", req_url, headers=headers, json=data)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as error:
        logging.error("HTTP error occurred: %s", error)
        return response


if __name__ == "__main__":
    print("Start script")

    EXAMPLE_SCHEMA = {
        "survey_id": "3456",
        "language": "welsh",
        "form_type": "business",
        "title": "NotDune",
        "schema_version": "1",
        "data_version": "1",
        "description": "Version of CI is for March 2023",
    }

    response = publish_schema_to_cir(EXAMPLE_SCHEMA)
    print(response.status_code, response.content)

```

Installing required packages

```bash
pip install requests
pip install google.auth
```

Now one can execute the script.

CIR can be confirmed to have been successfully deployed and ready for external use if

* 200 sucess response is received with the schema metadata
* CI Schema metadata is found in *FireStore* under *ons-collection-instrument* collection
* CI Schema file is found in the CIR Schema Bucket

## Toubleshooting

### Receiving 400 bad request or 412 precondition error

A 400 or 412 error might still be received when testing the load balancer despite following all the steps mentioned. One can try to turn off and on the IAP to solve the error.

1. Go to *Identity-Aware Proxy* on the project
2. Toggle the IAP switch to off for all of the backend services. It may take a while
3. Toggle the IAP switch back on for all of the backend services

[Deploy-Project Homepage](./README.md)
