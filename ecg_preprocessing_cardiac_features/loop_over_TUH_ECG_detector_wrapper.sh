#!/bin/bash

## Option - select input directory to be copied from and output directory to copy into
while getopts ":i:o:" option
do
case "${option}"
in
i) InputDest=${OPTARG};;
o) TargetDest=${OPTARG};;
esac
done

# Check script input integrity
if [[ $InputDest ]] || [[ $TargetDest ]];
then
  echo "Start Executing script"
else
  echo "No Input directory: $InputDest or Target directory: $TargetDest, use -i,-o options" >&2
  exit 1
fi

## Copy TUH folder tree structure
mkdir -p $TargetDest;
cd $InputDest && find . -type d -exec mkdir -p -- $TargetDest/{} \;

#Hack to force the bash to split command result only on newline char
#It is done to support the spaces in the folder names
OIFS="$IFS"
IFS=$'\n'

## List all EDF files in InputDest ##
for edf_file in $(find $InputDest/* -type f -name "*.edf" ); do

    filename=$(echo "$edf_file" | awk -F/ '{print $NF}')

    # Get relative path
    path=$(echo $edf_file | sed "s/$filename//g")
    CleanDest=$(echo $InputDest | sed 's/\//\\\//g')
    relative_path=$(echo $path | sed "s/$CleanDest\///g")

    # Get new filename
    dest_filename=$(echo $filename | sed 's/edf/json/g')

    python3 ./../ECG_detector_wrapper.py -i $edf_file -o $TargetDest/$relative_path/res_$dest_filename
    if [ $? -eq 0 ]
    then
      echo "$edf_file - OK"
    else
      echo "$edf_file - Fail" >&2
    fi

done

#Restore the bash automatic split on spaces
IFS="$OIFS"

exit 0
