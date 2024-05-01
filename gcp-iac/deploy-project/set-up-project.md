[Deploy-Project Homepage](./README.md)

# Set up project with Terraform

Before setting up project with Terraform, one should make sure all the prerequisites are in place.

[Prerequisites](./prerequisites.md)

## Clone the SDS-IAC Git Repository

Clone the repository following the link to your local IDE

`SDS-IAC` [https://github.com/ONSdigital/sds-iac](https://github.com/ONSdigital/sds-iac)

## Project requirements and initial setup

This project has the following dependencies:

* [google-cloud-sdk](https://cloud.google.com/sdk)
* [pre-commit](https://pre-commit.com/)
* [tfenv](https://github.com/tfutils/tfenv)

To install dependencies and configure the project for first use, follow the instructions below:

1. Open a terminal at the project root
2. Install dependencies using `brew`
   `$ brew upgrade && brew install google-cloud-sdk pre-commit tfenv`
3. Install pre-commit hooks to run terraform script formatting when committing changes
   `$ pre-commit install`
4. Install the terraform version defined in the `.terraform-version` file using `tfenv`
   `$ tfenv install`
5. Set the terraform version we want to use, if not already done by the installation
   `$ tfenv use $(cat .terraform-version)`

The project is now ready for development or to use for deployments.

## Setting up GPG key

A GPG key is required to sign commits if you plan to work on development of the repository

* For signing commits to the git repository, create a new GPG key if you don't have an existing key. Follow the [link](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key) for creating a new GPG Key
* For the adding the new key to the account, follow the [link](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account)
* For telling Git about the Signing Key(Only needed once),follow the [link](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key)

## Updating Terraform before running

The Terraform script is default optimised for updating an existing project. To create a project from scratch, one will have to change a few variables

* In `main.tf`at the repository root level, find `cir_create_db` and change the value from 0 to 1
* Similarly, on the next line of `main.tf`, find `sds_create_db` and change the value from 0 to 1

This will allow Terraform to create the FireStore databases. The value should be changed back to 0 once the Terraform is applied.

## Running Terraform to create a project configuration

1. Open a terminal at the project root of your IDE
2. Authenticate with Google Cloud
   `$ gcloud auth application-default login` and `$ gcloud auth login`
3. Run the initialisation script. This will set the `TF_VAR_bucket` and `TF_VAR_project_id` env vars for use when running Terraform commands
   `$ source ./initialise-project.sh`
4. When prompted, enter the Google Cloud project name you want to use (e.g. `ons-cir-dev`)
5. Initialise Terraform setting the gcs backend tfstate bucket. The `-backend-config` flag is used to load the correct bucket name for the project
   `$ terraform init -backend-config="bucket=${TF_VAR_bucket}" -reconfigure`
6. Run the `plan` command to show the actions Terraform will apply to check everything looks ok
   `$ terraform plan`
7. Run `apply` answering `yes` when prompted to build the pipeline
   `$ terraform apply`

## Update Terraform after running

In `main.tf`at the repository root level, find `cir_create_db` and `sds_create_db` and change the values back to 0

[Deploy-Project Homepage](./README.md)
