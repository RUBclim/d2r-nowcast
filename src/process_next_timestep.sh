#!/bin/bash

# this version has to be updated every time the pipeline version changes
PIPELINE_VERSION="v0.8.0"
RESOLUTION="3m"

if [ "$1" == "--help" ]; then
  echo "Usage: process_next_timestep.hs [savedir] [year] [month] [day] [hour]"
  echo
  echo "Loads meteorological weather data, runs SOLWEIG with it on the static data and finally mosaics the resulting Tmrt maps"
  echo
  echo "Arguments:"
  echo "  savedir (default: PWD): The savedir of the output metfile, e.g. ~/data/metfiles/"
  echo "  year (default: current year UTC): selected year"
  echo "  month (default: current month UTC): selected month"
  echo "  day (default: current day UTC): selected day"
  echo "  hour (default: current hour UTC): selected hour"
  echo
fi


savedir=${1:-$PWD}
now=$(date -u -I'seconds')  # '+%Y-%m-%d-%H-%j')

year=${2:-$(date --date="$now" +%Y)}
month=${3:-$(date --date="$now" +%m)}
day=${4:-$(date --date="$now" +%d)}
hour=${5:-$(date --date="$now" +%H)}
doy_long=$(date --date="$now" +%j)  # with leading zero
doy=${doy_long#${doy_long%%[1-9]*}}  # without leading zero

echo "savedir: ${savedir}"
echo "year: ${year}"
echo "month: ${month}"
echo "day: ${day}"
echo "hour: ${hour}"
echo "doy: ${doy}"
resultdir="/usr/app/src/results"
hours_ago=6  # hours required for warm-up

# download icon data for path 3.0 (fallback option) and save output file_location
icon_output=($(bash ./download_icon-d2.sh $resultdir $now $hours_ago | tail -n1))
file_location=${icon_output[0]}
timestamp=${icon_output[1]}
request_hour=${icon_output[2]}

# run interpolation module for current and previous hour
# if one or both fail to apply interpolation successfully, ICON-D2 will be used as default
station_data_dir="${resultdir}/station_data"

# execute request for stations in previous hour
output=$(bash ./interpolate_input_data.sh $station_data_dir $year $doy_long $hour "prev")
interpolate_exit_code=$?
# script returns 2 file names in last line if successful
last_line=$(echo "${output##*$'\n'}")   # remove all chars before the last line break

# handle possible interpolation script exit
if [ $interpolate_exit_code -ne 0 ]; then
  echo "Error: Failed to apply Interpolation for previous hour with error: ${last_line}"
else
  echo "INFO: Interpolation for previous hour applied successfully."
  mv "${station_data_dir}/output_meta.json" ${resultdir}/metadata/DO_meta_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_prev.json
  file_names_prev=($(echo $last_line))  # cast last line output into a tuple


  output=$(bash ./interpolate_input_data.sh $station_data_dir $year $doy_long $hour "now")
  interpolate_exit_code=$?
  # script returns 2 file names in last line if successful
  last_line=$(echo "${output##*$'\n'}")

  # handle possible interpolation script exit
  if [ $interpolate_exit_code -ne 0 ]; then
    echo "Error: Failed to apply Interpolation for current hour with error: ${last_line}."
  else
    echo "INFO: Interpolation for current hour applied successfully."
    file_names_now=($(echo $last_line))  # cast last line output into a tuple

    meta_file="${resultdir}/metadata/DO_meta_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_now.json"
    mv "${station_data_dir}/output_meta.json" $meta_file
  fi
fi

ta_raster_file_name=""
rh_raster_file_name=""

# Note: Interpolation already masks data to the ndv of its predictors, so
#  no need for masking the resulting rasters again

if [ "$interpolate_exit_code" -eq 0 ]; then
  # use station data

  ta_raster_file_name="${station_data_dir}/${file_names_now[0]}"
  rh_raster_file_name="${station_data_dir}/${file_names_now[1]}"

  echo "INFO: writing ta rh in ${ta_raster_file_name} and ${rh_raster_file_name}"

  # calc mean for ta and rh for current and previous hour
  python3 interpolate/calc_mean.py \
    -p "${station_data_dir}/${file_names_prev[0]}" \
    -n "${ta_raster_file_name}" \
    -o "${station_data_dir}/means/mean_ta_${year}_${doy_long}_${hour}.csv"
  python3 interpolate/calc_mean.py \
    -p "${station_data_dir}/${file_names_prev[1]}" \
    -n "${rh_raster_file_name}" \
    -o "${station_data_dir}/means/mean_rh_${year}_${doy_long}_${hour}.csv"

  # load metfile from icon data BUT replace ta and rh values
  metfile_location="${station_data_dir}/city_means_umep_interpolate_${year}_${doy_long}_${hour}.txt"

  proc_path=$(python3 interpolate/read_output_meta.py -f $meta_file -p 'wpath'| tail -n1)
  python3 interpolate/replace_ta_rh.py \
    -t "${station_data_dir}/means/mean_ta_${year}_${doy_long}_${hour}.csv" \
    -r "${station_data_dir}/means/mean_rh_${year}_${doy_long}_${hour}.csv" \
    -m "${file_location}/city_means_umep_${timestamp}.txt" \
    -o "${metfile_location}"

else
  # use icon-d2 data
  ta_raster_file_name="${file_location}/nwp-${timestamp}-band${band}-t_2m.tif"
  rh_raster_file_name="${file_location}/nwp-${timestamp}-band${band}-relhum_2m.tif"
  metfile_location="${file_location}/city_means_umep_${timestamp}.txt"
  echo '{"wpath": 3.0}' > ${resultdir}/metadata/DO_meta_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_icon.json
  proc_path="3.0"

  # align rasters to MRT raster after it was created

fi

echo "INFO: processing path of interpolation was ${proc_path}, metfile_location ${metfile_location}"
# select relevant hours from meteorological data for SOLWEIG run
python utils/load_metfile.py --input=${metfile_location} \
  --savedir=${savedir} \
  --year=${year} \
  --month=${month} \
  --day=${day} \
  --hour=${hour} \
  --proc=${proc_path}
metfile_forcing="${savedir}/metfile_${proc_path}_${year}-${month}-${day}_${hour}00.txt"


python umep_wrapper/solweig_multi_processing.py --data_path=/usr/app/src/data \
    --dsm_folder=3m/DTM+masked_DSM_tiles_3m/DTM+DSM_3m_tiles_1000+200 \
    --dtm_folder=3m/DTM_tiles_3m/DTM_3m_tiles_1000+200 \
    --met_file=${metfile_forcing} \
    --cdsm_folder=3m/canopy_DSM_3m/canopy_DSM_3m_tiles_1000+200 \
    --preprocess_data_path=/usr/app/src/data/3m/SOLWEIG_prepare_3m/SOLWEIG_prepare_3m_1000+200 \
    --lc_folder=3m/land_cover_3m/lc_3m_tiles_1000+200 \
    --output_path=${resultdir} \
    --proj_lib=/usr/share/proj


# remove all temporary folders created during the SOLWEIG run
rm -r /usr/app/UMEP-processing-fork/temp*

# rename tile-wise SOLWEIG results, since they all have the same name, create mosaic cannot read them properly all together
for f in ${resultdir}/SOLWEIG_3m_1000+200/temp_tiles/*/Tmrt_"$year"_"$doy"_"$hour"00*.tif
do
    DIR=$(dirname "$f")
    FILE=$(basename "$f")
    FOLDER=$(basename $(basename $(dirname "$f")))
    # F_NEW="${FOLDER}_${FILE}"
    suffix=$(echo ${FILE} | cut -d "_" -f 4)
    F_NEW="${FOLDER}_Tmrt_${RESOLUTION}_${PIPELINE_VERSION}_${year}_${doy_long}_${suffix}"
    echo "mv ${f} ${DIR}/${F_NEW}"
    mv $f "${DIR}/${F_NEW}"
done
# Note: SOLWEIG sets NoDataValue to -9999, for the following processing we use -32768 as NDV

# run mosaicing on tmp_dir and create mosaiced file in specific output directory
# "Usage: create_mosaic.sh [tiledir] [savename] [size] [overlap] [portion]"
bash ./utils/create_mosaic.sh ${resultdir}/SOLWEIG_3m_1000+200/temp_tiles/ /${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif 1000 200 *Tmrt_${RESOLUTION}_${PIPELINE_VERSION}_"$year"_"$doy_long"_"$hour"00*.tif

if false; then
    # remove all intermediate files
    # Note: placeholder for hour because our SOLWEIG runs consider two hours, one warm-up and one
    # requested hour. So we have to remove both created Tmrt files to clean up.
    # Thought: It would be nice to recycle already calculated Tmrt maps for a tile for the next
    # hour, but this requires internal changes within the SOLWEIG module, which we avoid.
    for f in ${resultdir}/SOLWEIG_3m_1000+200/temp_tiles/*/*Tmrt_"$year"_"$doy"_*00*.tif
    do
        rm $f
    done
else
    echo "INFO: keeping intermediate files .."
fi

# crop rasters to city boundaries
# MRT raster
filename_tmrt=${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
filename_tmrt_crop=${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_crop.tif
bash ./utils/apply_cutline.sh $filename_tmrt $filename_tmrt_crop utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
rm $filename_tmrt
mv $filename_tmrt_crop $filename_tmrt

# ---- ALIGN NWP RASTERS ----
# if processing path was defined to use ICON NWP data in the beginning

if [ $proc_path == "3.0" ]; then
  # select correct band from netCDF of nwp
  # remove leading zero for calculation
  h=${hour#${hour%%[1-9]*}};  # current hour
  r=${request_hour#${request_hour%%[1-9]*}}  # request hour
  temp=00
  # correct value for request hour "00"
  if [[ "$request_hour" == "$temp" ]]; then
    r=0
  fi
  # calculate band from the respective netCDF of nwp
  # 1. don't consider warum-up hours -> min. hours ago +
  # 2. determine position of current hour in the block of three-hourly model runs:
  # -->  (current hour - min. hours ago - model run hour) modulo 3 + 1
  # mod 3, due to 3 hourly model updates
  # +1, due to band 1 being the hour of the nwp model run
  band=$(python3 -c "print(${hours_ago}+(${h}-${hours_ago}-${r})%3+1)")

  # align weather data to raster
  python utils/align_rasters.py \
    ${file_location}/nwp-${timestamp}-t_2m.nc \
    ${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif \
    $band \
    ${ta_raster_file_name} \
    --src_epsg=4326 --ref_epsg=25832 --method=cubic

  python utils/align_rasters.py \
    ${file_location}/nwp-${timestamp}-relhum_2m.nc \
    ${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif \
    $band \
    ${rh_raster_file_name} \
    --src_epsg=4326 --ref_epsg=25832 --method=cubic

  # convert Kelvin (K) to Celsius (C)
  echo "INFO: air temp raster is at ${ta_raster_file_name}"
  python utils/convert_K_to_C.py -i ${ta_raster_file_name} -o ${ta_raster_file_name}

  # and crop to city boundaries

  # nwp t_2m raster
  filename_tair=${ta_raster_file_name}
  filename_tair_crop=${file_location}/nwp-${timestamp}-band${band}-t_2m_crop.tif
  bash ./utils/apply_cutline.sh $filename_tair $filename_tair_crop utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
  rm $filename_tair
  mv $filename_tair_crop $filename_tair

  # nwp relhum_2m raster
  filename_rh=${rh_raster_file_name}
  filename_rh_crop=${file_location}/nwp-${timestamp}-band${band}-relhum_2m_crop.tif
  bash ./utils/apply_cutline.sh $filename_rh $filename_rh_crop utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
  rm $filename_rh
  mv $filename_rh_crop $filename_rh
fi
# ---- END ALIGNMENT ----




# calculate thermal comfort indices (also creates classified rasters per default)
python umep_wrapper/calculate_tc_indices.py \
  --index="UTCI" \
  --metfile=${metfile_forcing} \
  --input_tmrt=${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif \
  --output_dir=${resultdir}/UTCI \
  --input_tair=${ta_raster_file_name} \
  --input_rh=${rh_raster_file_name} \

python umep_wrapper/calculate_tc_indices.py \
  --index="PET" \
  --metfile=${metfile_forcing} \
  --input_tmrt=${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif \
  --output_dir=${resultdir}/PET \
  --input_tair=${ta_raster_file_name} \
  --input_rh=${rh_raster_file_name} \


# crop rasters to city boundaries
# UTCI value raster
filename_umep=${resultdir}/UTCI/DO_UTCI_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
filename_crop=${resultdir}/UTCI/DO_UTCI_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_crop.tif
bash ./utils/apply_cutline.sh $filename_umep $filename_crop utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
rm $filename_umep
mv $filename_crop $filename_umep

# UTCI classified raster (shift to UTCI_CLASS dir)
filename_umep_class=${resultdir}/UTCI/DO_UTCI-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
filename_crop_class=${resultdir}/UTCI/DO_UTCI-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_crop.tif
filename_umep_class_new=${resultdir}/UTCI_CLASS/DO_UTCI-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
bash ./utils/apply_cutline.sh $filename_umep_class $filename_crop_class utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
rm $filename_umep_class
mv $filename_crop_class $filename_umep_class_new

# PET value raster
filename_pet=${resultdir}/PET/DO_PET_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
filename_crop=${resultdir}/PET/DO_PET_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_crop.tif
bash ./utils/apply_cutline.sh $filename_pet $filename_crop utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
rm $filename_pet
mv $filename_crop $filename_pet

# PET classified raster (shift to PET_CLASS dir)
filename_pet_class=${resultdir}/PET/DO_PET-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
filename_crop_class=${resultdir}/PET/DO_PET-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_crop.tif
filename_pet_class_new=${resultdir}/PET_CLASS/DO_PET-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}.tif
bash ./utils/apply_cutline.sh $filename_pet_class $filename_crop_class utils/DO_ADMIN_EPSG25832.geojson -crop_to_cutline
rm $filename_pet_class
mv $filename_crop_class $filename_pet_class_new


# create COG (LZW compression is used as default)
# UTCI values
filename_cog=${resultdir}/UTCI/DO_UTCI_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG $filename_umep $filename_cog
# UTCI classes, use different resampling method here
filename_cog_class=${resultdir}/UTCI_CLASS/DO_UTCI-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG -co RESAMPLING=NEAREST $filename_umep_class_new $filename_cog_class

# PET values
filename_cog=${resultdir}/PET/DO_PET_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG $filename_pet $filename_cog
# PET classes, use different resampling method here
filename_cog_class=${resultdir}/PET_CLASS/DO_PET-class_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG -co RESAMPLING=NEAREST $filename_pet_class_new $filename_cog_class

# t_2m
filename_cog=${resultdir}/TA/DO_TA_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG $ta_raster_file_name $filename_cog
# add entry to data sources log (source: either DWD or DWD+Stat)
echo "DO;TA;${year};${doy_long};${hour};${PIPELINE_VERSION};${proc_path};" >> ${resultdir}/TA/ta_data_sources.log
# relhum_2m
filename_cog=${resultdir}/RH/DO_RH_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG $rh_raster_file_name $filename_cog
# add entry to data sources log (source: either DWD or DWD+Stat)
echo "DO;RH;${year};${doy_long};${hour};${PIPELINE_VERSION};${proc_path};" >> ${resultdir}/RH/rh_data_sources.log

# MRT
filename_cog=${resultdir}/MRT/DO_MRT_${year}_${doy_long}_${hour}_${PIPELINE_VERSION}_cog.tif
gdal_translate -of COG $filename_tmrt $filename_cog
