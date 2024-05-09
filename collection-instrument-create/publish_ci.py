import datetime
import json
import logging
import os
import re
import subprocess

import google.auth.transport.requests
import google.oauth2.id_token
import requests

POST_URL = "/v1/publish_collection_instrument"
MANDATORY_KEYS = [
    "data_version",
    "form_type",
    "language",
    "survey_id",
    "title",
    "schema_version",
    "description",
]
OPTIONAL_KEYS = [
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


class CIRManager:
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

    def publish_collection_instrument(
        self, collection_instrument_data, project_id, base_url
    ):
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
        response = self.make_iap_request(
            f"{base_url}/v1/publish_collection_instrument",
            audience,
            collection_instrument_data,
        )
        return response

    def extract_key_id(self, filename):
        try:
            with open(filename, "r") as key_file:
                key_data = json.load(key_file)
                key_id = key_data.get("private_key_id")
                if not key_id:
                    raise ValueError("Key ID not found in the key file.")
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
                if "NOT_FOUND" in e.output.decode():
                    print(f"Key {key_id} no longer found in GCP.")
                else:
                    print(
                        f"Failed to delete key {key_id} from GCP: {e.output.decode()}"
                    )

        except Exception as e:
            print(f"Error during cleanup: {e}")


class CIProcessor:
    def __init__(self):
        pass

    @staticmethod
    def load_ci_from_file(file_path):
        """
        This function loads CI from the specified file and returns the CI object.
        """
        with open(file_path) as content:
            ci = json.load(content)
        return ci

    @staticmethod
    def glob_json_files(directory_path):
        """
        Function to glob the JSON files from a directory.
        """
        json_files = [
            os.path.join(directory_path, file)
            for file in os.listdir(directory_path)
            if file.endswith(".json")
        ]
        return json_files

    @staticmethod
    def validate_folder_path(folder_path):
        """
        Validate the provided folder path.
        """
        if os.path.isdir(folder_path):
            return True
        else:
            print("Error: The provided path is not a valid folder.")
            return False

    @staticmethod
    def get_folder_path_from_user():
        """
        Prompt the user to input the folder path.
        """
        folder_path = input("Enter the folder path containing CI JSON files: ").strip()
        while not CIProcessor.validate_folder_path(folder_path):
            folder_path = input(
                "Enter the folder path containing CI JSON files: "
            ).strip()
        return folder_path

    @staticmethod
    def publish_ci_file(
        ci, file_path, log_file, audience, total_errors_found, base_url
    ):
        """
        This function publishes CI and logs the response.
        """
        request_url = f"{base_url}{POST_URL}"

        ci_response = CIRManager().make_iap_request(request_url, audience, ci)

        if ci_response is None:
            # Handle the case where the request failed
            logging.error("Failed to make IAP request.")
            return total_errors_found

        try:
            ci_response_json = ci_response.json()

            # Handle error cases
            if ci_response_json.get("status") == "error":
                total_errors_found += 1
                log_message = (
                    f"CI file name {file_path}\nCI response {ci_response_json}\n\n"
                )
                log_file.write(log_message)
            else:
                log_file.write(
                    f"CI file name {file_path}\nCI response {ci_response_json}\n\n"
                )

        except KeyError:
            # Handle the case where the expected keys are not present in the response
            logging.error("KeyError: Required key(s) not found in the response JSON.")
            total_errors_found += 1
            log_file.write(
                f"Error: Required key(s) not found in the response JSON for CI file: {file_path}\n\n"
            )

        return total_errors_found

    @staticmethod
    def validate_ci_keys(ci):
        """
        Validates the keys of the CI dictionary.
        """
        mandatory_missing_keys = [key for key in MANDATORY_KEYS if key not in ci.keys()]
        additional_keys = [
            key for key in ci.keys() if key not in MANDATORY_KEYS + OPTIONAL_KEYS
        ]

        if mandatory_missing_keys or additional_keys:
            log_message = (
                f"Mandatory Missing Fields {mandatory_missing_keys}\n"
                f"Additional Fields Found {additional_keys}\n\n\n"
            )
            logging.error(log_message)
            return False
        return True

    @staticmethod
    def process_ci_files(
        directory_path, audience, key_filename, key_id, project_id, base_url
    ):
        """
        This function processes CI files from the specified directory path.
        """
        total_errors_found = 0
        log_filename = (
            f"log_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
        )
        with open(log_filename, "a") as log_file:
            for file_name in os.listdir(directory_path):
                if file_name.endswith(".json"):
                    file_path = os.path.join(directory_path, file_name)
                    try:
                        ci = CIProcessor.load_ci_from_file(file_path)
                    except Exception as e:
                        logging.error(f"Error loading CI file {file_path}: {e}")
                        continue

                    # Validate CI keys
                    if not CIProcessor.validate_ci_keys(ci):
                        total_errors_found += 1
                        continue

                    total_errors_found = CIProcessor.publish_ci_file(
                        ci, file_path, log_file, audience, total_errors_found, base_url
                    )

            log_file.write(
                f"Folder location provided: {directory_path}\n"
                f"Total Number of Json files to be published: {len(os.listdir(directory_path))}\n"
                f"Total errors found total_errors_found: {total_errors_found}\n\n"
            )
            return total_errors_found


class CIValidator:
    def __init__(self) -> None:
        None

    @staticmethod
    def validate_project_id(project_id):
        """
        Validate the format of the CIR Project ID.
        """
        if re.match(r"^[a-z\d-]+$", project_id):
            return True
        else:
            print(
                "Error: Invalid project ID format. Project ID can only contain lowercase letters, digits, and hyphens."
            )
            return False

    @staticmethod
    def validate_url(url):
        """
        Validate the format of the CIR URL.
        """
        if re.match(r"^https?://(?:[a-z\d-]+\.?)+[a-z]{2,}$", url):
            return True
        else:
            print(
                "Error: Invalid URL format. Please enter a valid URL starting with 'http://' or 'https://'."
            )
            return False


class CIPublisher:
    def __init__(self) -> None:
        pass

    def main():
        """
        This code includes the main function, which acts as the entry point for the script.
        It prompts the user for input, sets up logging, calls other functions to load and process
        the collection instrument files, and performs any necessary cleanup after processing.
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
        while not CIValidator.validate_project_id(project_id):
            project_id = input("Enter the CIR Project ID: ").strip()

        base_url = input("Enter the CIR URL: ").strip()
        while not CIValidator.validate_url(base_url):
            base_url = input("Enter the CIR URL: ").strip()

        try:
            # Prompt the user to input the folder path containing CI JSON files
            folder_path = CIProcessor.get_folder_path_from_user()

            # Generate key file
            cir_manager = CIRManager()
            key_filename, key_id = cir_manager.generate_key_file(project_id)

            # Obtain audience
            audience = cir_manager.get_client_id(project_id)

            CIProcessor.process_ci_files(
                folder_path,
                audience,
                key_filename,
                key_id,
                project_id,
                base_url,
            )

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Delete the key file after processing CIs
            cir_manager.cleanup_key_file(key_filename, key_id, project_id)


if __name__ == "__main__":
    CIPublisher.main()
