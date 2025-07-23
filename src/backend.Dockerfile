## Baseimage
FROM python:3.12-bookworm
## Note: bookworm holds a more recent GDAL version (3.6.2) than bullseye (3.2.2) and therefore is compatible with python3.11
## bullseye (GDAL 3.2.2) would require a setuptools<58.0.0 which is incompatible with python3.11

##Labels as key value pair
LABEL Maintainer="lw"

## Set working directory (arbitrary choice)
WORKDIR /usr/app/src

RUN echo 'deb http://deb.debian.org/debian/ unstable main contrib non-free' >> /etc/apt/sources.list

## Installing libgdal headers and obtaining 'gdal-config'
# cdo=2.3.0 would allow copy and mergetime operators at the same time, 3.11.6-bookworkm only has 2.1.1
RUN : \
    && apt-get update \
    && apt-get install --yes \
        bc \
        locales \
        cdo

# Debian 12 (bookworm) only has gdal 3.6.x available, which is build with numpy 1.x.x
# thermal-comfort requires numpy 2.x.x, hence gdal with a numpy 2.x.x build is needed
# i.e. gdal >= 3.9
# solution: install latest gdal from an unstable debian build
RUN apt update
RUN apt install -t unstable -y libgdal-dev gdal-bin
RUN apt-get install -y locales-all

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

## Update C environment variables so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

## Install requirements
COPY d2r-nowcast/src/umep_wrapper/requirements.txt ./
RUN pip install -r requirements.txt

## flexible option to install gdal based on package version of apt installed headers
# RUN pip install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2"."$3}')
RUN pip install GDAL==3.10.0
# gdal 3.6.2
# Manually set GDAL PROJ_LIB environment variable
ENV PROJ_LIB="/usr/share/proj"

# install sibling projects
COPY downloader downloader
RUN pip install --editable downloader/
COPY UMEP-processing-fork UMEP-processing-fork
RUN pip install --editable UMEP-processing-fork/
# allow adding temporary directories within umep
RUN chmod 777 UMEP-processing-fork

COPY d2r-nowcast d2r-nowcast

RUN pip install -r d2r-nowcast/src/icon_d2/requirements.txt
RUN pip install -r d2r-nowcast/src/interpolate/requirements.txt
RUN pip install thermal-comfort==1.1.2
RUN chmod +x d2r-nowcast/src/process_next_timestep.sh
RUN chmod +x d2r-nowcast/src/download_icon-d2.sh
RUN chmod +x d2r-nowcast/src/interpolate_input_data.sh
WORKDIR d2r-nowcast/src
ENV PYTHONPATH="${PYTHONPATH}:/usr/app/src/d2r-nowcast/src"
ENTRYPOINT ["./process_next_timestep.sh", "/usr/app/src/results/metfiles"]
