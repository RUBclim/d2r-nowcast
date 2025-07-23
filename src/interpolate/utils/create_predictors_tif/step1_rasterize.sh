#!/bin/bash

# This script rasterizes the following predictors
# from the geopackage file into GeoTIFF files.

predictors=(
"BDSM2_mean" "BDSM2_stdev" "BDSM2_min" "BDSM2_max" "ROAD_perc" \
"SVF_mean" "SVF_stdev" "DTM_mean" \
"DTM_stdev" "BU_perc" "VEG_perc" "VEG_max" "VEG_min" "VEG_mean" "COLD_perc" \
"CLMT1_perc" "CLMT2_perc" "CLMT3_perc" "CLMT4_perc" "CLMT5_perc" "CLMT6_perc" \
"CLMT7_perc" "CLMT8_perc" "IND_perc" "BUAREA_mean" "BUAREA_stdev")

infile=./predictors_v1.1.5_L0.gpkg
savedir=./L0
mkdir -p $savedir

for varname in "${predictors[@]}"; do
    echo $varname
    gdal_rasterize -a $varname -tr 100.0 100.0 -a_nodata -32768 -te 380000.0 5695000.0 409000.0 5719000.0 -ot Float32 -of GTiff $infile $savedir/$varname.tif
done

