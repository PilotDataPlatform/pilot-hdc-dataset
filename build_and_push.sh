#!/bin/bash
set -e

DOCKER_REGISTRY="docker-registry.ebrains.eu"

SERVICE="dataset"
TAG_MESSAGE="$1"
BRANCH="hdc"
GITLAB_INFRA_REPO_URL="git@gitlab.ebrains.eu:hdc/cscs-infra.git" # Replace with your actual GitLab Infra Repo URL
GITLAB_PIPELINE_URL="https://gitlab.ebrains.eu/hdc/cscs-infra/-/pipelines" # Replace with the template URL to your GitLab pipeline page

# Check for --help argument to display usage information
if [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [--help]"
    echo "This script automates the process of building and pushing both the service and alembic docker images."
    echo "Ensure the poetry version is updated to avoid conflicts with existing Docker images."
    echo "You'll also need to pass the message to be used upon creation of the git tag:"
    echo ""
    echo "  ./build_and_push.sh \"Your commit message here\""
    echo ""
    echo "  # Example:"
    echo "  ./build_and_push.sh \"We fixed all the bugs in this latest change.\""
    echo ""
    exit 0
fi

# Ask for user input to get a tag message if not provided
if [ -z "$TAG_MESSAGE" ]; then
    read -p "Please provide a tag message (optional): " TAG_MESSAGE
fi

# Ensure the git branch is correct and up-to-date
git checkout $BRANCH
git pull origin $BRANCH

TAG=$(poetry version -s)

# Ask for user input to get the TAG if not provided
if [ -z "$TAG" ]; then
    read -p "Please provide the tag: " TAG
fi

# Exit with error if TAG is still empty
if [ -z "$TAG" ]; then
    echo "Tag must not be empty."
    exit 1
fi

# Exit with error if there are merge conflicts
if [[ $(git ls-files -u) ]]; then
    echo "There are merge conflicts. Please resolve them before continuing."
    exit 1
fi

# Check if the Docker image with the given TAG already exists in the registry
DOCKER_TAG_SERVICE="$DOCKER_REGISTRY/hdc-services-image/$SERVICE:$SERVICE-$TAG"
DOCKER_TAG_ALEMBIC="$DOCKER_REGISTRY/hdc-services-image/$SERVICE:alembic-$TAG"

# Using docker manifest inspect to check if the image exists. Adjust the command if needed based on your registry.
if docker manifest inspect $DOCKER_TAG_SERVICE >/dev/null || docker manifest inspect $DOCKER_TAG_ALEMBIC >/dev/null; then
    echo "Docker image with tag $TAG already exists. Please update the poetry version."
    exit 1
fi

# Build and push the SERVICE image
docker build --target $SERVICE-image --tag $DOCKER_TAG_SERVICE --platform=linux/amd64 .
docker push $DOCKER_TAG_SERVICE

# Build and push the alembic image
docker build --target alembic-image --tag $DOCKER_TAG_ALEMBIC --platform=linux/amd64 .
docker push $DOCKER_TAG_ALEMBIC

# Create a git tag and push it
git tag -a $TAG -m "$TAG_MESSAGE"
git push origin $TAG
