#!/bin/bash

# before running this cronscript: build docker container with tag d2r-backend
# docker build -f backend.Dockerfile -t d2r-backend .
version="0.8.0"
container_name=d2r-backend:v${version}

docker run --rm -d \
-v <path-to-metfiles>/met_files/dummy_metfiles/:/usr/app/src/data/met_files \
-v <path-to-static-data>:/usr/app/src/data \
-v <path-to-results>/:/usr/app/src/results \
-u $(id -u ${USER}):$(id -g ${USER}) --memory=128g --cpus=32 $container_name
docker logs -f $(docker ps|grep $container_name |awk '{print $1}') &> <path-to-log-file>/OUTPUT_cron_${version}.log &
