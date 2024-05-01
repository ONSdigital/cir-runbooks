# Cir-runbooks

This script automates the process of publishing Collection Instruments (CIs) to a specified endpoint in the Collection Instrument Repository (CIR) system. It utilizes Google Cloud Platform (GCP) services for authentication and communication with the CIR.

# Setup for publishing a ci

Download Collection Instruments (CIs): Download the necessary Collection Instrument JSON files that you want to publish. Store these files in a folder on your computer. (Multiple ci files can be stored in a folder)
Finally run the following commands
    'pip install requests'
    'pip install google-auth'

# Publishing a ci/multiple ci's


To publish a ci you will need to do the following 

- Run the script publish_ci.py
- This will prompt you to authenticate your GCP account 
- Enter the project ID
- Enter the base url (this can be found in the load balancing page in GCP and must be inputted in the format http://xx.xx.xx.nip.io).
- Enter the absolute path of the folder where you stored the CI JSON files.
- Once complete view Log File you can view the log file (log_<timestamp>.log) generated in the same directory for details about the publishing process and verify the publishing of ci in the Firestore database.
