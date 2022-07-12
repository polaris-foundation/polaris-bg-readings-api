#!/usr/bin/env bash

set -ux

# The Dockerfiles require these
touch build-circleci.txt
touch build-githash.txt

cd integration-tests

# Enable ReportPortal integration if on the default branch
if [ $CIRCLE_BRANCH == $DEFAULT_BRANCH ]; then
  echo "Enabling reportportal integration"
  export BEHAVE_ARGS="-D rp_enable=True -D step_based=True"
  export ENVIRONMENT=dev
  export RELEASE=$(git describe --tags | sed s/v//g)
fi

# Start the containers, backgrounded so we can do docker wait
# Pre pulling the postgres image so wait-for-it doesn't time out
docker-compose rm -f
docker-compose pull
docker-compose build
docker-compose up --no-start --force-recreate

# Wait for the integration-tests container to finish, and assign to RESULT
docker-compose run gdm-bg-readings-api-integration-tests
RESULT=$?

# Print logs based on the test results
if [ "$RESULT" -ne 0 ];
then
  docker-compose logs
else
  docker-compose logs gdm-bg-readings-api-integration-tests
fi

# Stop the containers
docker-compose down

# Exit based on the test results
if [ "$RESULT" -ne 0 ]; then
  echo "Tests failed :-("
  exit 1
fi

echo "Tests passed! :-)"
