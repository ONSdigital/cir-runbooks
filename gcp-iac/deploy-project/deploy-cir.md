[Deploy-Project Homepage](./README.md)

# Deploy CIR

Before deploying CIR, it is expected the project is properly set up using the Terraform that is specified in the following page

[Set up project with Terraform](./set-up-project.md)

## Clone the CIR Git Repository

Clone the repository following the link to your local IDE

`CIR` [https://github.com/ONSdigital/eq-cir-fastapi](https://github.com/ONSdigital/eq-cir-fastapi)

## Deploy CIR Cloud Run application

The CloudBuild pipeline is used to deploy the CIR Cloud Run application. To trigger the pipeline, one will have to create a PR in the Git CIR repository.

1. Create a branch from *main* on GitHub
2. Go to the new branch and make a trivial change on CIR (most likely adding a comment in the Readme file)
3. Commit the change and create a PR. The pipeline *cloud-build-cir-cloud-run* should be triggered on your project
4. Check the progress on your project *Cloud Build* page. CIR Cloud Run application is deployed sucessfully when all the steps are passed

[Deploy-Project Homepage](./README.md)
