#!/bin/bash

QRS_DETECTORS=("gqrs" "xqrs" "hamilton" "engelsee" "swt")

## Option - select input directory to be copied from and output directory to copy into
while getopts ":i:o:a:" option
do
case "${option}"
in
i) InputDest=${OPTARG};;
a) AnnotDest=${OPTARG};;
o) TargetDest=${OPTARG};;
esac
done

# Check script input integrity
if [[ $InputDest ]] || [[ $TargetDest ]];
then
  echo "Start Executing script"
else
  echo "No Input res directory: $InputDest or no inpur annot directort: $AnnotDest or Target directory: $TargetDest, use -i,-a,-o options" >&2
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
for edf_file in $(find $InputDest/* -type f -name "*.json" ); do

    filename=$(echo "$edf_file" | awk -F/ '{print $NF}')

    # Get relative path
    path=$(echo $edf_file | sed "s/$filename//g")
    CleanDest=$(echo $InputDest | sed 's/\//\\\//g')
    relative_path=$(echo $path | sed "s/$CleanDest\///g")

    # Get new filename
    dest_filename=$(echo $filename | sed 's/^res_//g')

    for qrs_detector in ${QRS_DETECTORS[@]};do
      python3 ./../Cardiac_features_computation_wrapper.py -i $edf_file -a $AnnotDest/$relative_path/annot_$dest_filename -o $TargetDest/$relative_path/"feats_"$qrs_detector"_"$dest_filename -q $qrs_detector
      if [ $? -eq 0 ]
      then
        echo "$edf_file # $qrs_detector - OK"
      else
        echo "$edf_file # $qrs_detector - Fail" >&2
      fi

    done

done

#Restore the bash automatic split on spaces
IFS="$OIFS"

exit 0
