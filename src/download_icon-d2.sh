#!/bin/bash
if [ "$1" == "--help" ]; then
  echo "Usage: download_icon-d2.sh [resultdir] [now] [hours_ago]"
  echo
  echo "Loads meteorological weather data from DWD ICON-D2 NWPs"
  echo
  echo "Arguments:"
  echo "  resultdir (default: PWD): dir where results are stored"
  echo "  now: timestamp isoformat UTC of current datetime"
  echo "  hours_ago: int, number of hours passed since the NWP model started"
fi

# read args
resultdir=${1}
now=${2}
hours_ago=${3}

echo "DOWNLOAD ICON ${resultdir} ${now} ${hours_ago}"
# NWP request date in iso format (at least hours_ago=6 hours from now to avoid spin-up inaccuracies)
request_date=$(date --date="${now}" -d "${hours_ago} hour ago")
request_year=$(date --date="$request_date" '+%Y')
request_month=$(date --date="$request_date" '+%m')
request_day=$(date --date="$request_date" '+%d')
request_doy=$(date --date="$request_date" '+%j')
# round to latest model run (3-hourly updates)
request_hour=$(printf "%02d" $((($(date --date="$request_date" '+%-H')/3)*3)))
# Syntax comment: +%-H to get hour digits without a leading zero, then adding leading zero in printf

# adjust request date to 3-hourly model updates
request_date=${request_year}-${request_month}-${request_day}T${request_hour}:00:00
timestamp="${request_year}${request_month}${request_day}-${request_hour}"  # e.g. 20240227-06
icon_req_folder="${request_year}${request_month}${request_day}${request_hour}"  # e.g. 2024022706

file_location="${resultdir}/icon-d2-data/${icon_req_folder}"
echo "download data to ${file_location}"

# check if NWP data does not exist, and has to be downloaded to $savedir (mounted to the container)
if [ -d "${resultdir}/icon-d2-data/${request_year}${request_month}${request_day}${request_hour}" ]; then
  echo "NWP data for requested model run at ${request_date} does exist."
else
  python icon_d2/src/main.py -d $request_date -o "${resultdir}/icon-d2-data" --start 0 --step 1 --end 48

  # transform that to UMEP accepted format
  python umep_wrapper/icon2umep.py --city_means="${file_location}/city_means.csv" --output_file="city_means_umep_${timestamp}.txt" --output_dir=${file_location}

  echo "NWP 48h forecast data for requested model run at ${request_date} was downloaded to ${file_location}."
fi

echo $file_location $timestamp $request_hour
