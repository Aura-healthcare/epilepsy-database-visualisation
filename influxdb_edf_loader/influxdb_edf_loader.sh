#!/bin/bash


while getopts ":i:v:t:" option
do
case "${option}"
in
i) SearchDest=${OPTARG};;
v) Version=${OPTARG};;
t) Token=${OPTARG};;
esac
done

# Check script input integrity
if [[ $SearchDest ]] || [[ $Version ]] || [[ $Token ]];
then
  echo "Start loading processing"
else
  echo "No Search directory: $SearchDest, Version or Token: $TargetDest, use -i -v -t options" >&2
  exit 1
fi


#Hack to force the bash to split command result only on newline char
#It is done to support the spaces in the folder names
OIFS="$IFS"
IFS=$'\n'

for EDF_FILE in $(find $SearchDest* -type f -name "*.edf" ); 
do
	echo loading $EDF_FILE
	for CHANNEL in EMG6+EMG6- emg6+emg6- ECG1+ECG1- EMG1+EMG1- 
	do
		echo channel: $CHANNEL
		python3  influxdb_edf_loader.py -i $EDF_FILE -c $CHANNEL -v $Version -t $Token
		if [ $? -eq 0 ]
		then
			echo "File $EDF_FILE processed"
		else
			echo "Failed to process $EDF_FILE" >&2
		fi
	done
done


IFS="$IFS"
exit 0