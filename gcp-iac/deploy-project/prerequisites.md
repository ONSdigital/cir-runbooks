[Deploy-Project Homepage](./README.md)

# Prerequisites

## Connect the CIR, SDS and SDS-IAC Git Repositories

As SDS and CIR share the same IAC Terraform, all three Git Repositories have to be connected when deploying either of the service.

**This process will require an authorised person from SDS/CIR to complete. Please contact the SDS/CIR team for assistance.**

To connect the repositories:

1. Enable the Cloud Build API by searching *Cloud Build* and click *Enable*
2. Go to the *Triggers* page on the GCP project
3. Click *Connect Repository*
4. Select the *europe-west2* region and select *GitHub*
5. Follow the authenticate process
6. Find and select the following repositories
   * `EQ-CIR-FASTAPI`: *https://github.com/ONSdigital/eq-cir-fastapi*
   * `SDS`: *https://github.com/ONSdigital/sds*
   * `SDS-IAC`: *https://github.com/ONSdigital/sds-iac*

If a repository cannot be found, please contact the SDS/CIR team.

## Add OAuth Client Credential

An OAuth client credential is required as the load balancer has to be IAP (Identity Aware Proxy) enabled to protect the CIR backend services. More information on how IAP works can be found here: [Google Cloud IAP Overview](https://cloud.google.com/iap/docs/concepts-overview)

To create an OAuth client credential, an OAuth App has to be created first:

1. Go to the *OAuth consent screen* page on the GCP project
2. Select User Type: *External*
3. On the next screen, enter a name for the app (this name is not format restricted) and support email (usually it will be the google email account of the user creating the app)
4. Scroll down and enter the developer contact email as applicable (again it will usually be the google email account of the user creating the app)
5. Click *Save & Continue* all the way to summary
6. Click *Back to Dashboard*

Then, to create an OAuth client credential:

1. Go to the *Credential* page on the GCP project
2. Click *Create Credentials* and select *OAuth client ID*
3. Select Application Type: *Web application*
4. Enter a name for the credential. This name is not restricted
5. Click *Create*

Now, an OAuth client credential is created with a Client ID and a Client Secret.

## Add Redirect URL

To be able to receive a token for IAP, a redirect URI is required for the credential created. To provide the redirect URI:

1. Click on the OAuth client credential that has been created in previous section
2. Look for and copy the *Client ID* in *Additional information*. It should ends with `.apps.googleusercontent.com`.
3. Open a text editor and format the URI as following:
   `https://iap.googleapis.com/v1/oauth/clientIds/{client_id}:handleRedirect`
   Please insert the copied Client ID at the place holder *{client_id}*
4. Scroll down to the Authorised redirect URIs section
5. Click Add URI
6. Copy and paste the formatted URI
7. Click Save

## Store Client ID as Secret

The Client ID and Client Secret have to be stored in Google Secret Manager as a security measure. To do so:

1. Select the credential that has just been created
2. Download the *Client Secret* as a json file to your computer
3. Go to the *Secret Manager* page on the GCP project. You may need to enable the *Secret Manager* API
4. Click *Create Secret*
5. Enter the name as "**iap-secret**"
6. Upload the json file using the file browser
7. Leave *replication policy* unchecked
8. Make sure the encryption is using *Google-managed encryption key*
9. Click *Create Secret*

## Enable Compute Engine API

The Compute Engine API has to be manually enabled before running the Terraform if it has not been enabled before.

1. On the project, search for Compute Engine
2. Click *Enable Compute Engine API*

Now, the project is ready to be setup using Terraform

[Deploy-Project Homepage](./README.md)
