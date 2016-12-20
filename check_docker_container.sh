#!/bin/bash

# Author: James Tarball
# Email: james.tarball@gmail.com
#
# Usage: ./check_docker_container.sh 
# Checks all docker-compose processes
# (You must have a docker-compose.yml in the same directory as this file)
#
# Usage: ./check_docker_container.sh <container_id> 
# Checks the container status for <container_id>
#
# The script checks if a container is running.
#   OK - running
#   WARNING - container is dead or restarting
#   CRITICAL - container is stopped
#   UNKNOWN - does not exist


if [ ! -z $1 ] 
then 
    CONTAINERS=$1
else
	CONTAINERS=$(docker-compose ps -q)
fi

if [ "$CONTAINERS" == "" ]; then
  echo "CRITICAL - No docker containers found."
  exit 2
fi

for CONTAINER in $CONTAINERS; do
	HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER)
	RUNNING=$(docker inspect --format="{{ .State.Running }}" $CONTAINER 2> /dev/null)
	RESTARTING=$(docker inspect --format="{{ .State.Restarting }}" $CONTAINER 2> /dev/null)
	DEAD=$(docker inspect --format="{{ .State.Dead }}" $CONTAINER)

	if [ $? -eq 1 ]; then
	  echo "UNKNOWN - $CONTAINER does not exist."
	  exit 3
	fi

	if [ "$RUNNING" != "true" ]; then
	  echo "CRITICAL - $CONTAINER is not running."
	  exit 2
	fi

	if [ "$HEALTH" == "unhealthy" ]; then
	  echo "CRITICAL - $CONTAINER is unhealthy."
	  exit 2
	fi

	if [ "$RESTARTING" == "true" ]; then
	  echo "WARNING - $CONTAINER is restarting."
	  exit 2
	fi

	if [ "$DEAD" == "true" ]; then
	  echo "WARNING - $CONTAINER is dead."
	  exit 1
	fi

	STARTED=$(docker inspect --format="{{ .State.StartedAt }}" $CONTAINER)

	echo "OK - $CONTAINER is running. StartedAt: $STARTED"
done