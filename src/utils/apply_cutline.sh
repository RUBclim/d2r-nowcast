#!/bin/bash

if [ "$1" == "--help" ]; then
  echo "Usage: apply_cutline.sh [src] [dst] [plgn]"
  echo
  echo "Use a polygon to clip a raster. Both datasets must be in the same CRS."
  echo
  echo "Arguments:"
  echo "  src: The filepath of the input raster."
  echo "  dst: The savepath of the clipped file."
  echo "  plgn: The filepath of the polygon to use as a cutline"
  echo
  echo "Optional arguments:"
  echo "  -crop_to_cutline: Change the raster's extent to match that of the cutline."
  exit 0
fi

src=$1
dst=$2
plgn=$3
flag=${4:-"do not crop"}

if [ "$flag" == "-crop_to_cutline" ]; then
  gdalwarp -cutline ${plgn} -co compress=lzw -dstnodata -32768 -crop_to_cutline ${src} ${dst}
else
  gdalwarp -cutline ${plgn} -co compress=lzw -dstnodata -32768 ${src} ${dst}
fi
