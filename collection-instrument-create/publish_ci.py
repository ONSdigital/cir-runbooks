import logging
import subprocess
import re
import os
import json
import datetime
import requests
import google.oauth2.id_token
import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token

class SDSManager:
    def __init__(self):
        pass

    def make_iap_request(self, req_url, audience, data):
        """
        Function to make IAP request to CIR
        Parameters:
            req_url(str): The full path of the CIR endpoint
            audience(str): The Client ID of the OAuth client on CIR project
            data(schema): The schema being published
        Returns:
            HTTP Response, includes status code and message.
        """
        # Set Headers
        headers = self.generate_headers(audience)
        response = None  # Initialize response variable
        try:
            response = requests.request(
                "POST", req_url, headers=headers, json=data, verify=False
            )
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as error:
            print(f"HTTP error occurred: {error}")
            if response is not None:
                return response
            else:
                # Handle the case when response is None
                return None

    def generate_headers(self, audience) -> dict[str, str]:
        """
        Function to create headers for authentication with auth token.
        Parameters:
            audience(str): The Client ID of the OAuth client on CIR project
        Returns:
            dict[str, str]: the headers required for remote authentication.
        """
        auth_req = google.auth.transport.requests.Request()
        auth_token = google.oauth2.id_token.fetch_id_token(auth_req, audience=audience)

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        return headers

    def get_client_id(self, project_id) -> str:
        """
        Function to get Client ID of OAuth Client on CIR project
        Require the role OAuth Config Editor & Compute Viewer for the service account used
        Parameters:
            project_id(str): The CIR Project ID
        Returns:
            OAuth Client ID
        """
        try:
            # Fetch for the client ID of OAuth Client on CIR
            cmd_get_oauth_brand_name = (
                "gcloud iap oauth-brands list --format='value(name)' --limit=1 --project="
                + project_id
            )
            oauth_brand_name = subprocess.check_output(
                cmd_get_oauth_brand_name, shell=True
            )
            oauth_brand_name = oauth_brand_name.decode().strip()
            cmd_get_oauth_client_name = (
                "gcloud iap oauth-clients list "
                + oauth_brand_name
                + " --format='value(name)' --limit=1 --project="
                + project_id
            )
            oauth_client_name = subprocess.check_output(
                cmd_get_oauth_client_name, shell=True
            )
            oauth_client_name = oauth_client_name.decode().strip()
            oauth_client_id = oauth_client_name[oauth_client_name.rfind("/") + 1 :]
            return oauth_client_id
        except subprocess.CalledProcessError as e:
            print(e.output)


    def publish_collection_instrument(self, collection_instrument_data, project_id, base_url):
        """
        Function to publish a collection instrument to a specified endpoint.
        Parameters:
            collection_instrument_data: A dictionary containing the collection instrument data.
            project_id: Project ID where the collection instrument is being published.
            base_url: Base URL of the endpoint for publishing collection instruments.
        Returns:
            HTTP Response object containing the status code and message.
        """
        # Obtain the Client ID of OAuth Client on the project. Requires the project ID.
        audience = self.get_client_id(project_id)
        
        # Make a request to the specified endpoint
        response = self.make_iap_request(f"{base_url}/v1/publish_collection_instrument", audience, collection_instrument_data)
        return response


    def extract_key_id(self, filename):
        try:
            with open(filename, "r") as key_file:
                key_data = json.load(key_file)
                key_id = key_data.get("private_key_id")
                if not key_id:
                    raise Exception("Key ID not found in the key file.")
                return key_id
        except Exception as e:
            print(f"Error extracting key ID: {e}")
            return None
    
    def generate_key_file(self, project_id):
        # Constructing the service account email using the project_id
        service_account_email = f"{project_id}@appspot.gserviceaccount.com"

        key_filetype = "json"
        key_filename = project_id + "." + key_filetype

        # Setting environment variables
        os.environ["ONS_SDS_SANDBOX_SA"] = service_account_email
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_filename

        # Constructing the gcloud command
        cmd_create_service_account_key = (
            "gcloud iam service-accounts keys create "
            + key_filename
            + " --iam-account="
            + service_account_email
            + " --key-file-type="
            + key_filetype
            + " --project="
            + project_id
        )

        try:
            # Execute the command and capture the output
            key_output = subprocess.check_output(
                cmd_create_service_account_key, shell=True
            )
            key_id = self.extract_key_id(key_filename)
            if key_id is None:
                raise Exception("Key ID extraction failed.")
            return key_filename, key_id
        except Exception as e:
            print(f"Error occurred: {e}")
            return key_filename, None  # Return key_filename and None for key_id


    def cleanup_key_file(self, local_key_file, key_id, project_id):
        try:
            # Delete local key file
            if os.path.exists(local_key_file):
                os.remove(local_key_file)
                print(f"Deleted local key file: {local_key_file}")

            # Form the command to delete the key from GCP
            iam_account = f"{project_id}@appspot.gserviceaccount.com"
            cmd_delete_key = f"gcloud iam service-accounts keys delete {key_id} --iam-account={iam_account} --project={project_id} --quiet"

            # Execute the command
            try:
                subprocess.check_output(
                    cmd_delete_key, shell=True, stderr=subprocess.STDOUT
                )
                print(f"Deleted key {key_id} from GCP")
            except subprocess.CalledProcessError as e:
                print(f"Failed to delete key {key_id} from GCP: {e.output.decode()}")

        except Exception as e:
            print(f"Error during cleanup: {e}")

