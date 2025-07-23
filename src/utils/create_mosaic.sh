#!/bin/bash

if [ "$1" == "--help" ]; then
  echo "Usage: create_mosaic.sh [tiledir] [savename] [size] [overlap] [portion]"
  echo
  echo "Create a mosaic from the tiled tiffs, after clipping them using a subwindow to reduce the overlap."
  echo
  echo "Arguments:"
  echo "  tiledir: The directory containing the TIFF tiles to process."
  echo "  savename: The savepath of the output file, e.g. ~/data/mosaic.tif."
  echo "  size: The tile size in pixels."
  echo "  overlap: The tile overlap in pixels."
  echo
  echo "Optional arguments:"
  echo "  tilename (default: *.tif): The tilename pattern to look for, e.g. SkyViewFactor_*.tif"
  echo "  n_jobs (default: 1): Number of threads to use."
  exit 0
fi

tiledir=$1
savename=$2
size=$3
overlap=$4
tilename=${5:-"*.tif"}
n_jobs=${6:-1}


# Create the savedir and a temporary directory to store the VRTs. 
# The tempdir will be deleted at the end of the script.
savedir=$(dirname $savename)
tempdir=${savedir}/temp
mkdir -p $tempdir

# Step 1: Determine the origin and the size of the subwindow in image coordinates (i.e. pixels).
xsize=$(LC_NUMERIC="en_US.UTF-8" printf "%.0f" $(echo "$size - $overlap * 0.5" | bc))
ysize=$xsize

xoff=$(LC_NUMERIC="en_US.UTF-8" printf "%.0f" $(echo "0 + $overlap * 0.25" | bc))
yoff=$xoff

#Step 2: Clip the tiffs to the desired size and store the result as a VRT.
find "${tiledir}" -name "${tilename}" | while IFS= read -r file
do
    echo "Processing $file"
    gdal_translate -of VRT -srcwin $xoff $yoff $xsize $ysize $file $tempdir/$(basename $file .tif)_clpd.vrt
done

#Step 3: Create the mosaic as a geoTIFF.
echo "Creating mosaic..."
gdalwarp -r average -multi -co TILED=YES -co compress=lzw -co NUM_THREADS=${n_jobs} -dstnodata -32768 ${tempdir}/*.vrt ${savename}
rm -r $tempdir
