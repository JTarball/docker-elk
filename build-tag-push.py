#!/usr/bin/env python
"""
    build-tag-push.py

    Deployment script for docker projects

    create a production docker-compose file, pushs to docker hub
    and creates a github release.

"""

import os
import argparse
import subprocess
import yaml

from subprocess import check_output as check_cmd
from argparse import RawTextHelpFormatter


c_reset = check_cmd("tput sgr0".split())
c_red = check_cmd("tput setaf 1".split())
c_yellow = check_cmd("tput setaf 3".split())
c_green = check_cmd("tput setaf 2".split())


def colourise(msg='', colour=c_green):
    return colour + msg + c_reset


def red(msg):
    return colourise(msg, c_red)


def yellow(msg):
    return colourise(msg, c_yellow)


def green(msg):
    return colourise(msg, c_green)

# Basic script md5sum check
# =========================
# I use this script in many places / overkill to put into a generic package.
# Instead we use a basic md5sum to know what version of the script we are using.
# Therefore when you update this script add an entry into the dictionary below.
# NOTE: Our versioning is based of semantic versioning v0.0.1a / b / rc
# Add a 'a' or 'b' or - if you are currently developing
# http://www.jvandemo.com/a-simple-guide-to-semantic-versioning/

SCRIPT_VERSION = '0.0.1a'

SCRIPT_VERSIONING = {
    '0.0.1': '6ec1f96085e44238c6de666824e280e2'
}

if SCRIPT_VERSION.find('b') == -1 and SCRIPT_VERSION.find('a') == -1 \
        and SCRIPT_VERSIONING[SCRIPT_VERSION] != subprocess.check_call(["md5", __file__]):
    print red("ERROR: This script version is not %s" % SCRIPT_VERSION)
    print yellow(
        "To start developing the next version of this script "
        "add 'a' or 'b' to SCRIPT_VERSION e.g. %sa" % SCRIPT_VERSION
    )
    exit(1)

# ==============================================================================

# Beginning of main script
# ========================
parser = argparse.ArgumentParser(
    description="Build, tag and push docker image.\n\n"
    "Note: The script will only create a new 'release' docker-compose file "
    "unless specified with the correct options.",
    formatter_class=RawTextHelpFormatter
)

parser.add_argument(
    "--github_release",
    dest="push_to_github",
    action="store_true",
    default=False,
    help="If added we push a release to github"
)
parser.add_argument(
    "--dockerhub_release",
    dest="push_to_dockerhub",
    action="store_true",
    default=False,
    help="If added we push a release to docker hub"
)

args = parser.parse_args()

user_name = os.environ.get("DOCKERHUB_USER")
version = os.environ.get("PROJECT_VERSION")

if not version:
    print("Please set the PROJECT_VERSION to your project version, e.g.:")
    print("export PROJECT_VERSION=0.0.1")
    exit(1)

if not user_name:
    print("Please set the DOCKERHUB_USER to your user name, e.g.:")
    print("export DOCKERHUB_USER=james")
    exit(1)

# Get the name of the current directory.
project_name = os.path.basename(os.path.realpath("."))
# Remove '-' from project name
project_name = project_name.replace("-", "")

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
                compose_image = "{}_{}".format(project_name, service)
                hub_image = "{}/{}:{}".format(user_name, project_name, version)
                # Re-tag the image so that it can be uploaded to the Docker Hub.
                subprocess.check_call(["docker", "tag", compose_image, hub_image])
                # Spawn "docker push" to upload the image.
                if args.push_to_dockerhub:
                    push_operations[service_name] = subprocess.Popen(["docker", "push", hub_image])
                # Replace the "build" definition by an "image" definition,
                # using the name of the image on the Docker Hub.
                del services[service]["build"]
                services[service]["image"] = hub_image

if args.push_to_dockerhub:
    if push_operations == {}:
        print yellow("WARNING: Nothing to push to docker hub")

    # Wait for push operations to complete.
    for service_name, popen_object in push_operations.items():
        print("Waiting for {} push to complete...".format(service_name))
        popen_object.wait()
        print("Done.")

if args.push_to_github:
    pass


# Write the new docker-compose.yml file.
with open(output_file, "w") as f:
    yaml.safe_dump(stack, f, default_flow_style=False)

print("Wrote new compose file.")
print("COMPOSE_FILE={}".format(output_file))
