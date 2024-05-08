# Destroy a CIR project

As CIR and SDS share the same project environment and the resources are managed by the same Terraform, it is necessary to handle the resources for both of the projects in case of project destroy so that the environment is clean up properly for redeploying one of the service or both services.

## Notify external parties

It is important to notify the external parties who are using the project before and after project destroy so that actions can be taken to avoid interruption.

RAS team may have subscribed to the project SDS dataset Pub/Sub topic. If so, then

* Before destroying the project, RAS has to be notified
* After destroying the project, RAS has to be contacted to ask for re-subscribing to the Pub/Sub topic

Author team may be using the project SDS FireStore for dummy data. If so, then

* Before destroying the project, ask the Author team of any concern in data loss in FireStore
* Make sure the Permanent SDS FireStore backup and SDS Schema backup buckets are exists on project `ons-sds-dns` and contains the necessary data for recovering
* Read through the confluence page [Clearing Data from Integration Environment](https://confluence.ons.gov.uk/display/SDC/Clearing+Data+from+Integration+Environment) for any dos and don'ts

## Destroy a project with Terraform

Destorying a project by Terraform will delete all resources managed by Terraform, and the rest will be kept.

Resources that will be deleted

* SDS and CIR IP Addresses
* SDS Schema and Dataset buckets and all documents within
* CIR Schema buckets and all documents within
* Indexes of SDS and CIR FireStore database
* All SDS and CIR load balancing elements
* SDS Cloud Run service
* CIR Cloud Run service
* The cloudbuild service account
* All SDS and CIR images in local Artifact Registry
* SDS Publish Schema and Dataset Pub/Sub topics
* CIR Publish CI Pub/Sub topic
* All Cloudbuild triggers

Resources that will NOT be deleted

* SDS and CIR FireStore database and its data
* Other buckets
* OAuth app
* OAuth 2.0 Client ID
* Client ID secret
* SDS New-dataset cloud function
* Service account - App engine default service account
* Service account - Compute engine default service account

To confirm destroying the project, go to the root level of `SDS-IAC` repository in the IDE terminal.

1. Authenticate with Google Cloud
   `$ gcloud auth application-default login` and `$ gcloud auth login`
2. Run the Terraform command:
   `terraform destroy`

You will then be prompted for the Project ID, please make sure you input the correct Project ID

## Manual deletion of the SDS Cloud Function

The SDS *new-dataset* Cloud Function is not currently being managed by Terraform and thus will not be deleted together with the Cloud Run application. Leaving the cloud function undeleted will cause issue when re-deploying the SDS service such that the event-triggered cloud function will not run on the newly created dataset bucket as it ties to the bucket that is already been deleted.

To manually delete the *new-dataset* Cloud Function:

1. Go to *Cloud Run* of the project
2. Select the *new-dataset-function* service and click *Delete*
3. Go to *Cloud Functions* of the project
4. Select the *new-dataset-function* and click *Delete*

The project is now ready to be redeployed

## Manual deletion of the CIR subscription

CIR contains a subsciption that is used to carry out assertion when running the integration test. The subscription is not managed by Terraform and will need to be deleted manually. Leaving the subscription behind will cause it to malfunction as it is tied to a topic that will have been already deleted, causing the integration test to fail.

To manually delete the CIR subscription:

1. Go to *Pub/Sub* of the project
2. Go to the *Subscriptions* tab
3. Select the subscription with ID *ons-cir-publish-events-subscription-cir*
4. Click *Delete*

## Redeploying the CIR project

Please refer to the following page to redeploy a CIR project

[Deploying a CIR Project](../deploy-project/README.md)