details = {}
path_to_json = "./collection-instrument-create/CIR_test_schema_cleaned"
post_url = "/v1/publish_collection_instrument"
timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
mandatory_keys = ["data_version", "form_type", "language", "survey_id", "title", "schema_version", "description"]
optional_keys = [
    "legal_basis",
    "metadata",
    "mime_type",
    "navigation",
    "questionnaire_flow",
    "post_submission",
    "sds_schema",
    "sections",
    "submission",
    "theme",
]

def load_ci_from_path(path_to_json):
    """
    This function loads CIs from the specified path and return ci_list and json file names
    """
    ci_list = []
    json_files = [pos_json for pos_json in os.listdir(path_to_json)]
    for json_file in json_files:
        with open(f"{path_to_json}/{json_file}") as content:
            ci = json.load(content)
            ci_list.append(ci)
    return ci_list, json_files

def publish_ci_file(ci, file_name, log_file, audience, total_errors_found):
    """
    This function publishes ci and upon publish following things will be logged for each collection instrument
    to be published:
       1. File name.
       2. Response received.
       3. Missing Mandatory Fields(if response received has message `Field required`).
       4. Missing Optional Fields(if response received has the message `Field required`).
       5 Additional Fields that are not present in the `PostCiMetadataV1PostData` model(if
       response received has the message `Field required`)).
    """
    base_url = "https://34.36.120.202.nip.io"
    post_url = "/v1/publish_collection_instrument"
    request_url = f"{base_url}{post_url}"
    ci_response = SDSManager().make_iap_request(request_url, audience, ci) 
    if ci_response is not None: 
        try:
            ci_response_json = ci_response.json()
            # Process the JSON response
            if ci_response_json.get("message") == "Field required" and ci_response_json.get("status") == "error":
                total_errors_found += 1
                mandatory_missing_keys = [key for key in mandatory_keys if key not in ci.keys()]
                optional_missing_keys = [key for key in optional_keys if key not in ci.keys()]
                additional_keys = [key for key in ci.keys() if key not in (mandatory_keys + optional_keys)]
                log_file.write(
                    f"CI File name: {file_name}\n"
                    f"CI response {ci_response_json}\n"
                    f"Mandatory Missing Fields {mandatory_missing_keys}\n"
                    f"Optional Missing Fields {optional_missing_keys}\n"
                    f"Additional Fields Found {additional_keys}\n\n\n"
                )
            elif ci_response_json.get("status") == "error":
                total_errors_found += 1
                log_file.write(f"CI file name {file_name}\n" f"CI response {ci_response_json}\n\n")
            else:
                log_file.write(f"CI file name {file_name}\n" f"CI response {ci_response_json}\n\n")
        except KeyError:
            # Handle the case where the expected keys are not present in the response
            logging.error("KeyError: Required key(s) not found in the response JSON.")
            total_errors_found += 1
            log_file.write(f"Error: Required key(s) not found in the response JSON for CI file: {file_name}\n\n")
    else:
        # Handle the case where the request failed
        logging.error("Failed to make IAP request.")
    return total_errors_found

def process_ci_files(ci_list, json_files, audience, key_filename, key_id, project_id):
    """
    This function creates a log file which is used in storing responses in `publish_ci_file` function and provide
    consolidated count of json files to be published and errors found is provdied at the end of the log file
    """
    total_errors_found = 0
    with open(f"log_{timestamp}.log", "a") as log_file:
        for ci, file_name in zip(ci_list, json_files):
            total_errors_found = publish_ci_file(ci, file_name, log_file, audience, total_errors_found)
        log_file.write(
            f"Folder location provided: {path_to_json}\n"
            f"Total Number of Json files to be published: {len(json_files)}\n"
            f"Total errors found total_errors_found: {total_errors_found}\n\n"
        )

    # Delete the key file after all CIs have been published
    sds_manager = SDSManager()
    sds_manager.cleanup_key_file(key_filename, key_id, project_id)

def validate_project_id(project_id):
    """
    Validate the format of the CIR Project ID.
    """
    if re.match(r'^[a-z\d-]+$', project_id):
        return True
    else:
        print("Error: Invalid project ID format. Project ID can only contain lowercase letters, digits, and hyphens.")
        return False

def validate_url(url):
    """
    Validate the format of the CIR URL.
    """
    if re.match(r'^https?://(?:[a-z\d-]+\.?)+[a-z]{2,}$', url):
        return True
    else:
        print("Error: Invalid URL format. Please enter a valid URL starting with 'http://' or 'https://'.")
        return False

if __name__ == "__main__":
    """
    Before running this file make sure to clone the required repository and then specify the path above
    """
    # Automatically authenticate the user
    try:
        subprocess.run(["gcloud", "auth", "login", "--quiet"], check=True)
        print("Authentication successful. Continuing with the script...")
    except subprocess.CalledProcessError as e:
        print(f"Error: Authentication failed. {e}")
        exit(1)  # Exit the script if authentication fails
    
    # Prompt the user to enter the CIR Project ID and URL
    project_id = input("Enter the CIR Project ID: ").strip()
    while not validate_project_id(project_id):
        project_id = input("Enter the CIR Project ID: ").strip()
    
    base_url = input("Enter the CIR URL: ").strip()
    while not validate_url(base_url):
        base_url = input("Enter the CIR URL: ").strip()
    
    details = {"project_id": project_id, "base_url": base_url}
    sds_manager = SDSManager()

    ci_list, json_files = load_ci_from_path(path_to_json)
    key_filename, key_id = sds_manager.generate_key_file(details["project_id"])
    audience = SDSManager().get_client_id(details["project_id"]) 
    print(audience)

    if key_id is None:
        print("Error: Unable to create key file. Exiting the script.")
        exit()  # Exit the script if a key file cannot be created.

    process_ci_files(ci_list, json_files, audience, key_filename, key_id, details["project_id"])