#!/bin/bash

if [ "$1" == "--help" ]; then
  echo "Usage: interpolate_input_data.sh [resultdir] [year] [doy] [hour] [step]"
  echo
  echo "Loads meteorological weather data from stations"
  echo
  echo "Arguments:"
  echo "  resultdir: dir where results are stored, e.g. PWD"
  echo "  year: selected year in 4 digits"
  echo "  doy: selected doy in 3 digits"
  echo "  hour: selected hour in 2 digits"
  echo "  step ('now' or 'prev' or 'date'): whether latest data, data from the a passed hour or from a given date should be downloaded"
  echo
fi

resultdir=${1}
YEAR=${2}
DOY=${3}
HOUR=${4}
STEP=${5}

# LOAD DATA DEPENDING ON 'STEP'

if [ $STEP == "now" ]; then
  # load latest data
  # returns a tuple of filename and number of stations from which data was loaded
  RESULT=($(python3 interpolate/json_to_geojson.py -o $resultdir -s "now"))
else
  DOY_DATE=$(date -u -d "${YEAR}-1-1 +$((${DOY} - 1)) days" +%F);
  DATETIME=$(date -u -d "${DOY_DATE}T${HOUR}:00:00Z" +"%Y-%m-%dT%H:%M:%SZ");
  if [ $STEP == "prev" ]; then
    # load latest data equivalent from 1 hour ago in a window of 15 min, e.g.
    PREV_DATETIME=$(date -u -d "${DATETIME} -1 hour" +"%Y-%m-%dT%H:%M:%SZ");
    echo $PREV_DATETIME
    echo "load previous hour"
    RESULT=($(python3 interpolate/json_to_geojson.py -o $resultdir -s "prev" -m 15 -d $PREV_DATETIME))
  else # STEP is expected to be 'date'
    echo "load data for date ${DATETIME}"
    RESULT=($(python3 interpolate/json_to_geojson.py -o $resultdir -s "prev" -m 15 -d $DATETIME))
  fi
fi

FILENAME=${RESULT[0]}
N_POINTS=${RESULT[1]}

exit_message=$(python3 interpolate/apply_rk.py \
    $resultdir \
    "DO_TA_interpolate_${YEAR}_${DOY}_${HOUR}.tif" \
    "DO_RH_interpolate_${YEAR}_${DOY}_${HOUR}.tif" \
    "${FILENAME}" \
    "interpolate/utils/interpl_predictors_v3.0.0.tif" \
    --verbose 2)

if [ $? -ne 0 ]; then
  echo "Error: Failed to apply Interpolation with error: ${exit_message##*$'\n'}"
  exit 1
fi
  echo "Interpolation applied successfully."

meta_file="${resultdir}/output_meta.json"
WPATH=$(python3 interpolate/read_output_meta.py -f $meta_file -p 'wpath'| tail -n1)
QC_PASS=$(python3 interpolate/read_output_meta.py -f $meta_file -p 'qc'| tail -n1)

echo "qc pass: ${QC_PASS} (1 = true, 0 = false)"

# align only when the module passed quality control
if [ "$QC_PASS" == "1" ]; then
  python3 interpolate/nan_to_ndv.py "${resultdir}/DO_TA_interpolate_${YEAR}_${DOY}_${HOUR}.tif"
  python3 interpolate/nan_to_ndv.py "${resultdir}/DO_RH_interpolate_${YEAR}_${DOY}_${HOUR}.tif"


  # align 100m rasters to 3m resolution
  python3 utils/align_rasters.py \
    ${resultdir}/DO_TA_interpolate_${YEAR}_${DOY}_${HOUR}_ndv.tif \
    /usr/app/src/data/3m/DO_MRT_2025_105_12_3m_reference.tif \
    1 \
    ${resultdir}/DO_TA_interpolate-${WPATH}_${YEAR}_${DOY}_${HOUR}_${STEP}_align.tif \
    --src_epsg=25832 --ref_epsg=25832 --method=cubic

  python3 utils/align_rasters.py \
    ${resultdir}/DO_RH_interpolate_${YEAR}_${DOY}_${HOUR}_ndv.tif \
    /usr/app/src/data/3m/DO_MRT_2025_105_12_3m_reference.tif \
    1 \
    ${resultdir}/DO_RH_interpolate-${WPATH}_${YEAR}_${DOY}_${HOUR}_${STEP}_align.tif \
    --src_epsg=25832 --ref_epsg=25832 --method=cubic

  echo "Finished interpolation and alignment"
  echo "DO_TA_interpolate-${WPATH}_${YEAR}_${DOY}_${HOUR}_${STEP}_align.tif DO_RH_interpolate-${WPATH}_${YEAR}_${DOY}_${HOUR}_${STEP}_align.tif"
  exit 0
else
  # QC NOT PASSED
  echo "qc not passed"
  exit 1
fi
