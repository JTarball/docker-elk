#!/usr/bin/env python

import os
import subprocess
import time
import yaml
from subprocess import check_output as check_cmd


c_reset = check_cmd("tput sgr0".split())
c_red = check_cmd("tput setaf 1".split())
c_green = check_cmd("tput setaf 2".split())
user_name = os.environ.get("DOCKERHUB_USER")


def colourise(msg='', colour=c_green):
    return colour + msg + c_reset


def red(msg):
    return colourise(msg, c_red)


def green(msg):
    return colourise(msg, c_green)


if not user_name:
    print("Please set the DOCKERHUB_USER to your user name, e.g.:")
    print("export DOCKERHUB_USER=james")
    exit(1)

# Get the name of the current directory.
project_name = os.path.basename(os.path.realpath("."))

# Generate a Docker image tag, using the UNIX timestamp.
# (i.e. number of seconds since January 1st, 1970)
version = str(int(time.time()))

input_file = os.environ.get(
    "DOCKER_COMPOSE_YML", "docker-compose.yml")
output_file = os.environ.get(
    "DOCKER_COMPOSE_YML", "docker-compose.yml-{}".format(version))

if input_file == output_file == "docker-compose.yml":
    print("I will not clobber your docker-compose.yml file.")
    print("Unset DOCKER_COMPOSE_YML or set it to something else.")
    exit(1)

print("Input file: {}".format(input_file))
print("Output file: {}".format(output_file))

# Execute "docker-compose build" and abort if it fails.
subprocess.check_call(["docker-compose", "-f", input_file, "build"])

# Load the services from the input docker-compose.yml file.
# TODO: run parallel builds.
stack = yaml.load(open(input_file))

# Iterate over all services that have a "build" definition.
# Tag them, and initiate a push in the background.
if stack.get('version') != '2':
    print red("Sorry was expecting a docker-compose version 2")
    exit(1)

push_operations = dict()
for service_name, services in stack.items():
    if service_name == 'services':
        for service in services:
            if "build" in services[service]:
                print "Found service to build: %s" % green(service)


    # if "build" in service:
    #     print("build service: %s", service)
    #     compose_image = "{}_{}".format(project_name, service_name)
    #     hub_image = "{}/{}_{}:{}".format(user_name, project_name, service_name, version)
    #     # Re-tag the image so that it can be uploaded to the Docker Hub.
    #     subprocess.check_call(["docker", "tag", compose_image, hub_image])
    #     # Spawn "docker push" to upload the image.
    #     push_operations[service_name] = subprocess.Popen(["docker", "push", hub_image])
    #     # Replace the "build" definition by an "image" definition,
    #     # using the name of the image on the Docker Hub.
    #     del service["build"]
    #     service["image"] = hub_image

# Wait for push operations to complete.
for service_name, popen_object in push_operations.items():
    print("Waiting for {} push to complete...".format(service_name))
    popen_object.wait()
    print("Done.")

# Write the new docker-compose.yml file.
with open(output_file, "w") as f:
    yaml.safe_dump(stack, f, default_flow_style=False)

print("Wrote new compose file.")
print("COMPOSE_FILE={}".format(output_file))
